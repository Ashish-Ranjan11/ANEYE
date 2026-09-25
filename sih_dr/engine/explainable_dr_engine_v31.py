from pathlib import Path
import json
import time


from sih_dr.engine.explainable_dr_engine_v3 import (
    ExplainableDREngineV3,
    TRACE_ROUTE_CODES,
)

from sih_dr.xai.clinical_fusion_v31 import (
    grade_evidence_concordance_v31,
)

from sih_dr.xai.clinical_fusion_v2 import (
    trust_score_v2,
)


class ExplainableDREngineV31(
    ExplainableDREngineV3
):

    VERSION = "NETRAAI_ENGINE_V31"

    TRACE_VERSION = "TRACE_DR_V31"


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
        output_dir="results/sih_dr_v31/cases",
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

            output_dir=
                output_dir,
        )


        self.grade0_gate_contract_path = Path(
            grade0_gate_contract
        )


        if not self.grade0_gate_contract_path.exists():

            raise FileNotFoundError(
                "Grade-0 gate contract not found: "
                f"{self.grade0_gate_contract_path}"
            )


        with open(
            self.grade0_gate_contract_path,
            "r",
            encoding="utf-8",
        ) as file:

            contract = json.load(
                file
            )


        if (
            contract.get(
                "version"
            )
            !=
            "GRADE0_LESION_CONFLICT_GATE_V1"
        ):

            raise RuntimeError(
                "Unexpected Grade-0 gate contract version."
            )


        self.grade0_conflict_threshold = float(
            contract[
                "threshold"
            ]
        )


        print()
        print(
            "=========================================="
        )
        print(
            "NETRAAI ENGINE V3.1 READY"
        )
        print(
            "Concordance V3.1 + TRACE-DR V3.1"
        )
        print(
            "Grade-0 conflict threshold:",
            self.grade0_conflict_threshold,
        )
        print(
            "=========================================="
        )
        print()


    # ========================================================
    # ORIGINAL V3 LESION FUSION INPUT
    # ========================================================

    @staticmethod
    def _v3_fusion_lesions(
        result
    ):

        lesions = (
            result.get(
                "lesions"
            )
            or
            {}
        )


        def value(
            name
        ):

            item = (
                lesions.get(
                    name
                )
                or
                {}
            )


            if int(
                item.get(
                    "count",
                    0,
                )
            ) == 0:

                return 0.0


            return float(
                item.get(
                    "mean_confidence",
                    0.0,
                )
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
    # COMPOSITE LESION EVIDENCE FOR GRADE-0 GATE ONLY
    # ========================================================

    @staticmethod
    def _grade0_composite_evidence(
        result
    ):

        lesions = (
            result.get(
                "lesions"
            )
            or
            {}
        )


        def value(
            name
        ):

            return float(
                (
                    lesions.get(
                        name
                    )
                    or
                    {}
                )
                .get(
                    "evidence",
                    0.0,
                )
            )


        return {

            "MA":
                value("MA"),

            "HE":
                value("HE"),

            "EX":
                value("EX"),

            "SE":
                value("SE"),
        }


    # ========================================================
    # V3.1 ROUTE CONTRACT
    # ========================================================

    @classmethod
    def _attach_route_code_v31(
        cls,
        recommendation,
    ):

        action = recommendation[
            "action"
        ]


        recommendation[
            "route_code"
        ] = int(
            TRACE_ROUTE_CODES[
                action
            ]
        )


        recommendation[
            "trace_version"
        ] = cls.TRACE_VERSION


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


        # ----------------------------------------------------
        # Execute all established V3 neural-network paths once.
        # ----------------------------------------------------

        result = super().analyze(
            image_path
        )


        # ----------------------------------------------------
        # Quality gate remains unchanged.
        # ----------------------------------------------------

        if (
            result.get(
                "prediction"
            )
            is None
        ):

            result[
                "engine_version"
            ] = self.VERSION


            result[
                "trace_version"
            ] = self.TRACE_VERSION


            result[
                "recommendation"
            ] = (
                self._attach_route_code_v31(
                    result[
                        "recommendation"
                    ]
                )
            )


            result[
                "grade0_conflict_gate_contract"
            ] = {
                "version":
                    "GRADE0_LESION_CONFLICT_GATE_V1",

                "threshold":
                    self.grade0_conflict_threshold,
            }


            result[
                "timings"
            ][
                "fusion_v31_ms"
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
        # CONCORDANCE V3.1
        # ====================================================

        stage_start = (
            time.perf_counter()
        )


        fusion_lesions = (
            self._v3_fusion_lesions(
                result
            )
        )


        grade0_composite = (
            self._grade0_composite_evidence(
                result
            )
        )


        concordance = (
            grade_evidence_concordance_v31(

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
                    result[
                        "advanced_evidence"
                    ],

                grade0_composite_evidence=
                    grade0_composite,

                grade0_conflict_threshold=
                    self.grade0_conflict_threshold,
            )
        )


        # ====================================================
        # T-SCORE V2 — SAME WEIGHTS
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
        # TRACE-DR V3.1
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
            self._attach_route_code_v31(
                recommendation
            )
        )


        fusion_ms = (
            (
                time.perf_counter()
                -
                stage_start
            )
            *
            1000.0
        )


        # ====================================================
        # UPDATE RESULT
        #
        # P-SCORE IS DELIBERATELY UNCHANGED.
        # ====================================================

        result[
            "engine_version"
        ] = self.VERSION


        result[
            "trace_version"
        ] = self.TRACE_VERSION


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
            "grade0_conflict_gate_contract"
        ] = {

            "version":
                "GRADE0_LESION_CONFLICT_GATE_V1",

            "threshold":
                self.grade0_conflict_threshold,

            "role":
                (
                    "GRADE_0_CONVENTIONAL_LESION_"
                    "DISCORDANCE_OVERRIDE"
                ),

            "clinical_boundary":
                False,
        }


        result[
            "timings"
        ][
            "fusion_v31_ms"
        ] = round(
            fusion_ms,
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
        # SAVE V3.1 RESULT
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