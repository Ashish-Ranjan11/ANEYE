from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm


MANIFEST = Path(
    "datasets/metadata/IDRiD/tile_manifest_split.csv"
)

CACHE_ROOT = Path(
    "datasets/tiles/IDRiD"
)

LESIONS = {
    "MA": "ma_mask_path",
    "HE": "he_mask_path",
    "EX": "ex_mask_path",
    "SE": "se_mask_path",
}


def read_mask(path, h, w):

    if pd.isna(path) or not str(path).strip():
        return np.zeros((h, w), dtype=np.uint8)

    mask = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE,
    )

    if mask is None:
        return np.zeros((h, w), dtype=np.uint8)

    if mask.shape != (h, w):
        mask = cv2.resize(
            mask,
            (w, h),
            interpolation=cv2.INTER_NEAREST,
        )

    return (mask > 0).astype(np.uint8)


def main():

    df = pd.read_csv(MANIFEST)

    for split in ["train", "val", "test"]:

        (CACHE_ROOT / split / "images").mkdir(
            parents=True,
            exist_ok=True,
        )

        (CACHE_ROOT / split / "masks").mkdir(
            parents=True,
            exist_ok=True,
        )

    # Group by retina so each full-resolution image and mask
    # is loaded only once.
    grouped = df.groupby("image_id")

    records = []

    for image_id, group in tqdm(
        grouped,
        desc="Caching IDRiD retina tiles",
    ):

        first = group.iloc[0]

        image = cv2.imread(
            str(first["image_path"])
        )

        if image is None:
            raise RuntimeError(
                f"Could not read {first['image_path']}"
            )

        h, w = image.shape[:2]

        masks = {}

        for code, column in LESIONS.items():

            masks[code] = read_mask(
                first[column],
                h,
                w,
            )

        for _, row in group.iterrows():

            split = str(row["cv_split"])

            x1 = int(row["x_start"])
            y1 = int(row["y_start"])
            x2 = int(row["x_end"])
            y2 = int(row["y_end"])

            tile_id = str(row["tile_id"])

            image_tile = image[
                y1:y2,
                x1:x2
            ]

            mask_tile = np.stack(
                [
                    masks["MA"][y1:y2, x1:x2],
                    masks["HE"][y1:y2, x1:x2],
                    masks["EX"][y1:y2, x1:x2],
                    masks["SE"][y1:y2, x1:x2],
                ],
                axis=0,
            ).astype(np.uint8)

            image_path = (
                CACHE_ROOT
                / split
                / "images"
                / f"{tile_id}.jpg"
            )

            mask_path = (
                CACHE_ROOT
                / split
                / "masks"
                / f"{tile_id}.npz"
            )

            cv2.imwrite(
                str(image_path),
                image_tile,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    95,
                ],
            )

            np.savez_compressed(
                mask_path,
                mask=mask_tile,
            )

            rec = row.to_dict()

            rec["cached_image_path"] = (
                image_path.as_posix()
            )

            rec["cached_mask_path"] = (
                mask_path.as_posix()
            )

            records.append(rec)

    out = pd.DataFrame(records)

    out_path = (
        "datasets/metadata/IDRiD/"
        "tile_manifest_cached.csv"
    )

    out.to_csv(
        out_path,
        index=False,
    )

    print("\n=== CACHE COMPLETE ===")
    print("Tiles:", len(out))
    print(out["cv_split"].value_counts())
    print("\nSaved manifest:")
    print(out_path)


if __name__ == "__main__":
    main()