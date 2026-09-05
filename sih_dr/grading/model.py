import torch
import torch.nn as nn
import timm


class GlobalDRModel(nn.Module):

    def __init__(
        self,
        backbone="efficientnet_b0",
        pretrained=True,
    ):
        super().__init__()

        self.encoder = timm.create_model(
            backbone,
            pretrained=pretrained,
            num_classes=0,
            global_pool="avg",
        )

        n_features = (
            self.encoder.num_features
        )

        self.dropout = nn.Dropout(0.30)

        # ICDR 0-4
        self.grade_head = nn.Linear(
            n_features,
            5
        )

        # Referable DR
        self.rdr_head = nn.Linear(
            n_features,
            1
        )

    def forward(self, x):

        features = self.encoder(x)

        features = self.dropout(
            features
        )

        grade_logits = (
            self.grade_head(features)
        )

        rdr_logits = (
            self.rdr_head(features)
            .squeeze(1)
        )

        return {
            "grade_logits":
                grade_logits,

            "rdr_logits":
                rdr_logits,

            "features":
                features,
        }