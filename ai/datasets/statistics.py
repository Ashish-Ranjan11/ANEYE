from collections import Counter
import numpy as np


class DatasetStatistics:

    def __init__(self, metadata):
        self.metadata = metadata

    def generate(self):

        labels = [item["label"] for item in self.metadata]

        widths = [item["width"] for item in self.metadata]
        heights = [item["height"] for item in self.metadata]

        blur = [item["blur_score"] for item in self.metadata]
        brightness = [item["brightness"] for item in self.metadata]
        contrast = [item["contrast"] for item in self.metadata]

        valid = sum(item["valid"] for item in self.metadata)

        report = {

            "total_images": len(self.metadata),

            "valid_images": valid,

            "invalid_images": len(self.metadata) - valid,

            "classes": dict(Counter(labels)),

            "average_width": float(np.mean(widths)),

            "average_height": float(np.mean(heights)),

            "average_blur": float(np.mean(blur)),

            "average_brightness": float(np.mean(brightness)),

            "average_contrast": float(np.mean(contrast))

        }

        return report