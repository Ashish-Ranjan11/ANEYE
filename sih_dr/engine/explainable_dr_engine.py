from pathlib import Path
import json

import cv2
import numpy as np

from sih_dr.quality.quality_engine import (
    FundusQualityEngine,
    enhance_borderline,
)

from sih_dr.grading.inference import (
    GlobalDRInference,
)

from sih_dr.lesions.inference import (
    LesionInferenceEngine,
    create_lesion_overlay,
)

from sih_dr.xai.gradcam import (
    GlobalDRGradCAM,
    create_gradcam_overlay,
    attribution_in_fov,
    lesion_attribution_overlap,
)

from sih_dr.xai.clinical_fusion import (
    pathology_score,
    grade_evidence_concordance,
    trust_score,
)


GRADE_NAMES = {
    0: "No apparent DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


class ExplainableDREngine:

    def __init__(
        self,
        grader_checkpoint,
        lesion_checkpoint,
        output_dir="results/sih_dr/cases",
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        print("\n=== INITIALIZING TRACE-DR ENGINE ===")

        self.quality_engine = (
            FundusQualityEngine()
        )

        self.global_engine = (
            GlobalDRInference(
                grader_checkpoint
            )
        )

        self.lesion_engine = (
            LesionInferenceEngine(
                lesion_checkpoint
            )
        )

        self.gradcam = (
            GlobalDRGradCAM(
                self.global_engine.model
            )
        )

        print("TRACE-DR engine ready.\n")

    # ----------------------------------------------------
    # LESION EVIDENCE ADAPTER
    # ----------------------------------------------------

    @staticmethod
    def _fusion_lesions(
        lesion_result
    ):

        evidence = (
            lesion_result["evidence"]
        )

        def value(name):

            item = evidence[name]

            # Conservative:
            # absence means zero.
            # otherwise use model confidence,
            # not the earlier saturating heuristic.
            if item["count"] == 0:
                return 0.0

            return float(
                item["mean_confidence"]
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

    # ----------------------------------------------------
    # ACTION LOGIC
    # ----------------------------------------------------

    @staticmethod
    def _recommendation(
        quality,
        grade,
        rdr,
        trust,
        concordance
    ):

        if (
            quality["status"]
            == "UNGRADEABLE"
        ):
            return {
                "action":
                    "RECAPTURE",

                "priority":
                    "HIGH",

                "reason":
                    "Image quality is insufficient for reliable automated screening."
            }

        if (
            concordance["status"] == "LOW"
            or trust["level"] == "LOW"
        ):
            return {
                "action":
                    "HUMAN_REVIEW",

                "priority":
                    "HIGH",

                "reason":
                    "Model prediction and clinical evidence are insufficiently concordant."
            }

        if rdr:
            return {
                "action":
                    "REFER_OPHTHALMOLOGY",

                "priority":
                    "HIGH",

                "reason":
                    "Referable diabetic retinopathy screening result."
            }

        if (
            quality["status"]
            == "BORDERLINE"
        ):
            return {
                "action":
                    "REVIEW_OR_RECAPTURE",

                "priority":
                    "MODERATE",

                "reason":
                    "Retinal image is borderline quality."
            }

        return {
            "action":
                "ROUTINE_SCREENING",

            "priority":
                "LOW",

            "reason":
                "No referable DR identified with sufficient system reliability."
        }

    # ----------------------------------------------------
    # ANALYZE
    # ----------------------------------------------------

    def analyze(
        self,
        image_path
    ):

        image_path = Path(
            image_path
        )

        image = cv2.imread(
            str(image_path)
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
            / case_id
        )

        case_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------
        # 1. IMAGE QUALITY
        # -----------------------------------------

        quality_original = (
            self.quality_engine.analyze(
                image
            )
        )

        working_image = (
            image.copy()
        )

        enhancement_applied = False

        quality = quality_original

        if (
            quality_original["status"]
            == "BORDERLINE"
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

            # Only accept enhancement if quality improves.
            if (
                enhanced_quality["score"]
                >
                quality_original["score"]
            ):

                working_image = enhanced

                quality = (
                    enhanced_quality
                )

                enhancement_applied = True

                cv2.imwrite(
                    str(
                        case_dir
                        / "enhanced.png"
                    ),
                    enhanced
                )

        # -----------------------------------------
        # CRITICAL SAFETY GATE
        # -----------------------------------------

        if (
            quality["status"]
            == "UNGRADEABLE"
        ):

            result = {
                "case_id":
                    case_id,

                "quality":
                    quality,

                "enhancement_applied":
                    enhancement_applied,

                "prediction":
                    None,

                "lesions":
                    None,

                "p_score":
                    None,

                "concordance":
                    None,

                "xai_integrity":
                    None,

                "t_score":
                    None,

                "recommendation": {
                    "action":
                        "RECAPTURE",

                    "priority":
                        "HIGH",

                    "reason":
                        "Image failed retinal quality gate."
                }
            }

            self._save_json(
                case_dir,
                result
            )

            return result

        # -----------------------------------------
        # 2. GLOBAL DR PREDICTION
        # -----------------------------------------

        global_result = (
            self.global_engine.predict(
                working_image
            )
        )

        grade = (
            global_result["grade"]
        )

        # -----------------------------------------
        # 3. LESION INFERENCE
        # -----------------------------------------

        lesion_result = (
            self.lesion_engine.predict(
                working_image
            )
        )

        lesion_overlay = (
            create_lesion_overlay(
                working_image,
                lesion_result["masks"]
            )
        )

        lesion_overlay_path = (
            case_dir
            / "lesion_overlay.png"
        )

        cv2.imwrite(
            str(
                lesion_overlay_path
            ),
            lesion_overlay
        )

        # -----------------------------------------
        # 4. GRAD-CAM
        # -----------------------------------------

        tensor = (
            global_result["tensor"]
        )

        cam_result = (
            self.gradcam.generate(
                tensor,
                class_idx=grade
            )
        )

        heatmap = (
            cam_result["heatmap"]
        )

        gradcam_overlay = (
            create_gradcam_overlay(
                working_image,
                heatmap
            )
        )

        gradcam_path = (
            case_dir
            / "gradcam.png"
        )

        cv2.imwrite(
            str(
                gradcam_path
            ),
            gradcam_overlay
        )

        # -----------------------------------------
        # 5. XAI INTEGRITY
        # -----------------------------------------

        retina_mask = (
            lesion_result[
                "retina_mask"
            ]
        )

        combined_lesion_mask = (
            lesion_result["masks"]
            .max(axis=0)
            .astype(np.uint8)
        )

        fov_attribution = (
            attribution_in_fov(
                heatmap,
                retina_mask
            )
        )

        lesion_overlap = (
            lesion_attribution_overlap(
                heatmap,
                combined_lesion_mask
            )
        )

        # Do not punish a grade-0 case simply
        # because there are no lesion pixels.
        if (
            combined_lesion_mask.sum()
            == 0
            and grade == 0
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
                * fov_attribution
                +
                0.45
                * lesion_overlap_for_integrity,
                0,
                1
            )
        )

        # -----------------------------------------
        # 6. CLINICAL EVIDENCE FUSION
        # -----------------------------------------

        fusion_lesions = (
            self._fusion_lesions(
                lesion_result
            )
        )

        p_score = (
            pathology_score(
                fusion_lesions
            )
        )

        concordance = (
            grade_evidence_concordance(
                grade,
                fusion_lesions
            )
        )

        # IMPORTANT:
        # Current global confidence is not
        # temperature-calibrated yet.
        model_confidence = float(
            global_result[
                "grade_confidence"
            ]
        )

        t_score = (
            trust_score(
                image_reliability=float(
                    quality["score"]
                ),

                calibrated_confidence=
                    model_confidence,

                concordance=float(
                    concordance["score"]
                ) / 100.0,

                xai_integrity=
                    xai_integrity,

                stability=0.90
            )
        )

        # -----------------------------------------
        # 7. ROUTING
        # -----------------------------------------

        recommendation = (
            self._recommendation(
                quality,
                grade,
                global_result[
                    "referable_dr"
                ],
                t_score,
                concordance
            )
        )

        # -----------------------------------------
        # SERIALIZABLE LESION SUMMARY
        # -----------------------------------------

        lesion_summary = {}

        for name, info in (
            lesion_result[
                "evidence"
            ].items()
        ):

            lesion_summary[
                name
            ] = {
                "count":
                    info["count"],

                "area_px":
                    info["area_px"],

                "retinal_area_fraction":
                    info[
                        "retinal_area_fraction"
                    ],

                "mean_confidence":
                    info[
                        "mean_confidence"
                    ],

                "peak_confidence":
                    info[
                        "peak_confidence"
                    ],

                "components":
                    info.get(
                        "components",
                        []
                    ),
            }

        # -----------------------------------------
        # FINAL RESULT
        # -----------------------------------------

        result = {

            "case_id":
                case_id,

            "image_width":
                int(
                    working_image.shape[1]
                ),

            "image_height":
                int(
                    working_image.shape[0]
                ),

            "quality": {
                **quality,

                "enhancement_applied":
                    enhancement_applied
            },

            "prediction": {
                "icdr_grade":
                    grade,

                "grade_name":
                    GRADE_NAMES[grade],

                "grade_confidence":
                    global_result[
                        "grade_confidence"
                    ],

                "grade_probabilities":
                    global_result[
                        "grade_probabilities"
                    ],

                "rdr_probability":
                    global_result[
                        "rdr_probability"
                    ],

                "referable_dr":
                    global_result[
                        "referable_dr"
                    ],

                "confidence_calibration":
                    "NOT_YET_APPLIED"
            },

            "lesions":
                lesion_summary,

            "p_score":
                p_score,

            "concordance":
                concordance,

            "xai_integrity": {
                "score":
                    round(
                        xai_integrity
                        * 100,
                        1
                    ),

                "attribution_in_retinal_fov":
                    round(
                        fov_attribution
                        * 100,
                        1
                    ),

                "attribution_lesion_overlap":
                    round(
                        lesion_overlap
                        * 100,
                        1
                    ),
            },

            "t_score":
                t_score,

            "recommendation":
                recommendation,

            "artifacts": {
                "lesion_overlay":
                    str(
                        lesion_overlay_path
                    ),

                "gradcam":
                    str(
                        gradcam_path
                    )
            }
        }

        self._save_json(
            case_dir,
            result
        )

        return result

    # ----------------------------------------------------
    # JSON
    # ----------------------------------------------------

    @staticmethod
    def _save_json(
        case_dir,
        result
    ):

        output = (
            case_dir
            / "result.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                result,
                f,
                indent=2
            )