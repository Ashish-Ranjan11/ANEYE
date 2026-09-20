from pathlib import Path
import sys
import json


ROOT = Path(
    __file__
).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)


from sih_dr.engine.explainable_dr_engine_v2 import (
    ExplainableDREngineV2,
)


GRADER = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "grading"
    / "global_final.pth"
)

LESIONS = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "lesions"
    / "lesion_final.pth"
)

CALIBRATION = (
    ROOT
    / "nationals"
    / "calibration"
    / "calibration_config.json"
)

IMAGE = (
    ROOT
    / "datasets"
    / "raw"
    / "APTOS2019"
    / "train_images"
    / "000c1434d8d7.png"
)


engine = ExplainableDREngineV2(
    grader_checkpoint=
        GRADER,

    lesion_checkpoint=
        LESIONS,

    calibration_config=
        CALIBRATION,
)


result = engine.analyze(
    IMAGE
)


summary = {

    "case_id":
        result[
            "case_id"
        ],

    "quality":
        result[
            "quality"
        ],

    "prediction":
        result[
            "prediction"
        ],

    "p_score":
        result[
            "p_score"
        ],

    "concordance":
        result[
            "concordance"
        ],

    "xai_integrity":
        result[
            "xai_integrity"
        ],

    "stability": {
        "score":
            result[
                "stability"
            ][
                "score"
            ],

        "level":
            result[
                "stability"
            ][
                "level"
            ],
    },

    "t_score":
        result[
            "t_score"
        ],

    "advanced_evidence":
        result[
            "advanced_evidence"
        ],

    "recommendation":
        result[
            "recommendation"
        ],

    "timings":
        result[
            "timings"
        ],
}


print(
    "\n=========================================="
)

print(
    "NETRAAI V2 END-TO-END RESULT"
)

print(
    "==========================================\n"
)


print(
    json.dumps(
        summary,
        indent=2,
    )
)


engine.close()
