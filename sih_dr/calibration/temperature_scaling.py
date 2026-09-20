import numpy as np
import torch
import torch.nn.functional as F


class TemperatureScaler:
    """
    Scalar temperature scaling.

    Supports:
      - multiclass logits [N, C]
      - binary logits [N] or [N, 1]
    """

    def __init__(self, task="multiclass"):

        if task not in {
            "multiclass",
            "binary",
        }:
            raise ValueError(
                "task must be 'multiclass' or 'binary'"
            )

        self.task = task

        self.temperature = 1.0


    def fit(
        self,
        logits,
        targets,
        max_iter=500,
    ):

        logits = (
            logits
            .detach()
            .float()
            .cpu()
        )

        targets = (
            targets
            .detach()
            .cpu()
        )

        log_temperature = torch.nn.Parameter(
            torch.zeros(
                1,
                dtype=torch.float32
            )
        )

        optimizer = torch.optim.LBFGS(
            [log_temperature],
            lr=0.05,
            max_iter=max_iter,
            line_search_fn="strong_wolfe",
        )


        def closure():

            optimizer.zero_grad()

            temperature = torch.exp(
                log_temperature
            ).clamp(
                min=0.05,
                max=20.0,
            )

            scaled = (
                logits
                / temperature
            )

            if self.task == "multiclass":

                loss = F.cross_entropy(
                    scaled,
                    targets.long(),
                )

            else:

                loss = (
                    F.binary_cross_entropy_with_logits(
                        scaled.reshape(-1),
                        targets.float().reshape(-1),
                    )
                )

            loss.backward()

            return loss


        optimizer.step(
            closure
        )

        with torch.no_grad():

            temperature = torch.exp(
                log_temperature
            ).clamp(
                min=0.05,
                max=20.0,
            )

        self.temperature = float(
            temperature.item()
        )

        return self.temperature


    def scale_logits(
        self,
        logits
    ):

        return (
            logits
            / float(self.temperature)
        )


def multiclass_ece(
    probabilities,
    targets,
    n_bins=15,
):

    probs = np.asarray(
        probabilities,
        dtype=np.float64,
    )

    targets = np.asarray(
        targets,
        dtype=np.int64,
    )

    confidence = probs.max(
        axis=1
    )

    prediction = probs.argmax(
        axis=1
    )

    correct = (
        prediction
        == targets
    ).astype(
        np.float64
    )

    boundaries = np.linspace(
        0.0,
        1.0,
        n_bins + 1
    )

    ece = 0.0

    for i in range(
        n_bins
    ):

        low = boundaries[i]
        high = boundaries[i + 1]

        if i == n_bins - 1:

            mask = (
                (confidence >= low)
                &
                (confidence <= high)
            )

        else:

            mask = (
                (confidence >= low)
                &
                (confidence < high)
            )

        if not np.any(mask):
            continue

        bin_accuracy = correct[
            mask
        ].mean()

        bin_confidence = confidence[
            mask
        ].mean()

        ece += (
            mask.mean()
            *
            abs(
                bin_accuracy
                -
                bin_confidence
            )
        )

    return float(ece)


def binary_ece(
    probabilities,
    targets,
    n_bins=15,
):

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64,
    ).reshape(-1)

    targets = np.asarray(
        targets,
        dtype=np.float64,
    ).reshape(-1)

    boundaries = np.linspace(
        0.0,
        1.0,
        n_bins + 1
    )

    ece = 0.0

    for i in range(
        n_bins
    ):

        low = boundaries[i]
        high = boundaries[i + 1]

        if i == n_bins - 1:

            mask = (
                (probabilities >= low)
                &
                (probabilities <= high)
            )

        else:

            mask = (
                (probabilities >= low)
                &
                (probabilities < high)
            )

        if not np.any(mask):
            continue

        observed = targets[
            mask
        ].mean()

        predicted = probabilities[
            mask
        ].mean()

        ece += (
            mask.mean()
            *
            abs(
                observed
                -
                predicted
            )
        )

    return float(ece)


def multiclass_brier(
    probabilities,
    targets,
):

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64,
    )

    targets = np.asarray(
        targets,
        dtype=np.int64,
    )

    one_hot = np.zeros_like(
        probabilities
    )

    one_hot[
        np.arange(
            len(targets)
        ),
        targets
    ] = 1.0

    return float(
        np.mean(
            np.sum(
                (
                    probabilities
                    -
                    one_hot
                ) ** 2,
                axis=1,
            )
        )
    )


def binary_brier(
    probabilities,
    targets,
):

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64,
    ).reshape(-1)

    targets = np.asarray(
        targets,
        dtype=np.float64,
    ).reshape(-1)

    return float(
        np.mean(
            (
                probabilities
                -
                targets
            ) ** 2
        )
    )
