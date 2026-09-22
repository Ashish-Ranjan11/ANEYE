from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sih_dr.grading.model import GlobalDRModel
from sih_dr.data.aptos_dataset import APTOSDataset, get_eval_transform


CHECKPOINT = ROOT / "checkpoints" / "sih_dr" / "grading" / "global_final.pth"

CSV = ROOT / "datasets" / "raw" / "APTOS2019" / "train.csv"

IMAGE_DIR = ROOT / "datasets" / "raw" / "APTOS2019" / "train_images"

EXPORT_DIR = ROOT / "nationals" / "exports"
VALIDATION_DIR = ROOT / "nationals" / "validation"

ONNX_PATH = EXPORT_DIR / "global_effnetb0.onnx"
RESULT_PATH = VALIDATION_DIR / "effnet_onnx_reference.json"

TEST_ID = "000c1434d8d7"


class ONNXWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        out = self.model(x)

        grade_logits = out["grade_logits"]
        rdr_logits = out["rdr_logits"]

        # Force RDR output into a consistent [N,1] form
        if rdr_logits.ndim == 1:
            rdr_logits = rdr_logits.unsqueeze(1)

        return grade_logits, rdr_logits


def main():

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== NETRAAI GLOBAL MODEL EXPORT ===")

    print("\nCheckpoint:")
    print(CHECKPOINT)

    ckpt = torch.load(
        CHECKPOINT,
        map_location="cpu",
        weights_only=False,
    )

    print("\nCheckpoint metadata")
    print("-------------------")

    for key in [
        "epoch",
        "selection_score",
        "metrics",
        "image_size",
        "backbone",
        "labels",
        "rdr_definition",
    ]:
        if key in ckpt:
            print(f"{key}: {ckpt[key]}")

    image_size = int(
        ckpt.get(
            "image_size",
            384,
        )
    )

    backbone = ckpt.get(
        "backbone",
        "efficientnet_b0",
    )

    print("\nReconstructing model:")
    print("Backbone:", backbone)
    print("Input:", image_size, "x", image_size)

    model = GlobalDRModel(
        backbone=backbone,
        pretrained=False,
    )

    model.load_state_dict(
        ckpt["model_state_dict"],
        strict=True,
    )

    model.eval()

    print("Checkpoint loaded STRICTLY: OK")

    # --------------------------------------------------
    # BUILD EXACT TEST SAMPLE USING EXISTING DATA PIPELINE
    # --------------------------------------------------

    df = pd.read_csv(CSV)

    id_column = None

    for candidate in [
        "id_code",
        "image",
        "image_id",
        "id",
    ]:
        if candidate in df.columns:
            id_column = candidate
            break

    if id_column is None:
        raise RuntimeError(
            f"Could not identify image ID column. Columns: {list(df.columns)}"
        )

    target_df = df[
        df[id_column].astype(str)
        == TEST_ID
    ].copy()

    if len(target_df) != 1:
        raise RuntimeError(
            f"Expected exactly one row for {TEST_ID}, found {len(target_df)}"
        )

    dataset = APTOSDataset(
        target_df,
        IMAGE_DIR,
        transform=get_eval_transform(
            image_size
        ),
    )

    sample = dataset[0]

    x = sample["image"].unsqueeze(0)

    print("\nInput tensor:")
    print("Shape:", tuple(x.shape))
    print("dtype:", x.dtype)
    print("min:", float(x.min()))
    print("max:", float(x.max()))

    # --------------------------------------------------
    # PYTORCH REFERENCE
    # --------------------------------------------------

    with torch.no_grad():

        output = model(x)

        grade_logits = output["grade_logits"]

        rdr_logits = output["rdr_logits"]

        grade_probs = torch.softmax(
            grade_logits,
            dim=1,
        )

        rdr_prob = torch.sigmoid(
            rdr_logits
        )

        grade = int(
            grade_probs.argmax(
                dim=1
            ).item()
        )

        confidence = float(
            grade_probs.max(
                dim=1
            ).values.item()
        )

        rdr_probability = float(
            rdr_prob.reshape(-1)[0].item()
        )

    print("\n=== PYTORCH REFERENCE ===")

    print("Test image:", TEST_ID)
    print("Predicted grade:", grade)
    print("Grade confidence:", confidence)

    print(
        "Grade probabilities:",
        grade_probs.squeeze(0).tolist(),
    )

    print(
        "RDR probability:",
        rdr_probability,
    )

    print(
        "Referable:",
        rdr_probability >= 0.5,
    )

    # --------------------------------------------------
    # EXPORT
    # --------------------------------------------------

    wrapper = ONNXWrapper(
        model
    ).eval()

    print("\nExporting ONNX...")

    torch.onnx.export(
        wrapper,
        x,
        str(ONNX_PATH),

        input_names=[
            "fundus_image"
        ],

        output_names=[
            "grade_logits",
            "rdr_logits",
        ],

        dynamic_axes={
            "fundus_image": {
                0: "batch"
            },

            "grade_logits": {
                0: "batch"
            },

            "rdr_logits": {
                0: "batch"
            },
        },

        opset_version=17,

        do_constant_folding=True,
    )

    print("ONNX SAVED:")
    print(ONNX_PATH)

    result = {
        "model": "EfficientNet-B0",
        "checkpoint": str(CHECKPOINT),
        "test_image": TEST_ID,
        "image_size": image_size,

        "grade": grade,

        "grade_confidence":
            confidence,

        "grade_probabilities":
            grade_probs.squeeze(0).tolist(),

        "rdr_probability":
            rdr_probability,

        "referable_dr":
            bool(
                rdr_probability >= 0.5
            ),
    }

    RESULT_PATH.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nReference JSON:")
    print(RESULT_PATH)

    print("\n=== EXPORT COMPLETE ===")


if __name__ == "__main__":
    main()
