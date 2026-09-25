from pathlib import Path
import time

import cv2


from sih_dr.engine.explainable_dr_engine_v2 import (
    ExplainableDREngineV2,
)

from sih_dr.advanced.inference import (
    AdvancedEvidenceInference,
)

from sih_dr.xai.clinical_fusion_v3 import (
    grade_evidence_concordance_v3,
)

from sih_dr.xai.clinical_fusion_v2 import (
    trust_score_v2,
)


# ============================================================
# TRACE ROUTE CONTRACT
# ============================================================

TRACE_ROUTE_CODES = {

    "ROUTINE_SCREENING":
        1,

    "REFER_OPHTHALMOLOGY":
        2,

    "HUMAN_REVIEW":
        3,

    "REVIEW_OR_RECAPTURE":
        4,

    "RECAPTURE":
        5,
}


# ============================================================
# NETRAAI ENGINE V3
# ============================================================

class ExplainableDREngineV3(
    ExplainableDREngineV2
):

    VERSION = "NETRAAI_ENGINE_V3"

    TRACE_VERSION = "TRACE_DR_V3"


    def __init__(
        self,
        grader_checkpoint,
        lesion_checkpoint,
        calibration_config,
        advanced_checkpoint=None,
        advanced_operating_points=None,
        output_dir="results/sih_dr_v3/cases",
    ):

        # ----------------------------------------------------
        # Initialize validated V2 pipeline
        # ----------------------------------------------------

        super().__init__(
            grader_checkpoint=
                grader_checkpoint,

            lesion_checkpoint=
                lesion_checkpoint,

            calibration_config=
                calibration_config,

            output_dir=
                output_dir,
        )


        # ----------------------------------------------------
        # Advanced evidence model
        # ----------------------------------------------------

        self.advanced_engine = (
            AdvancedEvidenceInference(
                checkpoint_path=
                    advanced_checkpoint,

                operating_points_path=
                    advanced_operating_points,
            )
        )


        print()
        print(
            "=========================================="
        )

        print(
            "NETRAAI ENGINE V3 READY"
        )

        print(
            "Advanced Evidence + Concordance V3 enabled"
        )

        print(
            "=========================================="
        )

        print()


    # ========================================================
    # CONVENTIONAL LESION ADAPTER
    # ========================================================

    @staticmethod
    def _fusion_lesions_from_result(
        result
    ):

        lesions = result.get(
            "lesions"
        )


        if not isinstance(
            lesions,
            dict,
        ):

            return {
                "ma_evidence":
                    0.0,

                "he_evidence":
                    0.0,

                "ex_evidence":
                    0.0,

                "se_evidence":
                    0.0,
            }


        def value(
            name
        ):

            item = lesions.get(
                name,
                {}
            )


            return float(
                item.get(
                    "mean_confidence",
                    0.0,
                )
            )


        return {

            "ma_evidence":
                value(
                    "MA"
                ),

            "he_evidence":
                value(
                    "HE"
                ),

            "ex_evidence":
                value(
                    "EX"
                ),

            "se_evidence":
                value(
                    "SE"
                ),
        }


    # ========================================================
    # TRACE ROUTE CODE
    # ========================================================

    @staticmethod
    def _attach_route_code(
        recommendation
    ):

        action = recommendation.get(
            "action"
        )


        recommendation[
            "route_code"
        ] = int(
            TRACE_ROUTE_CODES[
                action
            ]
        )


        recommendation[
            "trace_version"
        ] = (
            ExplainableDREngineV3
            .TRACE_VERSION
        )


        return recommendation


    # ========================================================
    # ANALYSIS
    # ========================================================

    def analyze(
        self,
        image_path,
    ):

        total_start = (
            time.perf_counter()
        )


        # ====================================================
        # RUN COMPLETE VALIDATED V2 PIPELINE FIRST
        # ====================================================

        result = super().analyze(
            image_path
        )


        case_id = result[
            "case_id"
        ]


        case_dir = (
            Path(
                self.output_dir
            )
            /
            case_id
        )


        # ====================================================
        # UNGRADEABLE SAFETY GATE
        #
        # Do NOT run disease evidence models on an image that
        # already failed the retinal quality gate.
        # ====================================================

        if (
            result.get(
                "prediction"
            )
            is None
        ):

            result[
                "advanced_evidence"
            ] = {

                "version":
                    "ADVANCED_EVIDENCE_INFERENCE_V1",

                "status":
                    "NOT_RUN_QUALITY_GATE",

                "reason":
                    (
                        "Advanced disease evidence was not "
                        "evaluated because the image failed "
                        "the retinal quality gate."
                    ),

                "evidence":
                    None,

                "routing_flags":
                    None,
            }


            result[
                "concordance"
            ] = None


            result[
                "t_score"
            ] = None


            result[
                "trace_version"
            ] = self.TRACE_VERSION


            result[
                "recommendation"
            ] = self._attach_route_code(
                result[
                    "recommendation"
                ]
            )


            result[
                "timings"
            ][
                "advanced_evidence_ms"
            ] = 0.0


            result[
                "timings"
            ][
                "fusion_v3_ms"
            ] = 0.0


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
                result,
            )


            return result


        # ====================================================
        # LOAD THE EXACT IMAGE USED BY THE V2 PIPELINE
        #
        # This matters if BORDERLINE enhancement was applied.
        # ====================================================

        analysis_input = (
            result
            .get(
                "artifacts",
                {}
            )
            .get(
                "analysis_input"
            )
        )


        working_image = None


        if analysis_input is not None:

            working_image = cv2.imread(
                str(
                    analysis_input
                )
            )


        if working_image is None:

            working_image = cv2.imread(
                str(
                    image_path
                )
            )


        if working_image is None:

            raise RuntimeError(
                f"V3 could not reload analysis image: "
                f"{image_path}"
            )


        # ====================================================
        # ADVANCED EVIDENCE
        #
        # VB/IRMA + NV + VH
        # ====================================================

        stage_start = (
            time.perf_counter()
        )


        advanced_evidence = (
            self.advanced_engine.predict(
                working_image
            )
        )


        result[
            "timings"
        ][
            "advanced_evidence_ms"
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
        # CONVENTIONAL LESION EVIDENCE
        # ====================================================

        fusion_lesions = (
            self._fusion_lesions_from_result(
                result
            )
        )


        # ====================================================
        # CONCORDANCE V3
        # ====================================================

        stage_start = (
            time.perf_counter()
        )


        concordance = (
            grade_evidence_concordance_v3(

                grade=int(
                    result[
                        "prediction"
                    ][
                        "icdr_grade"
                    ]
                ),

                lesions=
                    fusion_lesions,

                advanced_evidence=
                    advanced_evidence,
            )
        )


        # ====================================================
        # TRUST SCORE
        #
        # T-score mathematics remains V2.
        #
        # What changes is the concordance evidence supplied
        # into it.
        # ====================================================

        trust = trust_score_v2(

            image_reliability=float(
                result[
                    "quality"
                ][
                    "score"
                ]
            ),

            calibrated_confidence=float(
                result[
                    "prediction"
                ][
                    "rdr_route_confidence"
                ]
            ),

            concordance=float(
                concordance[
                    "score"
                ]
            )
            /
            100.0,

            xai_integrity=float(
                result[
                    "xai_integrity"
                ][
                    "score"
                ]
            )
            /
            100.0,

            stability=float(
                result[
                    "stability"
                ][
                    "score"
                ]
            )
            /
            100.0,
        )


        # ====================================================
        # TRACE ROUTING
        #
        # Existing routing precedence is retained.
        # Concordance V3 can now cause advanced-evidence
        # disagreement to enter HUMAN_REVIEW.
        # ====================================================

        recommendation = (
            self._recommendation(

                quality=
                    result[
                        "quality"
                    ],

                referable_dr=bool(
                    result[
                        "prediction"
                    ][
                        "referable_dr"
                    ]
                ),

                concordance=
                    concordance,

                trust=
                    trust,

                stability=
                    result[
                        "stability"
                    ],
            )
        )


        recommendation = (
            self._attach_route_code(
                recommendation
            )
        )


        result[
            "timings"
        ][
            "fusion_v3_ms"
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
        # UPDATE P-SCORE ADVANCED-EVIDENCE METADATA
        #
        # IMPORTANT:
        #
        # NV is NOT inserted into the weighted P-score.
        #
        # This merely removes the obsolete "NV unavailable"
        # metadata from the V2 result.
        # ====================================================

        nv = (
            advanced_evidence[
                "evidence"
            ][
                "NV"
            ]
        )


        if (
            result.get(
                "p_score"
            )
            is not None
        ):

            result[
                "p_score"
            ][
                "advanced_evidence"
            ] = {

                "source":
                    (
                        "ADVANCED_EVIDENCE_"
                        "INFERENCE_V1"
                    ),

                "nv_available":
                    True,

                "nv_raw_model_score":
                    float(
                        nv[
                            "probability_raw"
                        ]
                    ),

                "nv_calibration_status":
                    nv[
                        "calibration_status"
                    ],

                "nv_state":
                    nv[
                        "state"
                    ],

                "nv_alert_positive":
                    bool(
                        nv[
                            "alert_positive"
                        ]
                    ),

                "nv_confirmed_positive":
                    bool(
                        nv[
                            "confirmed_positive"
                        ]
                    ),

                "note":
                    (
                        "NV is exposed as independent "
                        "advanced evidence and is not "
                        "included in the weighted P-score."
                    ),
            }


        # ====================================================
        # FINAL V3 RESULT
        # ====================================================

        result[
            "engine_version"
        ] = self.VERSION


        result[
            "trace_version"
        ] = self.TRACE_VERSION


        result[
            "advanced_evidence"
        ] = advanced_evidence


        result[
            "concordance"
        ] = concordance


        result[
            "t_score"
        ] = trust


        result[
            "recommendation"
        ] = recommendation


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


        # ====================================================
        # SAVE FINAL V3 JSON
        # ====================================================

        self._save_json(
            case_dir,
            result,
        )


        return result


    # ========================================================
    # CLEANUP
    # ========================================================

    def close(
        self
    ):

        super().close()