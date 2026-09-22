from pathlib import Path
import sys
import json
import random

import numpy as np
import pandas as pd

import torch
import torch.nn as nn

from torch.utils.data import (
    DataLoader,
)

from sklearn.model_selection import (
    train_test_split,
)

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
)


ROOT = Path(
    __file__
).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)


from sih_dr.advanced.dataset import (
    ADVANCED_LABELS,
    MMRDRAdvancedDataset,
    get_advanced_train_transform,
    get_advanced_eval_transform,
)

from sih_dr.advanced.model import (
    AdvancedDREvidenceModel,
)


# ============================================================
# CONFIG
# ============================================================

MANIFEST = (
    ROOT
    / "nationals"
    / "advanced"
    / "mmrdr_cfp_manifest.csv"
)

GLOBAL_CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "grading"
    / "global_final.pth"
)

OUTPUT_DIR = (
    ROOT
    / "nationals"
    / "advanced"
)

CHECKPOINT_DIR = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "advanced"
)

BEST_CHECKPOINT = (
    CHECKPOINT_DIR
    / "advanced_final.pth"
)


IMAGE_SIZE = 512

BATCH_SIZE = 6

EPOCHS = 12

PATIENCE = 4

SEED = 2026

ENCODER_LR = 5e-5

HEAD_LR = 2e-4

WEIGHT_DECAY = 1e-4


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(
    SEED
)

np.random.seed(
    SEED
)

torch.manual_seed(
    SEED
)

if torch.cuda.is_available():

    torch.cuda.manual_seed_all(
        SEED
    )


# ============================================================
# METRICS
# ============================================================

def binary_metrics(
    y_true,
    probability,
    threshold=0.50,
):

    y_true = np.asarray(
        y_true,
        dtype=np.int64,
    )

    probability = np.asarray(
        probability,
        dtype=np.float64,
    )

    prediction = (
        probability
        >=
        threshold
    ).astype(
        np.int64
    )

    if len(
        np.unique(
            y_true
        )
    ) >= 2:

        auroc = float(
            roc_auc_score(
                y_true,
                probability,
            )
        )

        aupr = float(
            average_precision_score(
                y_true,
                probability,
            )
        )

    else:

        auroc = float(
            "nan"
        )

        aupr = float(
            "nan"
        )


    tn, fp, fn, tp = (
        confusion_matrix(
            y_true,
            prediction,
            labels=[
                0,
                1,
            ],
        )
        .ravel()
    )


    sensitivity = (
        tp
        /
        max(
            tp + fn,
            1
        )
    )

    specificity = (
        tn
        /
        max(
            tn + fp,
            1
        )
    )

    f1 = float(
        f1_score(
            y_true,
            prediction,
            zero_division=0,
        )
    )


    return {
        "auroc":
            auroc,

        "aupr":
            aupr,

        "sensitivity":
            float(
                sensitivity
            ),

        "specificity":
            float(
                specificity
            ),

        "f1":
            f1,

        "tp":
            int(tp),

        "tn":
            int(tn),

        "fp":
            int(fp),

        "fn":
            int(fn),

        "threshold":
            float(
                threshold
            ),
    }


def evaluate_predictions(
    targets,
    probabilities,
):

    result = {}

    aurocs = []
    auprs = []

    for i, name in enumerate(
        ADVANCED_LABELS
    ):

        metrics = binary_metrics(
            targets[
                :,
                i
            ],
            probabilities[
                :,
                i
            ],
            threshold=0.50,
        )

        result[
            name
        ] = metrics

        aurocs.append(
            metrics[
                "auroc"
            ]
        )

        auprs.append(
            metrics[
                "aupr"
            ]
        )


    result[
        "macro_auroc"
    ] = float(
        np.nanmean(
            aurocs
        )
    )

    result[
        "macro_aupr"
    ] = float(
        np.nanmean(
            auprs
        )
    )

    # Precision-recall performance receives
    # greater weight because these labels are rare.
    result[
        "selection_score"
    ] = float(
        0.65
        *
        result[
            "macro_aupr"
        ]
        +
        0.35
        *
        result[
            "macro_auroc"
        ]
    )

    return result


# ============================================================
# INFERENCE
# ============================================================

@torch.no_grad()
def collect_predictions(
    model,
    loader,
    device,
):

    model.eval()

    probabilities = []

    targets = []

    ids = []

    grades = []


    for batch in loader:

        images = (
            batch[
                "image"
            ]
            .to(
                device,
                non_blocking=True,
            )
        )

        output = model(
            images
        )

        probs = torch.sigmoid(
            output[
                "logits"
            ]
        )

        probabilities.append(
            probs
            .float()
            .cpu()
            .numpy()
        )

        targets.append(
            batch[
                "target"
            ]
            .float()
            .cpu()
            .numpy()
        )

        ids.extend(
            batch[
                "image_id"
            ]
        )

        grades.extend(
            [
                int(x)
                for x in
                batch[
                    "grade"
                ]
            ]
        )


    return {
        "probabilities":
            np.concatenate(
                probabilities,
                axis=0,
            ),

        "targets":
            np.concatenate(
                targets,
                axis=0,
            ),

        "ids":
            ids,

        "grades":
            grades,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    print(
        "\n========================================"
    )

    print(
        "NETRAAI ADVANCED EVIDENCE TRAINING"
    )

    print(
        "VB/IRMA + NV + VH"
    )

    print(
        "========================================\n"
    )


    # --------------------------------------------------------
    # DATA SPLITS
    # --------------------------------------------------------

    df = pd.read_csv(
        MANIFEST
    )


    train_full = (
        df[
            df[
                "split"
            ]
            ==
            "train"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


    test_df = (
        df[
            df[
                "split"
            ]
            ==
            "test"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


    if len(
        test_df
    ) != 2225:

        raise RuntimeError(
            f"Expected 2225 test cases, found {len(test_df)}"
        )


    # Validation comes ONLY from supplied training partition.
    #
    # Test remains untouched until final evaluation.
    train_df, val_df = (
        train_test_split(
            train_full,
            test_size=0.15,
            random_state=SEED,
            stratify=train_full[
                "advanced_positive"
            ],
        )
    )


    train_df = (
        train_df
        .copy()
        .reset_index(
            drop=True
        )
    )

    val_df = (
        val_df
        .copy()
        .reset_index(
            drop=True
        )
    )


    train_df[
        "model_split"
    ] = "train"

    val_df[
        "model_split"
    ] = "val"

    test_df[
        "model_split"
    ] = "test"


    full_split = pd.concat(
        [
            train_df,
            val_df,
            test_df,
        ],
        ignore_index=True,
    )


    split_path = (
        OUTPUT_DIR
        /
        "advanced_split_v1.csv"
    )


    full_split.to_csv(
        split_path,
        index=False,
    )


    print(
        "Training:",
        len(
            train_df
        )
    )

    print(
        "Validation:",
        len(
            val_df
        )
    )

    print(
        "Test:",
        len(
            test_df
        )
    )


    print(
        "\nPositive counts:"
    )

    for name in ADVANCED_LABELS:

        print(
            f"{name:8s} "
            f"train={int(train_df[name].sum()):4d} "
            f"val={int(val_df[name].sum()):3d} "
            f"test={int(test_df[name].sum()):3d}"
        )


    # --------------------------------------------------------
    # POSITIVE CLASS WEIGHTS
    # --------------------------------------------------------

    positive_weights = []


    print(
        "\nPositive-class weights:"
    )


    for name in ADVANCED_LABELS:

        positive = float(
            train_df[
                name
            ].sum()
        )

        negative = float(
            len(
                train_df
            )
            -
            positive
        )

        weight = (
            negative
            /
            max(
                positive,
                1.0
            )
        )

        positive_weights.append(
            weight
        )

        print(
            f"{name:8s}: "
            f"{weight:.4f}"
        )


    # --------------------------------------------------------
    # DATASETS
    # --------------------------------------------------------

    train_dataset = (
        MMRDRAdvancedDataset(
            train_df,
            transform=
                get_advanced_train_transform(
                    IMAGE_SIZE
                ),
        )
    )

    val_dataset = (
        MMRDRAdvancedDataset(
            val_df,
            transform=
                get_advanced_eval_transform(
                    IMAGE_SIZE
                ),
        )
    )

    test_dataset = (
        MMRDRAdvancedDataset(
            test_df,
            transform=
                get_advanced_eval_transform(
                    IMAGE_SIZE
                ),
        )
    )


    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
    )


    # --------------------------------------------------------
    # DEVICE / MODEL
    # --------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else
        "cpu"
    )


    print(
        "\nDevice:",
        device
    )


    model = (
        AdvancedDREvidenceModel(
            backbone=
                "efficientnet_b0",

            pretrained=
                False,
        )
    )


    global_checkpoint = torch.load(
        GLOBAL_CHECKPOINT,
        map_location="cpu",
        weights_only=False,
    )


    encoder_load = (
        model.load_retinal_encoder(
            global_checkpoint
        )
    )


    print(
        "\nLoaded APTOS retinal encoder."
    )

    print(
        "Missing encoder keys:",
        len(
            encoder_load[
                "missing"
            ]
        )
    )

    print(
        "Unexpected encoder keys:",
        len(
            encoder_load[
                "unexpected"
            ]
        )
    )


    model.to(
        device
    )


    pos_weight = torch.tensor(
        positive_weights,
        dtype=torch.float32,
        device=device,
    )


    criterion = (
        nn.BCEWithLogitsLoss(
            pos_weight=
                pos_weight
        )
    )


    optimizer = (
        torch.optim.AdamW(
            [
                {
                    "params":
                        model.encoder.parameters(),

                    "lr":
                        ENCODER_LR,
                },

                {
                    "params":
                        model.heads.parameters(),

                    "lr":
                        HEAD_LR,
                },
            ],
            weight_decay=
                WEIGHT_DECAY,
        )
    )


    scaler = (
        torch.amp.GradScaler("cuda", 
            enabled=(
                device.type
                ==
                "cuda"
            )
        )
    )


    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    best_score = -1.0

    best_epoch = -1

    patience_counter = 0

    history = []


    for epoch in range(
        1,
        EPOCHS + 1,
    ):

        model.train()

        losses = []


        for batch in train_loader:

            images = (
                batch[
                    "image"
                ]
                .to(
                    device,
                    non_blocking=True,
                )
            )

            targets = (
                batch[
                    "target"
                ]
                .to(
                    device,
                    non_blocking=True,
                )
            )


            optimizer.zero_grad(
                set_to_none=True
            )


            with torch.autocast(
                device_type=
                    "cuda",

                dtype=
                    torch.float16,

                enabled=(
                    device.type
                    ==
                    "cuda"
                ),
            ):

                output = model(
                    images
                )

                loss = criterion(
                    output[
                        "logits"
                    ],
                    targets,
                )


            scaler.scale(
                loss
            ).backward()


            scaler.step(
                optimizer
            )


            scaler.update()


            losses.append(
                float(
                    loss.item()
                )
            )


        train_loss = float(
            np.mean(
                losses
            )
        )


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        val_output = (
            collect_predictions(
                model,
                val_loader,
                device,
            )
        )


        metrics = (
            evaluate_predictions(
                val_output[
                    "targets"
                ],
                val_output[
                    "probabilities"
                ],
            )
        )


        score = float(
            metrics[
                "selection_score"
            ]
        )


        print(
            "\n----------------------------------------"
        )

        print(
            f"EPOCH {epoch}/{EPOCHS}"
        )

        print(
            "----------------------------------------"
        )

        print(
            f"Train loss : {train_loss:.5f}"
        )

        print(
            f"Macro AUROC: {metrics['macro_auroc']:.4f}"
        )

        print(
            f"Macro AUPR : {metrics['macro_aupr']:.4f}"
        )

        print(
            f"Selection  : {score:.4f}"
        )


        for name in ADVANCED_LABELS:

            m = metrics[
                name
            ]

            print(
                f"{name:8s} | "
                f"AUROC {m['auroc']:.4f} | "
                f"AUPR {m['aupr']:.4f} | "
                f"Sens {m['sensitivity']:.4f} | "
                f"Spec {m['specificity']:.4f} | "
                f"F1 {m['f1']:.4f}"
            )


        history.append({
            "epoch":
                epoch,

            "train_loss":
                train_loss,

            "metrics":
                metrics,
        })


        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        if score > best_score:

            best_score = (
                score
            )

            best_epoch = (
                epoch
            )

            patience_counter = 0


            torch.save(
                {
                    "model_state_dict":
                        model.state_dict(),

                    "epoch":
                        epoch,

                    "selection_score":
                        score,

                    "metrics":
                        metrics,

                    "backbone":
                        "efficientnet_b0",

                    "image_size":
                        IMAGE_SIZE,

                    "labels":
                        ADVANCED_LABELS,

                    "pos_weight":
                        positive_weights,

                    "source_dataset":
                        "MMRDR-CFP",

                    "initialization":
                        (
                            "APTOS-trained EfficientNet-B0 encoder"
                        ),

                    "seed":
                        SEED,
                },
                BEST_CHECKPOINT,
            )


            print(
                "\n*** BEST CHECKPOINT SAVED ***"
            )

        else:

            patience_counter += 1


            print(
                f"\nNo improvement "
                f"({patience_counter}/{PATIENCE})"
            )


            if (
                patience_counter
                >=
                PATIENCE
            ):

                print(
                    "\nEarly stopping."
                )

                break


    # --------------------------------------------------------
    # LOAD BEST MODEL
    # --------------------------------------------------------

    best = torch.load(
        BEST_CHECKPOINT,
        map_location=device,
        weights_only=False,
    )


    model.load_state_dict(
        best[
            "model_state_dict"
        ]
    )


    model.eval()


    # --------------------------------------------------------
    # FINAL TEST — ONCE
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "FINAL UNTOUCHED TEST EVALUATION"
    )

    print(
        "========================================"
    )


    test_output = (
        collect_predictions(
            model,
            test_loader,
            device,
        )
    )


    test_metrics = (
        evaluate_predictions(
            test_output[
                "targets"
            ],
            test_output[
                "probabilities"
            ],
        )
    )


    print(
        "\nBest epoch:",
        best[
            "epoch"
        ]
    )

    print(
        "Test Macro AUROC:",
        round(
            test_metrics[
                "macro_auroc"
            ],
            5
        )
    )

    print(
        "Test Macro AUPR:",
        round(
            test_metrics[
                "macro_aupr"
            ],
            5
        )
    )


    for name in ADVANCED_LABELS:

        m = test_metrics[
            name
        ]

        print(
            f"\n{name}"
        )

        print(
            f"  AUROC      : {m['auroc']:.5f}"
        )

        print(
            f"  AUPR       : {m['aupr']:.5f}"
        )

        print(
            f"  Sensitivity: {m['sensitivity']:.5f}"
        )

        print(
            f"  Specificity: {m['specificity']:.5f}"
        )

        print(
            f"  F1         : {m['f1']:.5f}"
        )

        print(
            f"  TP/TN/FP/FN: "
            f"{m['tp']} "
            f"{m['tn']} "
            f"{m['fp']} "
            f"{m['fn']}"
        )


    # --------------------------------------------------------
    # SAVE TEST PREDICTIONS
    # --------------------------------------------------------

    rows = []


    for i, image_id in enumerate(
        test_output[
            "ids"
        ]
    ):

        row = {
            "image":
                image_id,

            "grade":
                test_output[
                    "grades"
                ][i],
        }


        for j, name in enumerate(
            ADVANCED_LABELS
        ):

            row[
                f"{name}_true"
            ] = int(
                test_output[
                    "targets"
                ][
                    i,
                    j
                ]
            )

            row[
                f"{name}_prob"
            ] = float(
                test_output[
                    "probabilities"
                ][
                    i,
                    j
                ]
            )


        rows.append(
            row
        )


    prediction_path = (
        OUTPUT_DIR
        /
        "advanced_test_predictions_raw.csv"
    )


    pd.DataFrame(
        rows
    ).to_csv(
        prediction_path,
        index=False,
    )


    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    report = {
        "version":
            "ADVANCED_EVIDENCE_V1",

        "best_epoch":
            int(
                best[
                    "epoch"
                ]
            ),

        "best_validation_selection_score":
            float(
                best[
                    "selection_score"
                ]
            ),

        "labels":
            ADVANCED_LABELS,

        "image_size":
            IMAGE_SIZE,

        "train_cases":
            len(
                train_df
            ),

        "validation_cases":
            len(
                val_df
            ),

        "untouched_test_cases":
            len(
                test_df
            ),

        "test_metrics":
            test_metrics,

        "note":
            (
                "0.5 thresholds are preliminary. "
                "Per-label thresholds will be locked "
                "using validation data after training."
            ),
    }


    report_path = (
        OUTPUT_DIR
        /
        "advanced_training_report.json"
    )


    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            report,
            f,
            indent=2,
        )


    print(
        "\nSaved checkpoint:"
    )

    print(
        BEST_CHECKPOINT
    )

    print(
        "\nSaved raw test predictions:"
    )

    print(
        prediction_path
    )

    print(
        "\nSaved report:"
    )

    print(
        report_path
    )


    print(
        "\n========================================"
    )

    print(
        "ADVANCED EVIDENCE TRAINING COMPLETE"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()

