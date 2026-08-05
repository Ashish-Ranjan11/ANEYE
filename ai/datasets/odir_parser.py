from pathlib import Path

from .base_parser import BaseDatasetParser
from .label_mapper import CLASS_MAPPING, CANONICAL_NAMES


class ODIRParser(BaseDatasetParser):

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def parse(self):

        samples = []

        for disease_folder in sorted(self.dataset_root.iterdir()):

            if not disease_folder.is_dir():
                continue

            folder_name = disease_folder.name

            key = folder_name.lower()

            if key not in CLASS_MAPPING:
                print(f"Skipping unknown folder: {folder_name}")
                continue

            for image_path in disease_folder.rglob("*"):

                if image_path.suffix.lower() not in self.IMAGE_EXTENSIONS:
                    continue

                samples.append(
                    {
                        "image_path": str(image_path),
                        "dataset": "ODIR5K",
                        "label": CANONICAL_NAMES[key],
                        "class_id": CLASS_MAPPING[key],
                    }
                )

        return samples