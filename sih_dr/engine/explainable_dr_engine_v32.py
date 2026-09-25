from pathlib import Path
import time


from sih_dr.engine.explainable_dr_engine_v31 import (
    ExplainableDREngineV31,
)

from sih_dr.engine.explainable_dr_engine_v3 import (
    TRACE_ROUTE_CODES,
)


class ExplainableDREngineV32(
    ExplainableDREngineV31
):
    """
    NetraAI Engine V3.2

    Neural models:
        unchanged

    P-score:
        unchanged

    Concordance:
        CONCORDANCE_V31

    New TRACE safety invariants:
        1. NV ALERT_ONLY -> HUMAN_REVIEW
        2. VH ALERT_ONLY -> HUMAN_REVIEW
        3. Predicted ICDR grade >= 2 cannot terminate ROUTINE

    VB/IRMA ALERT_ONLY is NOT automatically forced to review.
    """

    VERSION = "NETRAAI_ENGINE_V32"

    TRACE_VERSION = "TRACE_DR_V32"


    def __init__(
        self,
        grader_checkpoint,
        lesion_checkpoint,
        calibration_config,
        advanced_checkpoint=None,
        advanced_operating_points=None,
        grade0_gate_contract=(
            "nationals/calibration/"
            "grade0_lesion_conflict_gate_v1.json"
        ),
        output_dir="results/sih_dr_v32/cases",
    ):

        super().__init__(
            grader_checkpoint=
                grader_checkpoint,

            lesion_checkpoint=
                lesion_checkpoint,

            calibration_config=
                calibration_config,

            advanced_checkpoint=
                advanced_checkpoint,

            advanced_operating_points=
                advanced_operating_points,

            grade0_gate_contract=
                grade0_gate_contract,

            output_dir=
                output_dir,
        )


        print()
        print(
            "=========================================="
        )
        print(
            "NETRAAI ENGINE V3.2 READY"
        )
        print(
            "Concordance V3.1 + TRACE-DR V3.2"
        )
        print(
            "Advanced ALERT_ONLY safety routing enabled"
        )
        print(
            "=========================================="
        )
        print()


    @staticmethod
    def _advanced_state(
        result,
        label,
    ):

        advanced = (
            result.get(
                "advanced_evidence"
            )
            or
            {}
        )


        evidence = (
            advanced.get(
                "evidence"
            )
            or
            {}
        )


        item = (
            evidence.get(
                label
            )
            or
            {}
        )


        return item.get(
            "state"
        )


    def analyze(
        self,
        image_path,
    ):

        total_start = (
            time.perf_counter()
        )


        # ====================================================
        # RUN COMPLETE V3.1 PIPELINE
        # ====================================================

        result = super().analyze(
            image_path
        )


        safety_start = (
            time.perf_counter()
        )


        result[
            "engine_version"
        ] = self.VERSION


        result[
            "trace_version"
        ] = self.TRACE_VERSION


        # ====================================================
        # QUALITY-GATED CASE
        # ====================================================

        if (
            result.get(
                "prediction"
            )
            is None
        ):

            recommendation = (
                result.get(
                    "recommendation"
                )
                or
                {}
            )


            recommendation[
                "trace_version"
            ] = self.TRACE_VERSION


            result[
                "recommendation"
            ] = recommendation


            result[
                "trace_v32_safety"
            ] = {
                "applied":
                    False,

                "reason":
                    "QUALITY_GATE_TERMINAL_ROUTE",
            }


            result[
                "timings"
            ][
                "trace_v32_ms"
            ] = round(
                (
                    time.perf_counter()
                    -
                    safety_start
                )
                *
                1000.0,
                2,
            )


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


            case_dir = (
                Path(
                    self.output_dir
                )
                /
                result[
                    "case_id"
                ]
            )


            self._save_json(
                case_dir,
                result,
            )


            return result


        # ====================================================
        # CURRENT STATE
        # ====================================================

        prediction = result[
            "prediction"
        ]


        grade = int(
            prediction[
                "icdr_grade"
            ]
        )


        recommendation = (
            result.get(
                "recommendation"
            )
            or
            {}
        )


        current_action = (
            recommendation.get(
                "action"
            )
        )


        nv_state = (
            self._advanced_state(
                result,
                "NV",
            )
        )


        vh_state = (
            self._advanced_state(
                result,
                "VH",
            )
        )


        vb_state = (
            self._advanced_state(
                result,
                "VB_IRMA",
            )
        )


        # ====================================================
        # TRACE V3.2 SAFETY INVARIANTS
        # ====================================================

        reasons = []


        if (
            nv_state
            ==
            "ALERT_ONLY"
        ):

            reasons.append(
                "NV_ALERT_ONLY"
            )


        if (
            vh_state
            ==
            "ALERT_ONLY"
        ):

            reasons.append(
                "VH_ALERT_ONLY"
            )


        if (
            grade >= 2
            and
            current_action
            ==
            "ROUTINE_SCREENING"
        ):

            reasons.append(
                "ICDR_GRADE_GE_2_CANNOT_ROUTE_ROUTINE"
            )


        # ====================================================
        # SAFETY OVERRIDE
        # ====================================================

        if reasons:

            recommendation = {

                "action":
                    "HUMAN_REVIEW",

                "priority":
                    "HIGH",

                "reason":
                    (
                        "TRACE-DR V3.2 safety invariant "
                        "requires human review before "
                        "final disposition."
                    ),

                "route_code":
                    int(
                        TRACE_ROUTE_CODES[
                            "HUMAN_REVIEW"
                        ]
                    ),

                "trace_version":
                    self.TRACE_VERSION,
            }


            safety_applied = True


        else:

            recommendation[
                "route_code"
            ] = int(
                TRACE_ROUTE_CODES[
                    recommendation[
                        "action"
                    ]
                ]
            )


            recommendation[
                "trace_version"
            ] = self.TRACE_VERSION


            safety_applied = False


        # ====================================================
        # AUDIT METADATA
        # ====================================================

        result[
            "recommendation"
        ] = recommendation


        result[
            "trace_v32_safety"
        ] = {

            "applied":
                safety_applied,

            "reasons":
                reasons,

            "predicted_grade":
                grade,

            "advanced_states": {

                "VB_IRMA":
                    vb_state,

                "NV":
                    nv_state,

                "VH":
                    vh_state,
            },

            "invariants": {

                "nv_alert_only_requires_human_review":
                    True,

                "vh_alert_only_requires_human_review":
                    True,

                "predicted_grade_ge_2_cannot_be_routine":
                    True,

                "vb_irma_alert_only_forced_review":
                    False,
            },
        }


        result[
            "timings"
        ][
            "trace_v32_ms"
        ] = round(
            (
                time.perf_counter()
                -
                safety_start
            )
            *
            1000.0,
            2,
        )


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
        # SAVE FINAL V3.2 RESULT
        # ====================================================

        case_dir = (
            Path(
                self.output_dir
            )
            /
            result[
                "case_id"
            ]
        )


        self._save_json(
            case_dir,
            result,
        )


        return result