from pathlib import Path
import random
import pandas as pd


MANIFEST = Path("datasets/metadata/IDRiD/tile_manifest.csv")
OUTPUT = Path("datasets/metadata/IDRiD/tile_manifest_split.csv")

SEED = 42
VAL_FRACTION = 0.20


def main():
    df = pd.read_csv(MANIFEST)

    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()

    image_ids = sorted(train_df["image_id"].unique())

    print("Official training images:", len(image_ids))

    # Determine lesion presence at image level
    image_stats = (
        train_df.groupby("image_id")[
            ["ma_pixels", "he_pixels", "ex_pixels", "se_pixels"]
        ]
        .sum()
    )

    for c in image_stats.columns:
        image_stats[c] = (image_stats[c] > 0).astype(int)

    rng = random.Random(SEED)

    n_val = max(1, round(len(image_ids) * VAL_FRACTION))

    # Find a reproducible split that has examples of every lesion
    # in both train and validation.
    selected_val = None

    for attempt in range(1000):
        shuffled = image_ids.copy()
        rng.shuffle(shuffled)

        val_ids = set(shuffled[:n_val])
        tr_ids = set(shuffled[n_val:])

        val_stats = image_stats.loc[list(val_ids)].sum()
        tr_stats = image_stats.loc[list(tr_ids)].sum()

        if (val_stats > 0).all() and (tr_stats > 0).all():
            selected_val = val_ids
            break

    if selected_val is None:
        raise RuntimeError(
            "Could not create a train/val split containing all lesion classes."
        )

    train_ids = set(image_ids) - selected_val

    train_df["cv_split"] = train_df["image_id"].apply(
        lambda x: "val" if x in selected_val else "train"
    )

    # Keep official IDRiD test images completely untouched.
    test_df["cv_split"] = "test"

    out = pd.concat([train_df, test_df], ignore_index=True)

    out.to_csv(OUTPUT, index=False)

    print("\n=== IDRiD IMAGE-LEVEL SPLIT ===")
    print("Train images:", len(train_ids))
    print("Val images  :", len(selected_val))
    print("Test images :", test_df["image_id"].nunique())

    print("\nTile counts:")
    print(out["cv_split"].value_counts())

    print("\nValidation image lesion coverage:")
    print(image_stats.loc[list(selected_val)].sum())

    print("\nSaved:")
    print(OUTPUT)


if __name__ == "__main__":
    main()