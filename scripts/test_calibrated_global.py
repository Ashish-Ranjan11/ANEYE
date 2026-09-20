from pathlib import Path
import sys

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sih_dr.grading.calibrated_inference import (
    CalibratedGlobalDRInference,
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


engine = CalibratedGlobalDRInference(
    CHECKPOINT,
    CALIBRATION,
)

image = cv2.imread(
    str(IMAGE)
)

result = engine.predict(
    image
)

result.pop(
    "tensor"
)

print(
    "\n=== CALIBRATED GLOBAL INFERENCE ==="
)

for key, value in result.items():
    print(
        f"{key}: {value}"
    )
