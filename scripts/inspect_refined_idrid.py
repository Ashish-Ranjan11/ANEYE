from pathlib import Path
from collections import Counter

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

DATASET = (
    ROOT
    / "datasets"
    / "raw"
    / "RefinedIDRiD"
)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}


files = [
    p
    for p in DATASET.rglob("*")
    if p.is_file()
    and p.suffix.lower() in IMAGE_EXTENSIONS
]


print("\n=== REFINED IDRiD INVENTORY ===")
print("Image/mask files:", len(files))


print("\nFIRST 100 FILES")
print("----------------")

for p in files[:100]:
    print(
        p.relative_to(DATASET)
    )


print("\n=== POSSIBLE MASKS ===")

mask_candidates = []

for p in files:

    name = p.name.lower()

    if (
        "mask" in name
        or "label" in name
        or "gt" in name
        or "ground" in name
        or p.suffix.lower() in {
            ".png",
            ".tif",
            ".tiff",
        }
    ):

        img = cv2.imread(
            str(p),
            cv2.IMREAD_UNCHANGED,
        )

        if img is None:
            continue

        # Unified segmentation masks should
        # usually be single-channel.
        if img.ndim != 2:
            continue

        values = np.unique(
            img
        )

        # We are especially interested in masks
        # containing documented class IDs.
        documented = {
            0,
            4,
            8,
            16,
            24,
            32,
            63,
            96,
            127,
            166,
            191,
            255,
        }

        intersection = (
            set(
                int(v)
                for v in values
            )
            &
            documented
        )

        if intersection:

            mask_candidates.append(
                (
                    p,
                    values
                )
            )


print(
    "Candidate masks:",
    len(mask_candidates)
)


nv_masks = []

pixel_counter = Counter()


for p, values in mask_candidates:

    img = cv2.imread(
        str(p),
        cv2.IMREAD_UNCHANGED,
    )

    unique, counts = np.unique(
        img,
        return_counts=True,
    )

    for value, count in zip(
        unique,
        counts
    ):

        pixel_counter[
            int(value)
        ] += int(count)

    if np.any(
        img == 166
    ):

        nv_pixels = int(
            np.count_nonzero(
                img == 166
            )
        )

        nv_masks.append(
            (
                p,
                nv_pixels
            )
        )


print("\n=== GLOBAL LABEL COUNTS ===")

for value in sorted(
    pixel_counter
):

    print(
        f"{value:3d}: "
        f"{pixel_counter[value]:,} pixels"
    )


print("\n=== NV POSITIVE MASKS ===")

print(
    "Images containing label 166:",
    len(nv_masks)
)


for p, count in nv_masks:

    print(
        p.relative_to(DATASET),
        "| NV pixels:",
        count
    )


print("\n=== FINISHED ===")
