from pathlib import Path
import json
import time

import cv2
import numpy as np

from sih_dr.quality.quality_engine import (
    FundusQualityEngine,
    enhance_borderline,
)

from sih_dr.grading.calibrated_inference import (
    CalibratedGlobalDRInference,
)

from sih_dr.lesions.inference import (
    LesionInferenceEngine,
    create_lesion_overlay,
)

from sih_dr.structure.structural_engine import (
    StructuralRetinaEngine,
)

from sih_dr.xai.gradcam import (
    GlobalDRGradCAM,
    create_gradcam_overlay,
    attribution_in_fov,
    lesion_attribution_overlap,
)

from sih_dr.xai.stability import (
    StabilityEvaluator,
)

from sih_dr.xai.clinical_fusion_v2 import (
    pathology_score_v2,
    grade_evidence_concordance_v2,
    trust_score_v2,
)


GRADE_NAMES = {
    0: "No apparent DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


class ExplainableDREngineV2:

    VERSION = "NETRAAI_ENGINE_V2"


    def __init__(
        self,
        grader_checkpoint,
        lesion_checkpoint,
        calibration_config,
        output_dir="results/sih_dr_v2/cases",
    ):

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "\n=== INITIALIZING NETRAAI V2 ==="
        )

        self.quality_engine = (
            FundusQualityEngine()
        )

        self.global_engine = (
            CalibratedGlobalDRInference(
                grader_checkpoint,
                calibration_config,
            )
        )

        self.lesion_engine = (
            LesionInferenceEngine(
                lesion_checkpoint
            )
        )

        self.structure_engine = (
            StructuralRetinaEngine()
        )

        self.gradcam = (
            GlobalDRGradCAM(
                self.global_engine.model
            )
        )

        self.stability_engine = (
            StabilityEvaluator(
                self.global_engine
            )
        )

        print(
            "NetraAI V2 ready.\n"
        )


    # ========================================================
    # LESION ADAPTER
    # ========================================================

    @staticmethod
    def _fusion_lesions(
        lesion_result
    ):

        evidence = (
            lesion_result[
                "evidence"
            ]
        )

        def value(
            name
        ):

            item = evidence[
                name
            ]

            if item[
                "count"
            ] == 0:

                return 0.0

            return float(
                item[
                    "mean_confidence"
                ]
            )

        return {
            "ma_evidence":
                value("MA"),

            "he_evidence":
                value("HE"),

            "ex_evidence":
                value("EX"),

            "se_evidence":
                value("SE"),
        }


    # ========================================================
    # ROUTING
    # ========================================================

    @staticmethod
    def _recommendation(
        quality,
        referable_dr,
        concordance,
        trust,
        stability,
    ):

        if (
            quality[
                "status"
            ]
            ==
            "UNGRADEABLE"
        ):

            return {
                "action":
                    "RECAPTURE",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "Image quality is insufficient "
                        "for automated screening."
                    ),
            }


        if (
            concordance[
                "status"
            ]
            ==
            "LOW"
        ):

            return {
                "action":
                    "HUMAN_REVIEW",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "Global prediction and independent "
                        "retinal evidence are discordant."
                    ),
            }


        if (
            stability[
                "level"
            ]
            ==
            "LOW"
        ):

            return {
                "action":
                    "HUMAN_REVIEW",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "Prediction or explanation is unstable "
                        "under benign image perturbations."
                    ),
            }


        if (
            trust[
                "level"
            ]
            ==
            "LOW"
        ):

            return {
                "action":
                    "HUMAN_REVIEW",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "Overall case-level trust is low."
                    ),
            }


        if referable_dr:

            return {
                "action":
                    "REFER_OPHTHALMOLOGY",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "Calibrated referable-DR screening "
                        "decision exceeds the locked operating threshold."
                    ),
            }


        if (
            quality[
                "status"
            ]
            ==
            "BORDERLINE"
        ):

            return {
                "action":
                    "REVIEW_OR_RECAPTURE",

                "priority":
                    "MODERATE",

                "reason":
                    (
                        "Image remains borderline quality."
                    ),
            }


        return {
            "action":
                "ROUTINE_SCREENING",

            "priority":
                "LOW",

            "reason":
                (
                    "No referable DR identified with "
                    "sufficient system reliability."
                ),
        }


    # ========================================================
    # ANALYSIS
    # ========================================================

    def analyze(
        self,
        image_path
    ):

        total_start = (
            time.perf_counter()
        )

        image_path = Path(
            image_path
        )

        image = cv2.imread(
            str(
                image_path
            )
        )

        if image is None:

            raise RuntimeError(
                f"Could not read image: {image_path}"
            )


        case_id = (
            image_path.stem
        )

        case_dir = (
            self.output_dir
            /
            case_id
        )

        case_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        timings = {}


        # ====================================================
        # 1. QUALITY
        # ====================================================

        stage_start = (
            time.perf_counter()
        )


        quality_original = (
            self.quality_engine.analyze(
                image
            )
        )

        working_image = (
            image.copy()
        )

        quality = (
            quality_original
        )

        enhancement_applied = False


        if (
            quality_original[
                "status"
            ]
            ==
            "BORDERLINE"
        ):

            enhanced = (
                enhance_borderline(
                    image
                )
            )

            enhanced_quality = (
                self.quality_engine.analyze(
                    enhanced
                )
            )

            if (
                enhanced_quality[
                    "score"
                ]
                >
                quality_original[
                    "score"
                ]
            ):

                working_image = (
                    enhanced
                )

                quality = (
                    enhanced_quality
                )

                enhancement_applied = (
                    True
                )


        analysis_input = (
            case_dir
            /
            "analysis_input.png"
        )

        cv2.imwrite(
            str(
                analysis_input
            ),
            working_image,
        )


        timings[
            "quality_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # SAFETY GATE
        # ====================================================

        if (
            quality[
                "status"
            ]
            ==
            "UNGRADEABLE"
        ):

            result = {
                "engine_version":
                    self.VERSION,

                "case_id":
                    case_id,

                "quality": {
                    **quality,

                    "enhancement_applied":
                        enhancement_applied,
                },

                "prediction":
                    None,

                "lesions":
                    None,

                "anatomy":
                    None,

                "p_score":
                    None,

                "concordance":
                    None,

                "xai_integrity":
                    None,

                "stability":
                    None,

                "t_score":
                    None,

                "recommendation": {
                    "action":
                        "RECAPTURE",

                    "priority":
                        "HIGH",

                    "reason":
                        "Image failed retinal quality gate.",
                },

                "timings":
                    timings,
            }

            result[
                "timings"
            ][
                "total_ms"
            ] = round(
                (
                    time.perf_counter()
                    -
                    total_start
                )
                *
                1000.0,
                2,
            )

            self._save_json(
                case_dir,
                result
            )

            return result


        # ====================================================
        # 2. GLOBAL MODEL
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        global_result = (
            self.global_engine.predict(
                working_image
            )
        )

        grade = int(
            global_result[
                "grade"
            ]
        )

        timings[
            "global_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # 3. LESION PATH
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        lesion_result = (
            self.lesion_engine.predict(
                working_image
            )
        )

        timings[
            "lesions_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        lesion_overlay = (
            create_lesion_overlay(
                working_image,
                lesion_result[
                    "masks"
                ],
            )
        )

        lesion_overlay_path = (
            case_dir
            /
            "lesion_overlay.png"
        )

        cv2.imwrite(
            str(
                lesion_overlay_path
            ),
            lesion_overlay,
        )


        # ====================================================
        # 4. ANATOMY
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        structure_dir = (
            case_dir
            /
            "structure"
        )

        anatomy = (
            self.structure_engine.analyze(
                analysis_input,
                output_dir=
                    structure_dir,
            )
        )

        timings[
            "anatomy_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # 5. GRAD-CAM
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        cam_result = (
            self.gradcam.generate(
                global_result[
                    "tensor"
                ],
                class_idx=
                    grade,
            )
        )

        heatmap = (
            cam_result[
                "heatmap"
            ]
        )

        gradcam_overlay = (
            create_gradcam_overlay(
                working_image,
                heatmap,
            )
        )

        gradcam_path = (
            case_dir
            /
            "gradcam.png"
        )

        cv2.imwrite(
            str(
                gradcam_path
            ),
            gradcam_overlay,
        )


        retina_mask = (
            lesion_result[
                "retina_mask"
            ]
        )

        combined_lesion_mask = (
            lesion_result[
                "masks"
            ]
            .max(
                axis=0
            )
            .astype(
                np.uint8
            )
        )


        fov_attribution = (
            attribution_in_fov(
                heatmap,
                retina_mask,
            )
        )

        lesion_overlap = (
            lesion_attribution_overlap(
                heatmap,
                combined_lesion_mask,
            )
        )


        if (
            combined_lesion_mask.sum()
            ==
            0
            and
            grade
            ==
            0
        ):

            lesion_overlap_for_integrity = (
                fov_attribution
            )

        else:

            lesion_overlap_for_integrity = (
                lesion_overlap
            )


        xai_integrity = float(
            np.clip(
                0.55
                *
                fov_attribution
                +
                0.45
                *
                lesion_overlap_for_integrity,
                0.0,
                1.0,
            )
        )


        timings[
            "xai_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # 6. MEASURED STABILITY
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        stability = (
            self.stability_engine.evaluate(
                working_image
            )
        )

        timings[
            "stability_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # 7. P-SCORE + CONCORDANCE
        # ====================================================

        stage_start = (
            time.perf_counter()
        )

        fusion_lesions = (
            self._fusion_lesions(
                lesion_result
            )
        )


        # NV branch does not exist yet.
        # Explicit None prevents false NV claims.
        nv_evidence = None


        p_score = (
            pathology_score_v2(
                fusion_lesions,
                nv_evidence=
                    nv_evidence,
            )
        )


        concordance = (
            grade_evidence_concordance_v2(
                grade=
                    grade,

                lesions=
                    fusion_lesions,

                nv_evidence=
                    nv_evidence,

                severe_criteria=
                    None,
            )
        )


        # RDR calibration improved on held-out
        # prototype calibration evaluation.
        #
        # Therefore T-Score V2 uses calibrated
        # operational RDR route confidence.
        operational_confidence = float(
            global_result[
                "rdr_route_confidence"
            ]
        )


        t_score = (
            trust_score_v2(
                image_reliability=
                    float(
                        quality[
                            "score"
                        ]
                    ),

                calibrated_confidence=
                    operational_confidence,

                concordance=
                    float(
                        concordance[
                            "score"
                        ]
                    )
                    /
                    100.0,

                xai_integrity=
                    xai_integrity,

                stability=
                    float(
                        stability[
                            "score"
                        ]
                    )
                    /
                    100.0,
            )
        )


        timings[
            "trace_ms"
        ] = round(
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0,
            2,
        )


        # ====================================================
        # 8. ROUTING
        # ====================================================

        recommendation = (
            self._recommendation(
                quality=
                    quality,

                referable_dr=
                    global_result[
                        "referable_dr"
                    ],

                concordance=
                    concordance,

                trust=
                    t_score,

                stability=
                    stability,
            )
        )


        # ====================================================
        # SERIALIZABLE LESION SUMMARY
        # ====================================================

        lesion_summary = {}

        for (
            name,
            info
        ) in lesion_result[
            "evidence"
        ].items():

            lesion_summary[
                name
            ] = {
                "count":
                    int(
                        info[
                            "count"
                        ]
                    ),

                "area_px":
                    int(
                        info[
                            "area_px"
                        ]
                    ),

                "retinal_area_fraction":
                    float(
                        info[
                            "retinal_area_fraction"
                        ]
                    ),

                "mean_confidence":
                    float(
                        info[
                            "mean_confidence"
                        ]
                    ),

                "peak_confidence":
                    float(
                        info[
                            "peak_confidence"
                        ]
                    ),

                "evidence":
                    float(
                        info.get(
                            "evidence",
                            0.0,
                        )
                    ),

                "components":
                    info.get(
                        "components",
                        [],
                    ),
            }


        # ====================================================
        # FINAL RESULT
        # ====================================================

        result = {

            "engine_version":
                self.VERSION,

            "case_id":
                case_id,

            "quality": {
                **quality,

                "enhancement_applied":
                    enhancement_applied,
            },


            "prediction": {

                "icdr_grade":
                    grade,

                "grade_name":
                    GRADE_NAMES[
                        grade
                    ],

                "grade_probabilities_raw":
                    global_result[
                        "grade_probabilities_raw"
                    ],

                "grade_confidence_raw":
                    global_result[
                        "grade_confidence_raw"
                    ],

                "grade_temperature":
                    global_result[
                        "grade_temperature"
                    ],

                "grade_confidence_temperature_scaled":
                    global_result[
                        "grade_confidence_temperature_scaled"
                    ],

                "grade_calibration_status":
                    global_result[
                        "grade_calibration_status"
                    ],

                "rdr_probability_raw":
                    global_result[
                        "rdr_probability_raw"
                    ],

                "rdr_probability_calibrated":
                    global_result[
                        "rdr_probability_calibrated"
                    ],

                "rdr_temperature":
                    global_result[
                        "rdr_temperature"
                    ],

                "rdr_threshold":
                    global_result[
                        "rdr_threshold"
                    ],

                "referable_dr":
                    global_result[
                        "referable_dr"
                    ],

                "rdr_route_confidence":
                    global_result[
                        "rdr_route_confidence"
                    ],

                "rdr_calibration_status":
                    global_result[
                        "rdr_calibration_status"
                    ],
            },


            "lesions":
                lesion_summary,


            "advanced_evidence": {
                "neovascularization": {
                    "status":
                        "MODEL_UNAVAILABLE",

                    "evidence":
                        None,
                },

                "severe_421_criteria": {
                    "status":
                        "NOT_INDEPENDENTLY_MEASURED"
                },
            },


            "anatomy":
                anatomy,


            "p_score":
                p_score,


            "concordance":
                concordance,


            "xai_integrity": {

                "score":
                    round(
                        xai_integrity
                        *
                        100.0,
                        1,
                    ),

                "attribution_in_retinal_fov":
                    round(
                        fov_attribution
                        *
                        100.0,
                        1,
                    ),

                "attribution_lesion_overlap":
                    round(
                        lesion_overlap
                        *
                        100.0,
                        1,
                    ),
            },


            "stability":
                stability,


            "t_score":
                t_score,


            "recommendation":
                recommendation,


            "artifacts": {

                "analysis_input":
                    str(
                        analysis_input
                    ),

                "lesion_overlay":
                    str(
                        lesion_overlay_path
                    ),

                "gradcam":
                    str(
                        gradcam_path
                    ),

                "structural_overlay":
                    anatomy.get(
                        "artifacts",
                        {}
                    ).get(
                        "structural_overlay"
                    ),

                "vessel_mask":
                    anatomy.get(
                        "artifacts",
                        {}
                    ).get(
                        "vessel_mask"
                    ),
            },


            "timings":
                timings,
        }


        result[
            "timings"
        ][
            "total_ms"
        ] = round(
            (
                time.perf_counter()
                -
                total_start
            )
            *
            1000.0,
            2,
        )


        self._save_json(
            case_dir,
            result
        )

        return result


    # ========================================================
    # SAVE JSON
    # ========================================================

    @staticmethod
    def _save_json(
        case_dir,
        result,
    ):

        output = (
            case_dir
            /
            "result.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                result,
                f,
                indent=2,
            )


    # ========================================================
    # CLEANUP
    # ========================================================

    def close(
        self
    ):

        self.gradcam.close()

        self.stability_engine.close()
