from pathlib import Path
import json

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm


ROOT = Path("datasets/raw/IDRiD")

SEG = ROOT / "A. Segmentation"

IMAGE_ROOT = SEG / "1. Original Images"

MASK_ROOT = SEG / "2. All Segmentation Groundtruths"

OUTPUT = Path("datasets/metadata/IDRiD")
OUTPUT.mkdir(parents=True, exist_ok=True)


TILE_SIZE = 512
STRIDE = 256


LESIONS = {
    "MA": "1. Microaneurysms",
    "HE": "2. Haemorrhages",
    "EX": "3. Hard Exudates",
    "SE": "4. Soft Exudates",
}


def image_files(folder):
    valid = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in valid
    )


def find_mask(mask_folder, image_id, lesion_code):

    candidates = list(
        mask_folder.glob(
            f"{image_id}_{lesion_code}.*"
        )
    )

    if len(candidates) == 0:
        return None

    return candidates[0]


def tile_positions(length, tile_size, stride):

    if length <= tile_size:
        return [0]

    positions = list(
        range(
            0,
            length - tile_size + 1,
            stride
        )
    )

    final_position = length - tile_size

    if positions[-1] != final_position:
        positions.append(final_position)

    return positions


def load_binary_mask(path, height, width):

    if path is None:
        return np.zeros(
            (height, width),
            dtype=np.uint8
        )

    mask = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        return np.zeros(
            (height, width),
            dtype=np.uint8
        )

    if mask.shape != (height, width):
        mask = cv2.resize(
            mask,
            (width, height),
            interpolation=cv2.INTER_NEAREST
        )

    return (mask > 0).astype(np.uint8)


def process_split(split_name):

    if split_name == "train":
        image_folder = (
            IMAGE_ROOT /
            "a. Training Set"
        )

        gt_folder = (
            MASK_ROOT /
            "a. Training Set"
        )

    else:

        image_folder = (
            IMAGE_ROOT /
            "b. Testing Set"
        )

        gt_folder = (
            MASK_ROOT /
            "b. Testing Set"
        )

    images = image_files(image_folder)

    records = []

    for image_path in tqdm(
        images,
        desc=f"Building {split_name} manifest"
    ):

        image_id = image_path.stem

        image = cv2.imread(str(image_path))

        if image is None:
            print(
                "[WARNING] Could not read:",
                image_path
            )
            continue

        height, width = image.shape[:2]

        masks = {}

        mask_paths = {}

        for code, folder in LESIONS.items():

            mask_path = find_mask(
                gt_folder / folder,
                image_id,
                code
            )

            mask_paths[code] = (
                str(mask_path)
                if mask_path
                else None
            )

            masks[code] = load_binary_mask(
                mask_path,
                height,
                width
            )

        xs = tile_positions(
            width,
            TILE_SIZE,
            STRIDE
        )

        ys = tile_positions(
            height,
            TILE_SIZE,
            STRIDE
        )

        for y in ys:
            for x in xs:

                x2 = x + TILE_SIZE
                y2 = y + TILE_SIZE

                lesion_pixels = {}

                positive_lesions = []

                for code in LESIONS:

                    crop = masks[code][
                        y:y2,
                        x:x2
                    ]

                    count = int(crop.sum())

                    lesion_pixels[code] = count

                    if count > 0:
                        positive_lesions.append(code)

                is_positive = (
                    len(positive_lesions) > 0
                )

                tile_id = (
                    f"{image_id}"
                    f"_x{x}_y{y}"
                )

                records.append({

                    "dataset": "IDRiD",

                    "split": split_name,

                    "image_id": image_id,

                    "tile_id": tile_id,

                    "image_path": str(
                        image_path.as_posix()
                    ),

                    "original_width": width,
                    "original_height": height,

                    "tile_width": TILE_SIZE,
                    "tile_height": TILE_SIZE,

                    "x_start": x,
                    "y_start": y,

                    "x_end": x2,
                    "y_end": y2,

                    "ma_mask_path":
                        mask_paths["MA"],

                    "he_mask_path":
                        mask_paths["HE"],

                    "ex_mask_path":
                        mask_paths["EX"],

                    "se_mask_path":
                        mask_paths["SE"],

                    "ma_pixels":
                        lesion_pixels["MA"],

                    "he_pixels":
                        lesion_pixels["HE"],

                    "ex_pixels":
                        lesion_pixels["EX"],

                    "se_pixels":
                        lesion_pixels["SE"],

                    "has_lesion":
                        int(is_positive),

                    "lesion_types":
                        ",".join(
                            positive_lesions
                        ),
                })

    return records


def main():

    train_records = process_split(
        "train"
    )

    test_records = process_split(
        "test"
    )

    records = (
        train_records +
        test_records
    )

    df = pd.DataFrame(records)

    csv_file = (
        OUTPUT /
        "tile_manifest.csv"
    )

    json_file = (
        OUTPUT /
        "tile_manifest.json"
    )

    df.to_csv(
        csv_file,
        index=False
    )

    with open(
        json_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            records,
            f,
            indent=2
        )

    print("\n=== TILE MANIFEST ===")

    print("Total tiles :", len(df))

    print(
        "Train tiles :",
        (df["split"] == "train").sum()
    )

    print(
        "Test tiles  :",
        (df["split"] == "test").sum()
    )

    print(
        "Positive tiles:",
        df["has_lesion"].sum()
    )

    print(
        "Background tiles:",
        (df["has_lesion"] == 0).sum()
    )

    print("\nPositive lesion pixels:")

    for code in LESIONS:

        column = f"{code.lower()}_pixels"

        print(
            code,
            int(
                (df[column] > 0).sum()
            ),
            "tiles"
        )

    print("\nSaved:")
    print(csv_file)
    print(json_file)


if __name__ == "__main__":
    main()