from torch.utils.data import DataLoader

from ai.datasets.torch_dataset import RetinaDataset

from ai.training.splitter import StratifiedDatasetSplitter

from ai.preprocessing.transforms import (
    get_train_transforms,
    get_valid_transforms
)


def create_dataloaders(
    metadata_file,
    batch_size=16
):

    splitter = StratifiedDatasetSplitter(
        metadata_file
    )

    train_metadata, valid_metadata = splitter.split()

    train_dataset = RetinaDataset(
        train_metadata,
        transform=get_train_transforms()
    )

    valid_dataset = RetinaDataset(
        valid_metadata,
        transform=get_valid_transforms()
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )

    valid_loader = DataLoader(
        valid_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )

    return train_loader, valid_loader