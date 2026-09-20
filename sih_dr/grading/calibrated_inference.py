from pathlib import Path
import json

import torch

from sih_dr.grading.inference import (
    GlobalDRInference,
)


class CalibratedGlobalDRInference:
    """
    Frozen EfficientNet baseline + runtime calibration.

    Grade temperature is exposed for research/audit,
    but V1 operational routing remains based on the
    original ICDR argmax because held-out grade
    calibration results were mixed.

    RDR temperature scaling IS adopted because
    ECE, NLL and Brier all improved.
    """

    def __init__(
        self,
        checkpoint_path,
        calibration_config_path,
        device=None,
    ):

        self.base = GlobalDRInference(
            checkpoint_path,
            device=device,
        )

        self.model = self.base.model
        self.device = self.base.device
        self.image_size = self.base.image_size

        calibration_config_path = Path(
            calibration_config_path
        )

        with open(
            calibration_config_path,
            "r",
            encoding="utf-8",
        ) as f:
            self.config = json.load(f)

        self.grade_temperature = float(
            self.config[
                "temperature"
            ][
                "grade"
            ]
        )

        self.rdr_temperature = float(
            self.config[
                "temperature"
            ][
                "rdr"
            ]
        )

        self.rdr_threshold = float(
            self.config[
                "rdr_operating_point"
            ][
                "threshold"
            ]
        )


    def prepare(
        self,
        image_bgr
    ):

        return self.base.prepare(
            image_bgr
        )


    @torch.no_grad()
    def predict(
        self,
        image_bgr
    ):

        tensor = self.prepare(
            image_bgr
        )

        output = self.model(
            tensor
        )

        grade_logits = output[
            "grade_logits"
        ]

        rdr_logits = output[
            "rdr_logits"
        ]

        # ----------------------------------------------------
        # RAW GRADE
        # ----------------------------------------------------

        grade_probs_raw = torch.softmax(
            grade_logits,
            dim=1,
        )[0]

        grade = int(
            grade_probs_raw
            .argmax()
            .item()
        )

        grade_confidence_raw = float(
            grade_probs_raw[
                grade
            ].item()
        )

        # ----------------------------------------------------
        # TEMPERATURE-SCALED GRADE
        #
        # Kept for audit/research.
        # Not yet used as primary T-score confidence because
        # held-out NLL worsened slightly.
        # ----------------------------------------------------

        grade_probs_temp = torch.softmax(
            grade_logits
            /
            self.grade_temperature,
            dim=1,
        )[0]

        grade_confidence_temp = float(
            grade_probs_temp[
                grade
            ].item()
        )

        # ----------------------------------------------------
        # RDR
        # ----------------------------------------------------

        rdr_raw = float(
            torch.sigmoid(
                rdr_logits
            )
            .reshape(-1)[0]
            .item()
        )

        rdr_calibrated = float(
            torch.sigmoid(
                rdr_logits
                /
                self.rdr_temperature
            )
            .reshape(-1)[0]
            .item()
        )

        referable = bool(
            rdr_calibrated
            >=
            self.rdr_threshold
        )

        # Probability assigned to the operationally routed class.
        #
        # Because the threshold is sensitivity-led and below 0.5,
        # a borderline positive may legitimately have confidence
        # below 0.5. That is useful: TRACE should regard such cases
        # as less certain rather than hiding the uncertainty.
        if referable:

            rdr_route_confidence = (
                rdr_calibrated
            )

        else:

            rdr_route_confidence = (
                1.0
                -
                rdr_calibrated
            )

        return {
            "grade":
                grade,

            "grade_probabilities_raw": [
                round(
                    float(x),
                    6
                )
                for x in
                grade_probs_raw.cpu()
            ],

            "grade_confidence_raw":
                round(
                    grade_confidence_raw,
                    6
                ),

            "grade_probabilities_temperature_scaled": [
                round(
                    float(x),
                    6
                )
                for x in
                grade_probs_temp.cpu()
            ],

            "grade_confidence_temperature_scaled":
                round(
                    grade_confidence_temp,
                    6
                ),

            "grade_temperature":
                self.grade_temperature,

            "grade_calibration_status":
                "EVALUATED_NOT_ADOPTED_FOR_TRUST_V1",

            "rdr_probability_raw":
                round(
                    rdr_raw,
                    6
                ),

            "rdr_probability_calibrated":
                round(
                    rdr_calibrated,
                    6
                ),

            "rdr_temperature":
                self.rdr_temperature,

            "rdr_threshold":
                self.rdr_threshold,

            "referable_dr":
                referable,

            "rdr_route_confidence":
                round(
                    rdr_route_confidence,
                    6
                ),

            "rdr_calibration_status":
                "ADOPTED_V1",

            "tensor":
                tensor,
        }
