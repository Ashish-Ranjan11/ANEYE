import timm
import torch.nn as nn


class EfficientNetClassifier(nn.Module):

    def __init__(self, num_classes=8):

        super().__init__()

        self.model = timm.create_model(
            "efficientnet_b0",
            pretrained=True,
            num_classes=0
        )

        self.dropout = nn.Dropout(0.3)

        self.fc = nn.Linear(
            self.model.num_features,
            num_classes
        )

    def forward(self, x):

        x = self.model(x)

        x = self.dropout(x)

        x = self.fc(x)

        return x