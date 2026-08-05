import torch

from ai.models.efficientnet import EfficientNetClassifier

model = EfficientNetClassifier()

x = torch.randn(4, 3, 224, 224)

y = model(x)

print("=" * 60)

print("Output Shape")

print("=" * 60)

print(y.shape)