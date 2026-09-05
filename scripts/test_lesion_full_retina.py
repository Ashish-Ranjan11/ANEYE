from pathlib import Path

import cv2

from sih_dr.lesions.inference import (
    LesionInferenceEngine,
    create_lesion_overlay,
    draw_lesion_contours,
)


CHECKPOINT = (
    "checkpoints/sih_dr/lesions/"
    "lesion_final.pth"
)

IMAGE = (
    "datasets/raw/APTOS2019/"
    "train_images/000c1434d8d7.png"
)

OUTPUT_DIR = Path(
    "results/sih_dr/inference"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def main():

    image = cv2.imread(
        IMAGE
    )

    if image is None:
        raise RuntimeError(
            f"Cannot load {IMAGE}"
        )

    engine = LesionInferenceEngine(
        CHECKPOINT
    )

    result = engine.predict(
        image
    )

    print("\n=== LESION EVIDENCE ===")

    for lesion, info in (
        result["evidence"].items()
    ):

        print(
            f"\n{lesion}"
        )

        print(
            " Count:",
            info["count"]
        )

        print(
            " Area:",
            info["area_px"]
        )

        print(
            " Mean confidence:",
            info[
                "mean_confidence"
            ]
        )

        print(
            " Evidence:",
            info["evidence"]
        )

    overlay = create_lesion_overlay(
        image,
        result["masks"]
    )

    contours = draw_lesion_contours(
        image,
        result["masks"]
    )

    cv2.imwrite(
        str(
            OUTPUT_DIR
            / "lesion_overlay.png"
        ),
        overlay
    )

    cv2.imwrite(
        str(
            OUTPUT_DIR
            / "lesion_contours.png"
        ),
        contours
    )

    # Save every class separately
    for i, name in enumerate(
        ["MA", "HE", "EX", "SE"]
    ):

        mask = (
            result["masks"][i]
            * 255
        )

        cv2.imwrite(
            str(
                OUTPUT_DIR
                / f"{name}_mask.png"
            ),
            mask
        )

    print(
        "\nSaved outputs to:",
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()