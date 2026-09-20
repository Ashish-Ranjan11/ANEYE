from pathlib import Path
import sys
import json

import cv2


ROOT = Path(
    __file__
).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)


from sih_dr.grading.calibrated_inference import (
    CalibratedGlobalDRInference,
)

from sih_dr.xai.stability import (
    StabilityEvaluator,
)


CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "grading"
    / "global_final.pth"
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


image = cv2.imread(
    str(IMAGE)
)

if image is None:

    raise RuntimeError(
        f"Could not load {IMAGE}"
    )


global_engine = (
    CalibratedGlobalDRInference(
        CHECKPOINT,
        CALIBRATION,
    )
)


stability_engine = (
    StabilityEvaluator(
        global_engine
    )
)


result = (
    stability_engine.evaluate(
        image
    )
)


print(
    "\n=== NETRAAI MEASURED STABILITY ===\n"
)

print(
    json.dumps(
        result,
        indent=2,
    )
)


stability_engine.close()
