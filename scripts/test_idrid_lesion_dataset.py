from sih_dr.data.idrid_lesion_dataset import (
    IDRiDLesionDataset,
    get_train_transform,
)


MANIFEST = (
    "datasets/metadata/IDRiD/"
    "tile_manifest_cached.csv"
)


def main():

    ds = IDRiDLesionDataset(
        MANIFEST,
        split="train",
        transform=get_train_transform(),
    )

    print("Dataset length:", len(ds))

    sample = ds[0]

    image = sample["image"]
    mask = sample["mask"]

    print("Image shape:", image.shape)
    print("Mask shape :", mask.shape)
    print("Image dtype:", image.dtype)
    print("Mask dtype :", mask.dtype)

    print(
        "Mask pixels:",
        mask.sum(dim=(1, 2))
    )

    print(
        "Metadata:",
        sample["metadata"]
    )

    assert image.shape == (3, 512, 512)
    assert mask.shape == (4, 512, 512)

    print("\nIDRiD LESION DATASET OK")


if __name__ == "__main__":
    main()
