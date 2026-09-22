from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sih_dr.data.aptos_dataset import (
    APTOSDataset,
    get_eval_transform,
)

ONNX_PATH = ROOT / "nationals" / "exports" / "global_effnetb0.onnx"

REFERENCE_PATH = (
    ROOT
    / "nationals"
    / "validation"
    / "effnet_onnx_reference.json"
)

CSV = ROOT / "datasets" / "raw" / "APTOS2019" / "train.csv"

IMAGE_DIR = (
    ROOT
    / "datasets"
    / "raw"
    / "APTOS2019"
    / "train_images"
)

TEST_ID = "000c1434d8d7"


def softmax(x):
    x = x - np.max(x, axis=1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=1, keepdims=True)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def main():

    reference = json.loads(
        REFERENCE_PATH.read_text(encoding="utf-8")
    )

    image_size = int(reference["image_size"])

    df = pd.read_csv(CSV)

    id_column = next(
        col
        for col in ["id_code", "image", "image_id", "id"]
        if col in df.columns
    )

    target_df = df[
        df[id_column].astype(str) == TEST_ID
    ].copy()

    dataset = APTOSDataset(
        target_df,
        IMAGE_DIR,
        transform=get_eval_transform(image_size),
    )

    x = (
        dataset[0]["image"]
        .unsqueeze(0)
        .numpy()
        .astype(np.float32)
    )

    print("\n=== ONNX MODEL ===")
    print(ONNX_PATH)

    session = ort.InferenceSession(
        str(ONNX_PATH),
        providers=["CPUExecutionProvider"],
    )

    print("\nINPUTS:")
    for inp in session.get_inputs():
        print(inp.name, inp.shape, inp.type)

    print("\nOUTPUTS:")
    for out in session.get_outputs():
        print(out.name, out.shape, out.type)

    outputs = session.run(
        None,
        {"fundus_image": x},
    )

    grade_logits = outputs[0]
    rdr_logits = outputs[1]

    grade_probs = softmax(grade_logits)[0]

    rdr_probability = float(
        sigmoid(rdr_logits).reshape(-1)[0]
    )

    grade = int(np.argmax(grade_probs))

    pytorch_probs = np.asarray(
        reference["grade_probabilities"],
        dtype=np.float32,
    )

    grade_error = np.abs(
        pytorch_probs - grade_probs
    )

    max_grade_error = float(
        grade_error.max()
    )

    rdr_error = abs(
        float(reference["rdr_probability"])
        - rdr_probability
    )

    print("\n=== PYTORCH vs ONNX ===")

    print("\nPyTorch grade:")
    print(reference["grade"])

    print("\nONNX grade:")
    print(grade)

    print("\nPyTorch probabilities:")
    print(pytorch_probs)

    print("\nONNX probabilities:")
    print(grade_probs)

    print("\nAbsolute probability errors:")
    print(grade_error)

    print("\nMaximum grade probability error:")
    print(max_grade_error)

    print("\nPyTorch RDR:")
    print(reference["rdr_probability"])

    print("\nONNX RDR:")
    print(rdr_probability)

    print("\nRDR absolute error:")
    print(rdr_error)

    grade_match = (
        grade == int(reference["grade"])
    )

    parity = (
        max_grade_error < 1e-4
        and rdr_error < 1e-4
    )

    print("\nGRADE MATCH:", grade_match)
    print("NUMERICAL PARITY:", parity)

    if not grade_match or not parity:
        raise SystemExit(
            "\nPARITY FAILED"
        )

    print("\n==============================")
    print("ONNX PARITY PASSED")
    print("==============================")


if __name__ == "__main__":
    main()
