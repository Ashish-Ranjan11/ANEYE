from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from sih_dr.grading.model import GlobalDRModel
from sih_dr.data.aptos_dataset import (
    crop_retina,
    get_eval_transform,
)


GRADE_NAMES = {
    0: "No apparent DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


class GlobalDRInference:

    def __init__(
        self,
        checkpoint_path,
        device=None
    ):

        self.device = torch.device(
            device
            if device
            else (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device,
            weights_only=False
        )

        self.image_size = checkpoint.get(
            "image_size",
            384
        )

        backbone = checkpoint.get(
            "backbone",
            "efficientnet_b0"
        )

        self.model = GlobalDRModel(
            backbone=backbone,
            pretrained=False
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.to(self.device)

        self.model.eval()

        self.transform = get_eval_transform(
            self.image_size
        )

        self.checkpoint = checkpoint

    def prepare(self, image_bgr):

        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB
        )

        cropped = crop_retina(
            image_rgb
        )

        pil = Image.fromarray(
            cropped
        )

        tensor = self.transform(
            pil
        ).unsqueeze(0)

        return tensor.to(
            self.device
        )

    @torch.no_grad()
    def predict(self, image_bgr):

        tensor = self.prepare(
            image_bgr
        )

        output = self.model(
            tensor
        )

        grade_probs = torch.softmax(
            output["grade_logits"],
            dim=1
        )[0]

        rdr_probability = torch.sigmoid(
            output["rdr_logits"]
        )[0]

        grade = int(
            grade_probs.argmax().item()
        )

        confidence = float(
            grade_probs[grade].item()
        )

        rdr_prob = float(
            rdr_probability.item()
        )

        return {
            "grade": grade,

            "grade_name":
                GRADE_NAMES[grade],

            "grade_probabilities": [
                round(float(x), 5)
                for x in grade_probs.cpu()
            ],

            "grade_confidence":
                round(confidence, 5),

            "rdr_probability":
                round(rdr_prob, 5),

            "referable_dr":
                bool(rdr_prob >= 0.5),

            "tensor":
                tensor
        }