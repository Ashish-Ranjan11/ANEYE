import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):

    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):

        probs = torch.sigmoid(logits)

        dims = (0, 2, 3)

        intersection = (
            probs * targets
        ).sum(dims)

        denominator = (
            probs.sum(dims)
            +
            targets.sum(dims)
        )

        dice = (
            2.0 * intersection + self.smooth
        ) / (
            denominator + self.smooth
        )

        return 1.0 - dice.mean()


class BinaryFocalLoss(nn.Module):

    def __init__(
        self,
        alpha=0.75,
        gamma=2.0,
    ):
        super().__init__()

        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, targets):

        bce = F.binary_cross_entropy_with_logits(
            logits,
            targets,
            reduction="none",
        )

        probs = torch.sigmoid(logits)

        p_t = (
            probs * targets
            +
            (1 - probs) * (1 - targets)
        )

        focal = (
            (1 - p_t) ** self.gamma
        ) * bce

        alpha_t = (
            self.alpha * targets
            +
            (1 - self.alpha) * (1 - targets)
        )

        return (
            alpha_t * focal
        ).mean()


class LesionLoss(nn.Module):

    def __init__(
        self,
        dice_weight=0.7,
        focal_weight=0.3,
    ):
        super().__init__()

        self.dice = DiceLoss()
        self.focal = BinaryFocalLoss()

        self.dice_weight = dice_weight
        self.focal_weight = focal_weight

    def forward(self, logits, targets):

        dice = self.dice(
            logits,
            targets,
        )

        focal = self.focal(
            logits,
            targets,
        )

        total = (
            self.dice_weight * dice
            +
            self.focal_weight * focal
        )

        return total