import cv2
import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset

import albumentations as A
from albumentations.pytorch import ToTensorV2


LESION_CODES = [
    "MA",
    "HE",
    "EX",
    "SE",
]


def get_train_transform():

    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),

            A.ShiftScaleRotate(
                shift_limit=0.03,
                scale_limit=0.05,
                rotate_limit=15,
                border_mode=cv2.BORDER_REFLECT_101,
                p=0.4,
            ),

            A.RandomBrightnessContrast(
                brightness_limit=0.10,
                contrast_limit=0.10,
                p=0.3,
            ),

            A.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225),
            ),

            ToTensorV2(),
        ]
    )


def get_eval_transform():

    return A.Compose(
        [
            A.Normalize(
                mean=(0.485, 0.456, 0.406),
                std=(0.229, 0.224, 0.225),
            ),

            ToTensorV2(),
        ]
    )


class IDRiDLesionDataset(Dataset):

    def __init__(
        self,
        manifest_path,
        split,
        transform=None,
    ):

        df = pd.read_csv(
            manifest_path
        )

        self.df = (
            df[
                df["cv_split"] == split
            ]
            .reset_index(drop=True)
        )

        self.transform = transform

        if len(self.df) == 0:
            raise RuntimeError(
                f"No samples for {split}"
            )

    def __len__(self):

        return len(self.df)

    def __getitem__(self, index):

        row = self.df.iloc[index]

        image = cv2.imread(
            row["cached_image_path"]
        )

        if image is None:
            raise RuntimeError(
                row["cached_image_path"]
            )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        data = np.load(
            row["cached_mask_path"]
        )

        masks = data["mask"]

        masks = [
            masks[i]
            for i in range(4)
        ]

        if self.transform:

            aug = self.transform(
                image=image,
                masks=masks,
            )

            image = aug["image"]

            masks = aug["masks"]

        masks = torch.stack(
            [
                m.float()
                if torch.is_tensor(m)
                else torch.from_numpy(m).float()
                for m in masks
            ],
            dim=0,
        )

        masks = (
            masks > 0
        ).float()

        return {
            "image": image.float(),

            "mask": masks,

            "metadata": {
                "image_id":
                    str(row["image_id"]),

                "tile_id":
                    str(row["tile_id"]),

                "x_start":
                    int(row["x_start"]),

                "y_start":
                    int(row["y_start"]),
            }
        }