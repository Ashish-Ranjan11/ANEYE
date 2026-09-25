import cv2
import numpy as np
import torch

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


ADVANCED_LABELS = [
    "VB_IRMA",
    "NV",
    "VH",
]


def crop_retina(image_rgb):
    """
    Remove large black fundus-camera borders while
    preserving the complete retinal field.
    """

    gray = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2GRAY,
    )

    mask = (
        gray > 10
    ).astype(
        np.uint8
    )

    coords = cv2.findNonZero(
        mask
    )

    if coords is None:
        return image_rgb

    x, y, w, h = cv2.boundingRect(
        coords
    )

    return image_rgb[
        y:y+h,
        x:x+w
    ]


def get_advanced_train_transform(
    size=512
):

    return transforms.Compose([
        transforms.Resize(
            (
                size,
                size
            )
        ),

        transforms.RandomHorizontalFlip(
            p=0.5
        ),

        transforms.RandomRotation(
            degrees=10
        ),

        transforms.ColorJitter(
            brightness=0.10,
            contrast=0.10,
            saturation=0.08,
            hue=0.02,
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[
                0.485,
                0.456,
                0.406,
            ],
            std=[
                0.229,
                0.224,
                0.225,
            ],
        ),
    ])


def get_advanced_eval_transform(
    size=512
):

    return transforms.Compose([
        transforms.Resize(
            (
                size,
                size
            )
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[
                0.485,
                0.456,
                0.406,
            ],
            std=[
                0.229,
                0.224,
                0.225,
            ],
        ),
    ])


class MMRDRAdvancedDataset(
    Dataset
):

    def __init__(
        self,
        dataframe,
        transform=None,
    ):

        self.df = (
            dataframe
            .reset_index(
                drop=True
            )
        )

        self.transform = (
            transform
        )


    def __len__(
        self
    ):

        return len(
            self.df
        )


    def __getitem__(
        self,
        index
    ):

        row = self.df.iloc[
            index
        ]

        image_path = str(
            row[
                "full_path"
            ]
        )

        image = cv2.imread(
            image_path
        )

        if image is None:

            raise RuntimeError(
                f"Could not read image: {image_path}"
            )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        image = crop_retina(
            image
        )

        image = Image.fromarray(
            image
        )

        if self.transform:

            image = self.transform(
                image
            )

        target = np.asarray(
            [
                row["VB_IRMA"],
                row["NV"],
                row["VH"],
            ],
            dtype=np.float32,
        )

        return {
            "image":
                image,

            "target":
                torch.tensor(
                    target,
                    dtype=torch.float32,
                ),

            "image_id":
                str(
                    row[
                        "image"
                    ]
                ),

            "grade":
                int(
                    row[
                        "grade"
                    ]
                ),
        }
