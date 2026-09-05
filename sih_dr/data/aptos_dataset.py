from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image


LABELS = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


def crop_retina(img):
    """
    Remove large black borders while preserving the complete retinal FOV.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    mask = gray > 10

    coords = cv2.findNonZero(mask.astype(np.uint8))

    if coords is None:
        return img

    x, y, w, h = cv2.boundingRect(coords)

    return img[y:y+h, x:x+w]


def get_train_transform(size=384):
    return transforms.Compose([
        transforms.Resize((size, size)),

        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),

        transforms.RandomRotation(
            degrees=15
        ),

        transforms.ColorJitter(
            brightness=0.12,
            contrast=0.12,
            saturation=0.08,
            hue=0.02,
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


def get_eval_transform(size=384):
    return transforms.Compose([
        transforms.Resize((size, size)),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


class APTOSDataset(Dataset):

    def __init__(
        self,
        dataframe,
        image_dir,
        transform=None,
    ):
        self.df = dataframe.reset_index(drop=True)

        self.image_dir = Path(image_dir)

        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):

        row = self.df.iloc[idx]

        image_id = row["id_code"]

        grade = int(row["diagnosis"])

        image_path = (
            self.image_dir /
            f"{image_id}.png"
        )

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            raise RuntimeError(
                f"Could not read {image_path}"
            )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        image = crop_retina(image)

        image = Image.fromarray(image)

        if self.transform:
            image = self.transform(image)

        # PS definition: Grade >=2 = Referable DR
        rdr = float(grade >= 2)

        return {
            "image": image,
            "grade": torch.tensor(
                grade,
                dtype=torch.long,
            ),
            "rdr": torch.tensor(
                rdr,
                dtype=torch.float32,
            ),
            "image_id": image_id,
        }