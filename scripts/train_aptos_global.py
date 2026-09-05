from pathlib import Path
import time
import random

import numpy as np
import pandas as pd

import torch
import torch.nn as nn

from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    cohen_kappa_score,
    confusion_matrix,
    roc_auc_score,
)

from sih_dr.data.aptos_dataset import (
    APTOSDataset,
    get_train_transform,
    get_eval_transform,
)

from sih_dr.grading.model import (
    GlobalDRModel,
)


CSV = Path(
    "datasets/raw/APTOS2019/train.csv"
)

IMAGE_DIR = Path(
    "datasets/raw/APTOS2019/train_images"
)

CHECKPOINT = Path(
    "checkpoints/sih_dr/grading/"
    "aptos_global_best.pth"
)

HISTORY = Path(
    "results/sih_dr/grading/"
    "aptos_training_history.csv"
)

SPLIT_FILE = Path(
    "datasets/metadata/"
    "APTOS2019_split.csv"
)


IMAGE_SIZE = 384
BATCH_SIZE = 8

EPOCHS = 10
PATIENCE = 3

LR = 2e-4
WEIGHT_DECAY = 1e-4

NUM_WORKERS = 2
SEED = 42

RDR_LOSS_WEIGHT = 0.50


def seed_everything(seed):

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_split():

    df = pd.read_csv(CSV)

    train_df, val_df = train_test_split(
        df,
        test_size=0.20,
        random_state=SEED,
        stratify=df["diagnosis"],
    )

    train_df = train_df.copy()
    val_df = val_df.copy()

    train_df["split"] = "train"
    val_df["split"] = "val"

    combined = pd.concat(
        [train_df, val_df],
        ignore_index=True,
    )

    SPLIT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    combined.to_csv(
        SPLIT_FILE,
        index=False,
    )

    return train_df, val_df


def class_weights(train_df):

    counts = (
        train_df["diagnosis"]
        .value_counts()
        .sort_index()
        .values
    )

    weights = (
        len(train_df)
        / (5.0 * counts)
    )

    return torch.tensor(
        weights,
        dtype=torch.float32
    )


def calculate_rdr_metrics(
    y_true,
    probs,
    threshold=0.5,
):

    preds = (
        np.array(probs) >= threshold
    ).astype(int)

    y_true = np.array(y_true)

    tn, fp, fn, tp = (
        confusion_matrix(
            y_true,
            preds,
            labels=[0, 1],
        )
        .ravel()
    )

    sensitivity = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0
    )

    try:
        auc = roc_auc_score(
            y_true,
            probs
        )
    except Exception:
        auc = 0

    return (
        sensitivity,
        specificity,
        auc,
    )


def train_epoch(
    model,
    loader,
    optimizer,
    grade_loss_fn,
    rdr_loss_fn,
    scaler,
    device,
):

    model.train()

    total_loss = 0

    for batch in loader:

        images = batch["image"].to(
            device,
            non_blocking=True,
        )

        grades = batch["grade"].to(
            device,
            non_blocking=True,
        )

        rdr = batch["rdr"].to(
            device,
            non_blocking=True,
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=(
                device.type == "cuda"
            ),
        ):

            out = model(images)

            grade_loss = grade_loss_fn(
                out["grade_logits"],
                grades,
            )

            rdr_loss = rdr_loss_fn(
                out["rdr_logits"],
                rdr,
            )

            loss = (
                grade_loss
                +
                RDR_LOSS_WEIGHT
                * rdr_loss
            )

        scaler.scale(
            loss
        ).backward()

        scaler.unscale_(
            optimizer
        )

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            5.0,
        )

        scaler.step(
            optimizer
        )

        scaler.update()

        total_loss += (
            loss.item()
            * images.size(0)
        )

    return (
        total_loss
        / len(loader.dataset)
    )


@torch.no_grad()
def validate(
    model,
    loader,
    grade_loss_fn,
    rdr_loss_fn,
    device,
):

    model.eval()

    total_loss = 0

    all_grade_true = []
    all_grade_pred = []

    all_rdr_true = []
    all_rdr_prob = []

    for batch in loader:

        images = batch["image"].to(
            device,
            non_blocking=True,
        )

        grades = batch["grade"].to(
            device,
            non_blocking=True,
        )

        rdr = batch["rdr"].to(
            device,
            non_blocking=True,
        )

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=(
                device.type == "cuda"
            ),
        ):

            out = model(images)

            grade_loss = grade_loss_fn(
                out["grade_logits"],
                grades,
            )

            rdr_loss = rdr_loss_fn(
                out["rdr_logits"],
                rdr,
            )

            loss = (
                grade_loss
                +
                RDR_LOSS_WEIGHT
                * rdr_loss
            )

        total_loss += (
            loss.item()
            * images.size(0)
        )

        grade_pred = (
            out["grade_logits"]
            .argmax(dim=1)
        )

        rdr_prob = torch.sigmoid(
            out["rdr_logits"]
        )

        all_grade_true.extend(
            grades.cpu().numpy()
        )

        all_grade_pred.extend(
            grade_pred.cpu().numpy()
        )

        all_rdr_true.extend(
            rdr.cpu().numpy()
        )

        all_rdr_prob.extend(
            rdr_prob.cpu().numpy()
        )

    accuracy = accuracy_score(
        all_grade_true,
        all_grade_pred,
    )

    macro_f1 = f1_score(
        all_grade_true,
        all_grade_pred,
        average="macro",
        zero_division=0,
    )

    qwk = cohen_kappa_score(
        all_grade_true,
        all_grade_pred,
        weights="quadratic",
    )

    (
        sensitivity,
        specificity,
        rdr_auc,
    ) = calculate_rdr_metrics(
        all_rdr_true,
        all_rdr_prob,
    )

    val_loss = (
        total_loss
        / len(loader.dataset)
    )

    return {
        "loss":
            val_loss,

        "accuracy":
            accuracy,

        "macro_f1":
            macro_f1,

        "qwk":
            qwk,

        "sensitivity":
            sensitivity,

        "specificity":
            specificity,

        "rdr_auc":
            rdr_auc,
    }


def main():

    seed_everything(
        SEED
    )

    CHECKPOINT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    HISTORY.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "\n=== APTOS GLOBAL DR TRAINING ==="
    )

    print(
        "Device:",
        device
    )

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    train_df, val_df = (
        build_split()
    )

    print(
        "Train:",
        len(train_df)
    )

    print(
        "Val:",
        len(val_df)
    )

    print(
        "\nTrain class distribution:"
    )

    print(
        train_df[
            "diagnosis"
        ].value_counts().sort_index()
    )

    train_ds = APTOSDataset(
        train_df,
        IMAGE_DIR,
        transform=get_train_transform(
            IMAGE_SIZE
        ),
    )

    val_ds = APTOSDataset(
        val_df,
        IMAGE_DIR,
        transform=get_eval_transform(
            IMAGE_SIZE
        ),
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=True,
        persistent_workers=(
            NUM_WORKERS > 0
        ),
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=True,
        persistent_workers=(
            NUM_WORKERS > 0
        ),
    )

    model = GlobalDRModel(
        backbone="efficientnet_b0",
        pretrained=True,
    ).to(device)

    weights = class_weights(
        train_df
    ).to(device)

    print(
        "\nClass weights:",
        weights
    )

    grade_loss_fn = (
        nn.CrossEntropyLoss(
            weight=weights,
            label_smoothing=0.05,
        )
    )

    # Slight class imbalance protection
    n_rdr = (
        train_df[
            "diagnosis"
        ] >= 2
    ).sum()

    n_non = (
        train_df[
            "diagnosis"
        ] < 2
    ).sum()

    pos_weight = torch.tensor(
        [n_non / n_rdr],
        dtype=torch.float32,
        device=device,
    )

    rdr_loss_fn = (
        nn.BCEWithLogitsLoss(
            pos_weight=pos_weight
        )
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LR,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = (
        torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=EPOCHS,
            eta_min=1e-6,
        )
    )

    scaler = torch.amp.GradScaler(
        "cuda",
        enabled=(
            device.type == "cuda"
        ),
    )

    history = []

    best_score = -1

    epochs_without_improvement = 0

    for epoch in range(
        1,
        EPOCHS + 1
    ):

        start = time.time()

        print(
            f"\nEpoch {epoch}/{EPOCHS}"
        )

        train_loss = train_epoch(
            model,
            train_loader,
            optimizer,
            grade_loss_fn,
            rdr_loss_fn,
            scaler,
            device,
        )

        metrics = validate(
            model,
            val_loader,
            grade_loss_fn,
            rdr_loss_fn,
            device,
        )

        scheduler.step()

        # SIH-weighted model-selection score
        selection_score = (
            0.40
            * metrics["qwk"]
            +
            0.35
            * metrics["sensitivity"]
            +
            0.25
            * metrics["specificity"]
        )

        minutes = (
            time.time()
            - start
        ) / 60

        print(
            f"Train loss : {train_loss:.4f}"
        )

        print(
            f"Val loss   : {metrics['loss']:.4f}"
        )

        print(
            f"Accuracy   : {metrics['accuracy']:.4f}"
        )

        print(
            f"Macro F1   : {metrics['macro_f1']:.4f}"
        )

        print(
            f"QWK        : {metrics['qwk']:.4f}"
        )

        print(
            f"RDR Sens   : {metrics['sensitivity']:.4f}"
        )

        print(
            f"RDR Spec   : {metrics['specificity']:.4f}"
        )

        print(
            f"RDR AUC    : {metrics['rdr_auc']:.4f}"
        )

        print(
            f"Score      : {selection_score:.4f}"
        )

        print(
            f"Time       : {minutes:.2f} min"
        )

        row = {
            "epoch":
                epoch,

            "train_loss":
                train_loss,

            **metrics,

            "selection_score":
                selection_score,

            "minutes":
                minutes,
        }

        history.append(
            row
        )

        pd.DataFrame(
            history
        ).to_csv(
            HISTORY,
            index=False,
        )

        if (
            selection_score
            > best_score
        ):

            best_score = (
                selection_score
            )

            epochs_without_improvement = 0

            torch.save(
                {
                    "epoch":
                        epoch,

                    "model_state_dict":
                        model.state_dict(),

                    "selection_score":
                        selection_score,

                    "metrics":
                        metrics,

                    "image_size":
                        IMAGE_SIZE,

                    "backbone":
                        "efficientnet_b0",

                    "labels": {
                        0: "No DR",
                        1: "Mild NPDR",
                        2: "Moderate NPDR",
                        3: "Severe NPDR",
                        4: "Proliferative DR",
                    },

                    "rdr_definition":
                        "ICDR >=2",
                },

                CHECKPOINT,
            )

            print(
                "BEST GLOBAL CHECKPOINT SAVED"
            )

        else:

            epochs_without_improvement += 1

        if (
            epochs_without_improvement
            >= PATIENCE
        ):

            print(
                "\nEarly stopping."
            )

            break

    print(
        "\n=== GLOBAL TRAINING FINISHED ==="
    )

    print(
        "Best score:",
        round(best_score, 4)
    )

    print(
        "Checkpoint:",
        CHECKPOINT
    )


if __name__ == "__main__":
    main()