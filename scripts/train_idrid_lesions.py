from pathlib import Path
import json
import math
import time

import numpy as np
import pandas as pd

import torch
from torch.utils.data import (
    DataLoader,
    WeightedRandomSampler,
)

from tqdm import tqdm

from sih_dr.data.idrid_lesion_dataset import (
    IDRiDLesionDataset,
    get_train_transform,
    get_eval_transform,
)

from sih_dr.lesions.model import (
    build_lesion_model,
)

from sih_dr.lesions.losses import (
    LesionLoss,
)


MANIFEST = (
    "datasets/metadata/IDRiD/"
    "tile_manifest_cached.csv"
)

CHECKPOINT = Path(
    "checkpoints/sih_dr/lesions/"
    "idrid_unet_b0_best.pth"
)

HISTORY_PATH = Path(
    "results/sih_dr/lesions/"
    "training_history.csv"
)

CONFIG_PATH = Path(
    "results/sih_dr/lesions/"
    "training_config.json"
)


LESION_NAMES = [
    "MA",
    "HE",
    "EX",
    "SE",
]


# RTX 3050 6 GB
BATCH_SIZE = 2
ACCUM_STEPS = 4

EPOCHS = 20

LEARNING_RATE = 2e-4

WEIGHT_DECAY = 1e-4

NUM_WORKERS = 2

THRESHOLD = 0.5

PATIENCE = 5

SEED = 42


def seed_everything(seed):

    np.random.seed(seed)

    torch.manual_seed(seed)

    torch.cuda.manual_seed_all(seed)


def build_sampler(dataset):

    df = dataset.df

    weights = []

    for _, row in df.iterrows():

        has_ma = row["ma_pixels"] > 0
        has_he = row["he_pixels"] > 0
        has_ex = row["ex_pixels"] > 0
        has_se = row["se_pixels"] > 0

        # Start with low probability for pure
        # background patches.
        weight = 0.35

        if has_ma:
            weight += 1.0

        if has_he:
            weight += 1.0

        if has_ex:
            weight += 1.0

        # Soft exudates are much rarer.
        if has_se:
            weight += 4.0

        weights.append(weight)

    weights = torch.DoubleTensor(
        weights
    )

    sampler = WeightedRandomSampler(
        weights=weights,
        num_samples=len(weights),
        replacement=True,
    )

    return sampler


class SegmentationMetrics:

    def __init__(self):

        self.tp = torch.zeros(
            4,
            dtype=torch.float64,
        )

        self.fp = torch.zeros(
            4,
            dtype=torch.float64,
        )

        self.fn = torch.zeros(
            4,
            dtype=torch.float64,
        )

    def update(
        self,
        logits,
        targets,
    ):

        probs = torch.sigmoid(
            logits
        )

        preds = (
            probs >= THRESHOLD
        )

        targets = (
            targets >= 0.5
        )

        dims = (
            0,
            2,
            3,
        )

        tp = (
            preds & targets
        ).sum(dims).cpu()

        fp = (
            preds & ~targets
        ).sum(dims).cpu()

        fn = (
            ~preds & targets
        ).sum(dims).cpu()

        self.tp += tp

        self.fp += fp

        self.fn += fn

    def compute(self):

        eps = 1e-7

        dice = (
            2 * self.tp + eps
        ) / (
            2 * self.tp
            + self.fp
            + self.fn
            + eps
        )

        iou = (
            self.tp + eps
        ) / (
            self.tp
            + self.fp
            + self.fn
            + eps
        )

        return (
            dice.numpy(),
            iou.numpy(),
        )


def train_one_epoch(
    model,
    loader,
    optimizer,
    criterion,
    scaler,
    device,
):

    model.train()

    running_loss = 0.0

    optimizer.zero_grad(
        set_to_none=True
    )

    progress = tqdm(
        loader,
        desc="Train",
        leave=False,
    )

    for step, batch in enumerate(
        progress
    ):

        images = batch["image"].to(
            device,
            non_blocking=True,
        )

        masks = batch["mask"].to(
            device,
            non_blocking=True,
        )

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=device.type == "cuda",
        ):

            logits = model(images)

            loss = criterion(
                logits,
                masks,
            )

            scaled_loss = (
                loss / ACCUM_STEPS
            )

        scaler.scale(
            scaled_loss
        ).backward()

        if (
            (step + 1) % ACCUM_STEPS == 0
            or
            step + 1 == len(loader)
        ):

            scaler.unscale_(
                optimizer
            )

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=5.0,
            )

            scaler.step(
                optimizer
            )

            scaler.update()

            optimizer.zero_grad(
                set_to_none=True
            )

        running_loss += (
            loss.item()
            * images.size(0)
        )

        progress.set_postfix(
            loss=f"{loss.item():.4f}"
        )

    return (
        running_loss
        / len(loader.dataset)
    )


@torch.no_grad()
def validate(
    model,
    loader,
    criterion,
    device,
):

    model.eval()

    running_loss = 0.0

    metrics = (
        SegmentationMetrics()
    )

    progress = tqdm(
        loader,
        desc="Validation",
        leave=False,
    )

    for batch in progress:

        images = batch["image"].to(
            device,
            non_blocking=True,
        )

        masks = batch["mask"].to(
            device,
            non_blocking=True,
        )

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=device.type == "cuda",
        ):

            logits = model(
                images
            )

            loss = criterion(
                logits,
                masks,
            )

        running_loss += (
            loss.item()
            * images.size(0)
        )

        metrics.update(
            logits,
            masks,
        )

    dice, iou = (
        metrics.compute()
    )

    val_loss = (
        running_loss
        / len(loader.dataset)
    )

    return (
        val_loss,
        dice,
        iou,
    )


def main():

    seed_everything(
        SEED
    )

    CHECKPOINT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HISTORY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("\n=== SIH IDRiD LESION TRAINING ===")
    print("Device:", device)

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

        print(
            "VRAM:",
            round(
                torch.cuda.get_device_properties(
                    0
                ).total_memory
                / 1024**3,
                2,
            ),
            "GB",
        )

    train_ds = (
        IDRiDLesionDataset(
            MANIFEST,
            split="train",
            transform=get_train_transform(),
        )
    )

    val_ds = (
        IDRiDLesionDataset(
            MANIFEST,
            split="val",
            transform=get_eval_transform(),
        )
    )

    sampler = (
        build_sampler(
            train_ds
        )
    )

    train_loader = DataLoader(
        train_ds,

        batch_size=BATCH_SIZE,

        sampler=sampler,

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

    print(
        "Train tiles:",
        len(train_ds)
    )

    print(
        "Val tiles:",
        len(val_ds)
    )

    model = (
        build_lesion_model(
            encoder_weights="imagenet"
        )
        .to(device)
    )

    criterion = (
        LesionLoss(
            dice_weight=0.7,
            focal_weight=0.3,
        )
    )

    optimizer = (
        torch.optim.AdamW(
            model.parameters(),
            lr=LEARNING_RATE,
            weight_decay=WEIGHT_DECAY,
        )
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
        enabled=device.type == "cuda",
    )

    config = {

        "model":
            "U-Net",

        "encoder":
            "efficientnet-b0",

        "input_size":
            512,

        "classes":
            LESION_NAMES,

        "batch_size":
            BATCH_SIZE,

        "gradient_accumulation":
            ACCUM_STEPS,

        "effective_batch":
            BATCH_SIZE
            * ACCUM_STEPS,

        "epochs":
            EPOCHS,

        "learning_rate":
            LEARNING_RATE,

        "tile_stride":
            256,

        "validation":
            "image-level split",

        "test":
            "official IDRiD test set untouched",
    }

    with open(
        CONFIG_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            config,
            f,
            indent=2,
        )

    history = []

    best_score = -1.0

    epochs_without_improvement = 0

    for epoch in range(
        1,
        EPOCHS + 1,
    ):

        start = time.time()

        print(
            f"\nEpoch {epoch}/{EPOCHS}"
        )

        train_loss = (
            train_one_epoch(
                model,
                train_loader,
                optimizer,
                criterion,
                scaler,
                device,
            )
        )

        (
            val_loss,
            dice,
            iou,
        ) = validate(
            model,
            val_loader,
            criterion,
            device,
        )

        scheduler.step()

        # Give each lesion equal importance.
        macro_dice = float(
            dice.mean()
        )

        elapsed = (
            time.time()
            - start
        )

        print(
            f"Train loss: {train_loss:.5f}"
        )

        print(
            f"Val loss  : {val_loss:.5f}"
        )

        print(
            f"Macro Dice: {macro_dice:.4f}"
        )

        for i, lesion in enumerate(
            LESION_NAMES
        ):

            print(
                f"{lesion:>2} "
                f"Dice={dice[i]:.4f} "
                f"IoU={iou[i]:.4f}"
            )

        print(
            "Time:",
            round(
                elapsed / 60,
                2,
            ),
            "min",
        )

        print(
            "LR:",
            optimizer.param_groups[0]["lr"]
        )

        row = {

            "epoch":
                epoch,

            "train_loss":
                train_loss,

            "val_loss":
                val_loss,

            "macro_dice":
                macro_dice,

            "ma_dice":
                dice[0],

            "he_dice":
                dice[1],

            "ex_dice":
                dice[2],

            "se_dice":
                dice[3],

            "ma_iou":
                iou[0],

            "he_iou":
                iou[1],

            "ex_iou":
                iou[2],

            "se_iou":
                iou[3],

            "minutes":
                elapsed / 60,
        }

        history.append(
            row
        )

        pd.DataFrame(
            history
        ).to_csv(
            HISTORY_PATH,
            index=False,
        )

        if macro_dice > best_score:

            best_score = (
                macro_dice
            )

            epochs_without_improvement = 0

            torch.save(
                {
                    "epoch":
                        epoch,

                    "model_state_dict":
                        model.state_dict(),

                    "optimizer_state_dict":
                        optimizer.state_dict(),

                    "macro_dice":
                        macro_dice,

                    "dice":
                        dice.tolist(),

                    "iou":
                        iou.tolist(),

                    "config":
                        config,
                },
                CHECKPOINT,
            )

            print(
                "BEST CHECKPOINT SAVED"
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

        if device.type == "cuda":

            print(
                "Peak CUDA memory:",
                round(
                    torch.cuda.max_memory_allocated()
                    / 1024**3,
                    2,
                ),
                "GB",
            )

            torch.cuda.reset_peak_memory_stats()

    print("\n=== TRAINING FINISHED ===")

    print(
        "Best Macro Dice:",
        round(
            best_score,
            4,
        )
    )

    print(
        "Checkpoint:",
        CHECKPOINT
    )

    print(
        "History:",
        HISTORY_PATH
    )


if __name__ == "__main__":
    main()