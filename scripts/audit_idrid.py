from pathlib import Path
from collections import Counter

ROOT = Path("datasets/raw/IDRiD")

SEG = ROOT / "A. Segmentation"

TRAIN_IMAGES = (
    SEG
    / "1. Original Images"
    / "a. Training Set"
)

TEST_IMAGES = (
    SEG
    / "1. Original Images"
    / "b. Testing Set"
)

TRAIN_GT = (
    SEG
    / "2. All Segmentation Groundtruths"
    / "a. Training Set"
)

TEST_GT = (
    SEG
    / "2. All Segmentation Groundtruths"
    / "b. Testing Set"
)

LESIONS = {
    "MA": "1. Microaneurysms",
    "HE": "2. Haemorrhages",
    "EX": "3. Hard Exudates",
    "SE": "4. Soft Exudates",
    "OD": "5. Optic Disc",
}


def list_images(folder):
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )


def main():

    print("\n=== IDRiD AUDIT ===\n")

    train_images = list_images(TRAIN_IMAGES)
    test_images = list_images(TEST_IMAGES)

    print("Training fundus images :", len(train_images))
    print("Testing fundus images  :", len(test_images))

    print("\nTraining image examples:")
    for p in train_images[:5]:
        print(" ", p.name)

    print("\nMask counts:")

    for code, folder_name in LESIONS.items():

        train_folder = TRAIN_GT / folder_name
        test_folder = TEST_GT / folder_name

        train_masks = list_images(train_folder)
        test_masks = list_images(test_folder)

        print(
            f"{code:>2} | "
            f"train={len(train_masks):3d} "
            f"test={len(test_masks):3d}"
        )

        if train_masks:
            print("   example:", train_masks[0].name)

    print("\nDataset root OK.")


if __name__ == "__main__":
    main()