import json
import cv2
import torch

from torch.utils.data import Dataset


class RetinaDataset(Dataset):

    def __init__(self, metadata_source, transform=None):

        if isinstance(metadata_source, str):

            with open(metadata_source) as f:
                self.data = json.load(f)

        else:

            self.data = metadata_source

        self.transform = transform

    def __len__(self):

        return len(self.data)

    def __getitem__(self, index):

        sample = self.data[index]

        image = cv2.imread(sample["image_path"])

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        if self.transform:

            image = self.transform(image=image)["image"]

        image = torch.tensor(
            image,
            dtype=torch.float32
        ).permute(2, 0, 1)

        image /= 255.0

        label = sample["class_id"]

        return image, label