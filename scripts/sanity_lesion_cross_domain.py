from pathlib import Path
import cv2

from sih_dr.lesions.inference import (
    LesionInferenceEngine,
    create_lesion_overlay,
)

BASE = Path("datasets/raw/APTOS2019/train_images")

CASES = {
    "grade0": "002c21358ce6.png",
    "grade1": "0024cdab0c1e.png",
    "grade2": "000c1434d8d7.png",
}

OUT = Path("results/sih_dr/sanity")
OUT.mkdir(parents=True, exist_ok=True)

engine = LesionInferenceEngine(
    "checkpoints/sih_dr/lesions/lesion_final.pth"
)

for label, filename in CASES.items():

    image = cv2.imread(str(BASE / filename))

    print(f"\n===== {label.upper()} =====")

    result = engine.predict(image)

    for lesion, info in result["evidence"].items():
        print(
            lesion,
            "count=", info["count"],
            "area=", info["area_px"],
            "conf=", info["mean_confidence"],
        )

    overlay = create_lesion_overlay(
        image,
        result["masks"]
    )

    cv2.imwrite(
        str(OUT / f"{label}_overlay.png"),
        overlay
    )

print("\nSaved:", OUT)