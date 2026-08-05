from ai.datasets.torch_dataset import RetinaDataset

from ai.preprocessing.transforms import (
    get_train_transforms
)

dataset = RetinaDataset(

    "datasets/metadata/ODIR5K/metadata.json",

    transform=get_train_transforms()

)

print("=" * 60)

print("Dataset Size")

print("=" * 60)

print(len(dataset))

image, label = dataset[0]

print()

print(image.shape)

print(label)

print(image.min())

print(image.max())