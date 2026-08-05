import json
from pathlib import Path

from ai.datasets.validator import ImageValidator


class MetadataGenerator:

    def __init__(self):

        self.validator = ImageValidator()

    def generate(self, samples):

        metadata = []

        for idx, sample in enumerate(samples):

            quality = self.validator.validate(sample["image_path"])

            metadata.append(
                {
                    "image_id": idx,
                    "image_path": sample["image_path"],
                    "dataset": sample["dataset"],
                    "label": sample["label"],
                    "class_id": sample["class_id"],

                    "width": quality["width"],
                    "height": quality["height"],
                    "channels": quality["channels"],

                    "blur_score": float(quality["blur_score"]),
                    "brightness": float(quality["brightness"]),
                    "contrast": float(quality["contrast"]),

                    "valid": quality["valid"]
                }
            )

        return metadata

    def save(self, metadata, save_path):

        save_path = Path(save_path)

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:

            json.dump(metadata, f, indent=4)