from pathlib import Path
import sys
import json
import random

import numpy as np
import pandas as pd

import torch

from torch.utils.data import DataLoader

from sklearn.model_selection import (
    train_test_split
)

from sklearn.metrics import (
    confusion_matrix,
    log_loss,
    roc_auc_score,
    average_precision_score,
)


ROOT = Path(
    __file__
).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT)
)


from sih_dr.data.aptos_dataset import (
    APTOSDataset,
    get_eval_transform,
)

from sih_dr.grading.model import (
    GlobalDRModel,
)

from sih_dr.calibration.temperature_scaling import (
    TemperatureScaler,
    multiclass_ece,
    binary_ece,
    multiclass_brier,
    binary_brier,
)


# ============================================================
# CONFIG
# ============================================================

CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "grading"
    / "global_final.pth"
)

SPLIT_FILE = (
    ROOT
    / "datasets"
    / "metadata"
    / "APTOS2019_split.csv"
)

IMAGE_DIR = (
    ROOT
    / "datasets"
    / "raw"
    / "APTOS2019"
    / "train_images"
)

OUTPUT_DIR = (
    ROOT
    / "nationals"
    / "calibration"
)

SEED = 2026
BATCH_SIZE = 8
NUM_WORKERS = 0


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


def collect_logits(
    model,
    loader,
    device,
):

    model.eval()

    grade_logits_all = []
    rdr_logits_all = []

    grades_all = []
    rdr_all = []

    ids_all = []

    with torch.no_grad():

        for batch in loader:

            images = batch[
                "image"
            ].to(
                device
            )

            output = model(
                images
            )

            grade_logits_all.append(
                output[
                    "grade_logits"
                ].float().cpu()
            )

            rdr_logits_all.append(
                output[
                    "rdr_logits"
                ].float().cpu()
            )

            grades_all.append(
                batch[
                    "grade"
                ].cpu()
            )

            rdr_all.append(
                batch[
                    "rdr"
                ].cpu()
            )

            ids_all.extend(
                batch[
                    "image_id"
                ]
            )

    return {
        "grade_logits":
            torch.cat(
                grade_logits_all,
                dim=0
            ),

        "rdr_logits":
            torch.cat(
                rdr_logits_all,
                dim=0
            ).reshape(-1),

        "grades":
            torch.cat(
                grades_all,
                dim=0
            ),

        "rdr":
            torch.cat(
                rdr_all,
                dim=0
            ).reshape(-1),

        "ids":
            ids_all,
    }


def softmax_np(
    logits
):

    logits = np.asarray(
        logits,
        dtype=np.float64
    )

    logits = (
        logits
        -
        logits.max(
            axis=1,
            keepdims=True
        )
    )

    exp = np.exp(
        logits
    )

    return (
        exp
        /
        exp.sum(
            axis=1,
            keepdims=True
        )
    )


def sigmoid_np(
    logits
):

    logits = np.asarray(
        logits,
        dtype=np.float64
    )

    return (
        1.0
        /
        (
            1.0
            +
            np.exp(
                -logits
            )
        )
    )


def rdr_metrics(
    y_true,
    probability,
    threshold,
):

    y_true = np.asarray(
        y_true,
        dtype=np.int64
    )

    probability = np.asarray(
        probability,
        dtype=np.float64
    )

    prediction = (
        probability
        >= threshold
    ).astype(
        np.int64
    )

    tn, fp, fn, tp = (
        confusion_matrix(
            y_true,
            prediction,
            labels=[
                0,
                1
            ]
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

    ppv = (
        tp
        /
        max(
            tp + fp,
            1
        )
    )

    npv = (
        tn
        /
        max(
            tn + fn,
            1
        )
    )

    return {
        "threshold":
            float(
                threshold
            ),

        "tp":
            int(tp),

        "tn":
            int(tn),

        "fp":
            int(fp),

        "fn":
            int(fn),

        "sensitivity":
            float(
                sensitivity
            ),

        "specificity":
            float(
                specificity
            ),

        "ppv":
            float(
                ppv
            ),

        "npv":
            float(
                npv
            ),
    }


def choose_threshold(
    y_true,
    probability,
):

    rows = []

    for threshold in np.linspace(
        0.01,
        0.99,
        981
    ):

        m = rdr_metrics(
            y_true,
            probability,
            threshold,
        )

        m[
            "youden_j"
        ] = (
            m[
                "sensitivity"
            ]
            +
            m[
                "specificity"
            ]
            -
            1.0
        )

        m[
            "meets_ps_target"
        ] = bool(
            m[
                "sensitivity"
            ]
            >= 0.90
            and
            m[
                "specificity"
            ]
            >= 0.85
        )

        rows.append(
            m
        )

    df = pd.DataFrame(
        rows
    )

    feasible = df[
        df[
            "meets_ps_target"
        ]
    ].copy()

    if len(
        feasible
    ) > 0:

        chosen = (
            feasible
            .sort_values(
                by=[
                    "youden_j",
                    "sensitivity",
                    "specificity",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ]
            )
            .iloc[0]
        )

        mode = (
            "PS_CONSTRAINED_YOUDEN"
        )

    else:

        chosen = (
            df
            .sort_values(
                by=[
                    "youden_j"
                ],
                ascending=False
            )
            .iloc[0]
        )

        mode = (
            "BEST_YOUDEN_NO_PS_FEASIBLE_THRESHOLD"
        )

    return (
        float(
            chosen[
                "threshold"
            ]
        ),
        mode,
        df
    )


def evaluate_grade(
    probs,
    targets,
):

    targets = np.asarray(
        targets,
        dtype=np.int64
    )

    probs = np.asarray(
        probs,
        dtype=np.float64
    )

    prediction = probs.argmax(
        axis=1
    )

    accuracy = float(
        (
            prediction
            == targets
        ).mean()
    )

    nll = float(
        log_loss(
            targets,
            probs,
            labels=[
                0,
                1,
                2,
                3,
                4,
            ]
        )
    )

    return {
        "accuracy":
            accuracy,

        "nll":
            nll,

        "ece":
            multiclass_ece(
                probs,
                targets
            ),

        "brier":
            multiclass_brier(
                probs,
                targets
            ),
    }


def evaluate_rdr(
    probabilities,
    targets,
):

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64
    )

    targets = np.asarray(
        targets,
        dtype=np.int64
    )

    eps = 1e-8

    clipped = np.clip(
        probabilities,
        eps,
        1.0 - eps
    )

    nll = float(
        -np.mean(
            targets
            * np.log(
                clipped
            )
            +
            (
                1
                -
                targets
            )
            * np.log(
                1.0
                -
                clipped
            )
        )
    )

    return {
        "nll":
            nll,

        "ece":
            binary_ece(
                probabilities,
                targets
            ),

        "brier":
            binary_brier(
                probabilities,
                targets
            ),

        "auroc":
            float(
                roc_auc_score(
                    targets,
                    probabilities
                )
            ),

        "aupr":
            float(
                average_precision_score(
                    targets,
                    probabilities
                )
            ),
    }


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "\n=== NETRAAI CALIBRATION ==="
    )

    print(
        "\nLoading checkpoint:"
    )

    print(
        CHECKPOINT
    )


    checkpoint = torch.load(
        CHECKPOINT,
        map_location="cpu",
        weights_only=False,
    )


    image_size = int(
        checkpoint.get(
            "image_size",
            384
        )
    )

    backbone = checkpoint.get(
        "backbone",
        "efficientnet_b0"
    )


    # --------------------------------------------------------
    # LOAD ORIGINAL VALIDATION SPLIT
    # --------------------------------------------------------

    split_df = pd.read_csv(
        SPLIT_FILE
    )

    val_df = (
        split_df[
            split_df[
                "split"
            ]
            ==
            "val"
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )


    print(
        "\nOriginal validation cases:",
        len(
            val_df
        )
    )


    calibration_df, evaluation_df = (
        train_test_split(
            val_df,
            test_size=0.50,
            random_state=SEED,
            stratify=val_df[
                "diagnosis"
            ],
        )
    )


    calibration_df = (
        calibration_df
        .copy()
        .reset_index(
            drop=True
        )
    )

    evaluation_df = (
        evaluation_df
        .copy()
        .reset_index(
            drop=True
        )
    )


    calibration_df[
        "calibration_role"
    ] = "fit"

    evaluation_df[
        "calibration_role"
    ] = "eval"


    calibration_split = pd.concat(
        [
            calibration_df,
            evaluation_df
        ],
        ignore_index=True
    )


    calibration_split.to_csv(
        OUTPUT_DIR
        /
        "APTOS_calibration_split.csv",
        index=False,
    )


    print(
        "Calibration fit:",
        len(
            calibration_df
        )
    )

    print(
        "Calibration eval:",
        len(
            evaluation_df
        )
    )


    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    calibration_ds = APTOSDataset(
        calibration_df,
        IMAGE_DIR,
        transform=get_eval_transform(
            image_size
        ),
    )

    evaluation_ds = APTOSDataset(
        evaluation_df,
        IMAGE_DIR,
        transform=get_eval_transform(
            image_size
        ),
    )


    calibration_loader = DataLoader(
        calibration_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )

    evaluation_loader = DataLoader(
        evaluation_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
    )


    # --------------------------------------------------------
    # MODEL
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


    model = GlobalDRModel(
        backbone=backbone,
        pretrained=False,
    )

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ],
        strict=True,
    )

    model.to(
        device
    )

    model.eval()


    # --------------------------------------------------------
    # COLLECT LOGITS
    # --------------------------------------------------------

    print(
        "\nCollecting calibration logits..."
    )

    fit = collect_logits(
        model,
        calibration_loader,
        device,
    )


    print(
        "Collecting evaluation logits..."
    )

    evaluation = collect_logits(
        model,
        evaluation_loader,
        device,
    )


    # --------------------------------------------------------
    # TEMPERATURE FITTING
    # --------------------------------------------------------

    grade_scaler = (
        TemperatureScaler(
            task="multiclass"
        )
    )

    rdr_scaler = (
        TemperatureScaler(
            task="binary"
        )
    )


    grade_temperature = (
        grade_scaler.fit(
            fit[
                "grade_logits"
            ],
            fit[
                "grades"
            ],
        )
    )


    rdr_temperature = (
        rdr_scaler.fit(
            fit[
                "rdr_logits"
            ],
            fit[
                "rdr"
            ],
        )
    )


    print(
        "\nGrade temperature:",
        grade_temperature
    )

    print(
        "RDR temperature:",
        rdr_temperature
    )


    # --------------------------------------------------------
    # FIT-SET CALIBRATED RDR
    # --------------------------------------------------------

    fit_rdr_calibrated = sigmoid_np(
        fit[
            "rdr_logits"
        ].numpy()
        /
        rdr_temperature
    )


    threshold, threshold_mode, sweep = (
        choose_threshold(
            fit[
                "rdr"
            ].numpy(),
            fit_rdr_calibrated,
        )
    )


    sweep.to_csv(
        OUTPUT_DIR
        /
        "rdr_threshold_sweep.csv",
        index=False,
    )


    print(
        "\nLocked RDR threshold:",
        threshold
    )

    print(
        "Selection mode:",
        threshold_mode
    )


    # --------------------------------------------------------
    # EVALUATION
    # --------------------------------------------------------

    grade_logits_eval = (
        evaluation[
            "grade_logits"
        ].numpy()
    )


    rdr_logits_eval = (
        evaluation[
            "rdr_logits"
        ].numpy()
    )


    grade_targets_eval = (
        evaluation[
            "grades"
        ].numpy()
    )


    rdr_targets_eval = (
        evaluation[
            "rdr"
        ].numpy()
    )


    grade_probs_raw = softmax_np(
        grade_logits_eval
    )

    grade_probs_calibrated = softmax_np(
        grade_logits_eval
        /
        grade_temperature
    )


    rdr_probs_raw = sigmoid_np(
        rdr_logits_eval
    )

    rdr_probs_calibrated = sigmoid_np(
        rdr_logits_eval
        /
        rdr_temperature
    )


    grade_before = evaluate_grade(
        grade_probs_raw,
        grade_targets_eval,
    )

    grade_after = evaluate_grade(
        grade_probs_calibrated,
        grade_targets_eval,
    )


    rdr_before = evaluate_rdr(
        rdr_probs_raw,
        rdr_targets_eval,
    )

    rdr_after = evaluate_rdr(
        rdr_probs_calibrated,
        rdr_targets_eval,
    )


    rdr_operating = rdr_metrics(
        rdr_targets_eval,
        rdr_probs_calibrated,
        threshold,
    )


    # --------------------------------------------------------
    # SAVE PER-CASE OUTPUT
    # --------------------------------------------------------

    prediction_rows = []

    for i, image_id in enumerate(
        evaluation[
            "ids"
        ]
    ):

        prediction_rows.append({
            "image_id":
                image_id,

            "grade_true":
                int(
                    grade_targets_eval[i]
                ),

            "rdr_true":
                int(
                    rdr_targets_eval[i]
                ),

            "grade_raw_confidence":
                float(
                    grade_probs_raw[
                        i
                    ].max()
                ),

            "grade_calibrated_confidence":
                float(
                    grade_probs_calibrated[
                        i
                    ].max()
                ),

            "grade_raw_pred":
                int(
                    grade_probs_raw[
                        i
                    ].argmax()
                ),

            "grade_calibrated_pred":
                int(
                    grade_probs_calibrated[
                        i
                    ].argmax()
                ),

            "rdr_raw":
                float(
                    rdr_probs_raw[
                        i
                    ]
                ),

            "rdr_calibrated":
                float(
                    rdr_probs_calibrated[
                        i
                    ]
                ),

            "rdr_pred_locked":
                int(
                    rdr_probs_calibrated[
                        i
                    ]
                    >=
                    threshold
                ),
        })


    pd.DataFrame(
        prediction_rows
    ).to_csv(
        OUTPUT_DIR
        /
        "calibration_eval_predictions.csv",
        index=False,
    )


    # --------------------------------------------------------
    # SAVE CONFIG + REPORT
    # --------------------------------------------------------

    result = {

        "version":
            "NETRAAI_CALIBRATION_V1",

        "checkpoint":
            str(
                CHECKPOINT
            ),

        "backbone":
            backbone,

        "image_size":
            image_size,

        "split": {
            "original_validation_cases":
                len(
                    val_df
                ),

            "calibration_fit_cases":
                len(
                    calibration_df
                ),

            "calibration_eval_cases":
                len(
                    evaluation_df
                ),

            "seed":
                SEED,

            "note":
                (
                    "Baseline checkpoint was originally selected "
                    "using the full validation split. "
                    "This deterministic subdivision is for "
                    "prototype calibration evaluation, not an "
                    "independent final clinical test."
                ),
        },

        "temperature": {
            "grade":
                grade_temperature,

            "rdr":
                rdr_temperature,
        },

        "rdr_operating_point": {
            "threshold":
                threshold,

            "selection":
                threshold_mode,

            "definition":
                "ICDR >= 2",
        },

        "grade_calibration": {
            "before":
                grade_before,

            "after":
                grade_after,
        },

        "rdr_calibration": {
            "before":
                rdr_before,

            "after":
                rdr_after,
        },

        "locked_threshold_eval":
            rdr_operating,
    }


    output_json = (
        OUTPUT_DIR
        /
        "calibration_config.json"
    )


    with open(
        output_json,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
        )


    # --------------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------------

    print(
        "\n=================================="
    )

    print(
        "GRADE CALIBRATION"
    )

    print(
        "=================================="
    )

    print(
        "ECE before:",
        round(
            grade_before[
                "ece"
            ],
            6
        )
    )

    print(
        "ECE after :",
        round(
            grade_after[
                "ece"
            ],
            6
        )
    )

    print(
        "NLL before:",
        round(
            grade_before[
                "nll"
            ],
            6
        )
    )

    print(
        "NLL after :",
        round(
            grade_after[
                "nll"
            ],
            6
        )
    )

    print(
        "Brier before:",
        round(
            grade_before[
                "brier"
            ],
            6
        )
    )

    print(
        "Brier after :",
        round(
            grade_after[
                "brier"
            ],
            6
        )
    )


    print(
        "\n=================================="
    )

    print(
        "RDR CALIBRATION"
    )

    print(
        "=================================="
    )

    print(
        "ECE before:",
        round(
            rdr_before[
                "ece"
            ],
            6
        )
    )

    print(
        "ECE after :",
        round(
            rdr_after[
                "ece"
            ],
            6
        )
    )

    print(
        "NLL before:",
        round(
            rdr_before[
                "nll"
            ],
            6
        )
    )

    print(
        "NLL after :",
        round(
            rdr_after[
                "nll"
            ],
            6
        )
    )

    print(
        "Brier before:",
        round(
            rdr_before[
                "brier"
            ],
            6
        )
    )

    print(
        "Brier after :",
        round(
            rdr_after[
                "brier"
            ],
            6
        )
    )


    print(
        "\n=================================="
    )

    print(
        "LOCKED RDR OPERATING POINT"
    )

    print(
        "=================================="
    )

    print(
        "Threshold:",
        threshold
    )

    print(
        "Sensitivity:",
        round(
            rdr_operating[
                "sensitivity"
            ],
            6
        )
    )

    print(
        "Specificity:",
        round(
            rdr_operating[
                "specificity"
            ],
            6
        )
    )

    print(
        "PPV:",
        round(
            rdr_operating[
                "ppv"
            ],
            6
        )
    )

    print(
        "NPV:",
        round(
            rdr_operating[
                "npv"
            ],
            6
        )
    )

    print(
        "TP/TN/FP/FN:",
        rdr_operating[
            "tp"
        ],
        rdr_operating[
            "tn"
        ],
        rdr_operating[
            "fp"
        ],
        rdr_operating[
            "fn"
        ],
    )


    print(
        "\nSaved:"
    )

    print(
        output_json
    )

    print(
        "\n=== CALIBRATION COMPLETE ==="
    )


if __name__ == "__main__":
    main()
