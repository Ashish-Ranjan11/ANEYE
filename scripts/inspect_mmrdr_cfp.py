from pathlib import Path
import ast
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DATA_ROOT = Path(
    r"D:\ANEYE_DATASETS\MMRDR\CFP\MMRDR-CFP"
)

CSV_PATH = DATA_ROOT / "FP.csv"

OUTPUT_DIR = (
    ROOT
    / "nationals"
    / "advanced"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


LESION_NAMES = [
    "MA",
    "HE",
    "IH",
    "VB_IRMA",
    "NV",
    "VH",
    "RD",
]


print("\n======================================")
print("MMRDR CFP DATASET AUDIT")
print("======================================\n")


df = pd.read_csv(
    CSV_PATH
)


print("Rows:", len(df))
print("Columns:", list(df.columns))


# ------------------------------------------------------------
# PARSE LESION VECTOR
# ------------------------------------------------------------

parsed = []

bad_rows = []


for index, value in enumerate(
    df["lesion"]
):

    try:

        vector = ast.literal_eval(
            str(value)
        )

        vector = [
            int(x)
            for x in vector
        ]

        if (
            len(vector) != 7
            or any(
                x not in (0, 1)
                for x in vector
            )
        ):

            raise ValueError(
                f"Invalid lesion vector: {vector}"
            )

        parsed.append(
            vector
        )

    except Exception as exc:

        bad_rows.append({
            "row":
                index,

            "value":
                value,

            "error":
                str(exc),
        })

        parsed.append(
            [0] * 7
        )


if bad_rows:

    print(
        "\nBAD LESION ROWS:",
        len(bad_rows)
    )

    for row in bad_rows[:10]:
        print(row)

    sys.exit(
        "STOP: lesion parsing failed."
    )


lesion_df = pd.DataFrame(
    parsed,
    columns=LESION_NAMES,
)


for column in LESION_NAMES:

    df[
        column
    ] = lesion_df[
        column
    ]


# ------------------------------------------------------------
# RESOLVE IMAGE PATHS
# ------------------------------------------------------------

df[
    "full_path"
] = df[
    "image"
].apply(
    lambda x:
        str(
            DATA_ROOT
            /
            Path(
                str(x).replace(
                    "/",
                    "\\"
                )
            )
        )
)


df[
    "exists"
] = df[
    "full_path"
].apply(
    lambda p:
        Path(p).exists()
)


missing = df[
    ~df[
        "exists"
    ]
]


# ------------------------------------------------------------
# INFER PROVIDED SPLIT FROM IMAGE NAME
# ------------------------------------------------------------

def infer_split(
    image_path
):

    name = Path(
        str(image_path)
    ).name.lower()

    if name.startswith(
        "tr"
    ):
        return "train"

    if name.startswith(
        "te"
    ):
        return "test"

    return "unknown"


df[
    "split"
] = df[
    "image"
].apply(
    infer_split
)


# ------------------------------------------------------------
# BASIC CHECKS
# ------------------------------------------------------------

print(
    "\n=== IMAGE INTEGRITY ==="
)

print(
    "Images existing:",
    int(
        df[
            "exists"
        ].sum()
    )
)

print(
    "Missing images:",
    len(
        missing
    )
)

print(
    "Duplicate image paths:",
    int(
        df[
            "image"
        ].duplicated().sum()
    )
)


print(
    "\n=== SPLIT COUNTS ==="
)

print(
    df[
        "split"
    ].value_counts(
        dropna=False
    )
)


print(
    "\n=== GRADE COUNTS ==="
)

print(
    df[
        "grade"
    ].value_counts()
    .sort_index()
)


print(
    "\n=== LEFT / RIGHT COUNTS ==="
)

print(
    df[
        "lr"
    ].value_counts(
        dropna=False
    )
)


# ------------------------------------------------------------
# LESION POSITIVES
# ------------------------------------------------------------

print(
    "\n=== LESION POSITIVE COUNTS ==="
)


for lesion in LESION_NAMES:

    count = int(
        df[
            lesion
        ].sum()
    )

    prevalence = (
        count
        /
        len(df)
        *
        100.0
    )

    print(
        f"{lesion:8s}: "
        f"{count:5d} "
        f"({prevalence:6.2f}%)"
    )


# ------------------------------------------------------------
# PER-SPLIT LESION COUNTS
# ------------------------------------------------------------

print(
    "\n=== LESION COUNTS BY SPLIT ==="
)


for split_name in (
    "train",
    "test",
    "unknown",
):

    subset = df[
        df[
            "split"
        ]
        ==
        split_name
    ]

    if len(
        subset
    ) == 0:
        continue

    print(
        f"\n[{split_name.upper()}]"
    )

    print(
        "Cases:",
        len(
            subset
        )
    )

    for lesion in LESION_NAMES:

        count = int(
            subset[
                lesion
            ].sum()
        )

        print(
            f"{lesion:8s}: {count}"
        )


# ------------------------------------------------------------
# ADVANCED EVIDENCE COUNTS
# ------------------------------------------------------------

df[
    "advanced_positive"
] = (
    (
        df[
            "VB_IRMA"
        ]
        |
        df[
            "NV"
        ]
        |
        df[
            "VH"
        ]
    )
    .astype(
        int
    )
)


print(
    "\n=== ADVANCED EVIDENCE ==="
)

print(
    "VB/IRMA positive:",
    int(
        df[
            "VB_IRMA"
        ].sum()
    )
)

print(
    "NV positive:",
    int(
        df[
            "NV"
        ].sum()
    )
)

print(
    "VH positive:",
    int(
        df[
            "VH"
        ].sum()
    )
)

print(
    "Any advanced evidence:",
    int(
        df[
            "advanced_positive"
        ].sum()
    )
)


# ------------------------------------------------------------
# SAVE TRAINING MANIFEST
# ------------------------------------------------------------

manifest_columns = [
    "type",
    "image",
    "full_path",
    "split",
    "grade",
    "lr",
    "MA",
    "HE",
    "IH",
    "VB_IRMA",
    "NV",
    "VH",
    "RD",
    "advanced_positive",
]


manifest = df[
    manifest_columns
].copy()


manifest_path = (
    OUTPUT_DIR
    /
    "mmrdr_cfp_manifest.csv"
)


manifest.to_csv(
    manifest_path,
    index=False,
)


print(
    "\nManifest saved:"
)

print(
    manifest_path
)


print(
    "\n======================================"
)

print(
    "MMRDR CFP AUDIT COMPLETE"
)

print(
    "======================================"
)
