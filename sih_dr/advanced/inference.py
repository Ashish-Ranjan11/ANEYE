from pathlib import Path
import json

import cv2
import numpy as np
import torch

from PIL import Image


from sih_dr.advanced.dataset import (
    ADVANCED_LABELS,
    crop_retina,
    get_advanced_eval_transform,
)

from sih_dr.advanced.model import (
    AdvancedDREvidenceModel,
)


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(
    __file__
).resolve().parents[2]


# ============================================================
# DEFAULT ARTIFACTS
# ============================================================

DEFAULT_CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "advanced"
    / "advanced_final.pth"
)

DEFAULT_OPERATING_POINTS = (
    ROOT
    / "nationals"
    / "advanced"
    / "advanced_operating_points_v2.json"
)


# ============================================================
# ADVANCED EVIDENCE INFERENCE
# ============================================================

class AdvancedEvidenceInference:

    VERSION = "ADVANCED_EVIDENCE_INFERENCE_V1"


    def __init__(
        self,
        checkpoint_path=None,
        operating_points_path=None,
        device=None,
    ):

        self.checkpoint_path = Path(
            checkpoint_path
            if checkpoint_path is not None
            else DEFAULT_CHECKPOINT
        )

        self.operating_points_path = Path(
            operating_points_path
            if operating_points_path is not None
            else DEFAULT_OPERATING_POINTS
        )


        # ----------------------------------------------------
        # FILE VALIDATION
        # ----------------------------------------------------

        if not self.checkpoint_path.exists():

            raise FileNotFoundError(
                f"Advanced checkpoint not found: "
                f"{self.checkpoint_path}"
            )


        if not self.operating_points_path.exists():

            raise FileNotFoundError(
                f"Advanced operating-point contract not found: "
                f"{self.operating_points_path}"
            )


        # ----------------------------------------------------
        # DEVICE
        # ----------------------------------------------------

        if device is None:

            self.device = torch.device(
                "cuda"
                if torch.cuda.is_available()
                else
                "cpu"
            )

        else:

            self.device = torch.device(
                device
            )


        # ----------------------------------------------------
        # OPERATING-POINT CONTRACT
        # ----------------------------------------------------

        with open(
            self.operating_points_path,
            "r",
            encoding="utf-8",
        ) as file:

            self.contract = json.load(
                file
            )


        contract_version = self.contract.get(
            "version"
        )

        if (
            contract_version
            !=
            "ADVANCED_OPERATING_POINTS_V2"
        ):

            raise RuntimeError(
                "Unexpected advanced evidence contract: "
                f"{contract_version}"
            )


        contract_labels = self.contract.get(
            "labels",
            []
        )

        if (
            list(
                contract_labels
            )
            !=
            list(
                ADVANCED_LABELS
            )
        ):

            raise RuntimeError(
                "Operating-point label order does not match "
                f"model labels: {ADVANCED_LABELS}"
            )


        self.operating_points = self.contract[
            "operating_points"
        ]


        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device,
            weights_only=False,
        )


        checkpoint_labels = checkpoint.get(
            "labels",
            ADVANCED_LABELS,
        )


        if (
            list(
                checkpoint_labels
            )
            !=
            list(
                ADVANCED_LABELS
            )
        ):

            raise RuntimeError(
                "Checkpoint label order does not match "
                f"expected labels: {ADVANCED_LABELS}"
            )


        self.checkpoint_epoch = int(
            checkpoint.get(
                "epoch",
                -1,
            )
        )


        self.image_size = int(
            checkpoint.get(
                "image_size",
                512,
            )
        )


        self.backbone = str(
            checkpoint.get(
                "backbone",
                "efficientnet_b0",
            )
        )


        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        self.model = AdvancedDREvidenceModel(
            backbone=self.backbone,
            pretrained=False,
        )


        self.model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )


        self.model.to(
            self.device
        )


        self.model.eval()


        # ----------------------------------------------------
        # PREPROCESSING
        # ----------------------------------------------------

        self.transform = (
            get_advanced_eval_transform(
                self.image_size
            )
        )


        # ----------------------------------------------------
        # CONTRACT VALIDATION
        # ----------------------------------------------------

        for label in ADVANCED_LABELS:

            if (
                label
                not in
                self.operating_points
            ):

                raise RuntimeError(
                    f"Missing operating point for {label}"
                )


            alert_threshold = float(
                self.operating_points[
                    label
                ][
                    "alert_threshold"
                ]
            )


            confirm_threshold = float(
                self.operating_points[
                    label
                ][
                    "confirm_threshold"
                ]
            )


            if (
                alert_threshold
                >
                confirm_threshold
            ):

                raise RuntimeError(
                    f"{label}: alert threshold "
                    f"{alert_threshold:.6f} exceeds "
                    f"confirm threshold "
                    f"{confirm_threshold:.6f}"
                )


        print()
        print(
            "AdvancedEvidenceInference ready."
        )

        print(
            f"  Device      : {self.device}"
        )

        print(
            f"  Backbone    : {self.backbone}"
        )

        print(
            f"  Image size  : {self.image_size}"
        )

        print(
            f"  Epoch       : {self.checkpoint_epoch}"
        )

        print(
            f"  Contract    : {contract_version}"
        )


    # ========================================================
    # PREPROCESS
    # ========================================================

    def _prepare_image(
        self,
        image_bgr,
    ):

        if not isinstance(
            image_bgr,
            np.ndarray,
        ):

            raise TypeError(
                "image_bgr must be a NumPy array."
            )


        if (
            image_bgr.ndim
            !=
            3
            or
            image_bgr.shape[2]
            !=
            3
        ):

            raise ValueError(
                "Expected BGR image with shape H x W x 3."
            )


        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB,
        )


        image_rgb = crop_retina(
            image_rgb
        )


        pil_image = Image.fromarray(
            image_rgb
        )


        tensor = self.transform(
            pil_image
        )


        tensor = (
            tensor
            .unsqueeze(
                0
            )
            .to(
                self.device
            )
        )


        return tensor


    # ========================================================
    # EVIDENCE STATE
    # ========================================================

    @staticmethod
    def _state(
        value,
        alert_threshold,
        confirm_threshold,
    ):

        if (
            value
            >=
            confirm_threshold
        ):

            return "CONFIRMED"


        if (
            value
            >=
            alert_threshold
        ):

            return "ALERT_ONLY"


        return "BELOW_ALERT"


    # ========================================================
    # PREDICT NUMPY IMAGE
    # ========================================================

    @torch.no_grad()
    def predict(
        self,
        image_bgr,
    ):

        tensor = self._prepare_image(
            image_bgr
        )


        output = self.model(
            tensor
        )


        probabilities = (
            torch.sigmoid(
                output[
                    "logits"
                ]
            )
            .squeeze(
                0
            )
            .float()
            .cpu()
            .numpy()
        )


        evidence = {}


        for (
            index,
            label
        ) in enumerate(
            ADVANCED_LABELS
        ):

            raw_score = float(
                probabilities[
                    index
                ]
            )


            operating_point = (
                self.operating_points[
                    label
                ]
            )


            alert_threshold = float(
                operating_point[
                    "alert_threshold"
                ]
            )


            confirm_threshold = float(
                operating_point[
                    "confirm_threshold"
                ]
            )


            state = self._state(
                raw_score,
                alert_threshold,
                confirm_threshold,
            )


            evidence[
                label
            ] = {

                # Sigmoid model output.
                # It has NOT undergone probability calibration.
                "probability_raw":
                    raw_score,

                "calibration_status":
                    "UNCALIBRATED_MODEL_SCORE",

                "alert_threshold":
                    alert_threshold,

                "confirm_threshold":
                    confirm_threshold,

                "alert_positive":
                    bool(
                        raw_score
                        >=
                        alert_threshold
                    ),

                "confirmed_positive":
                    bool(
                        raw_score
                        >=
                        confirm_threshold
                    ),

                "state":
                    state,
            }


        any_alert = any(
            item[
                "alert_positive"
            ]
            for item
            in evidence.values()
        )


        any_confirmed = any(
            item[
                "confirmed_positive"
            ]
            for item
            in evidence.values()
        )


        return {

            "version":
                self.VERSION,

            "checkpoint_epoch":
                self.checkpoint_epoch,

            "backbone":
                self.backbone,

            "image_size":
                self.image_size,

            "operating_point_contract":
                self.contract[
                    "version"
                ],

            "operating_point_selection_split":
                self.contract[
                    "selection_split"
                ],

            "test_labels_used_for_threshold_selection":
                bool(
                    self.contract[
                        "test_labels_used_for_selection"
                    ]
                ),

            "evidence":
                evidence,

            "routing_flags": {

                "any_alert":
                    bool(
                        any_alert
                    ),

                "any_confirmed":
                    bool(
                        any_confirmed
                    ),

                "vb_irma_alert":
                    bool(
                        evidence[
                            "VB_IRMA"
                        ][
                            "alert_positive"
                        ]
                    ),

                "vb_irma_confirmed":
                    bool(
                        evidence[
                            "VB_IRMA"
                        ][
                            "confirmed_positive"
                        ]
                    ),

                "nv_alert":
                    bool(
                        evidence[
                            "NV"
                        ][
                            "alert_positive"
                        ]
                    ),

                "nv_confirmed":
                    bool(
                        evidence[
                            "NV"
                        ][
                            "confirmed_positive"
                        ]
                    ),

                "vh_alert":
                    bool(
                        evidence[
                            "VH"
                        ][
                            "alert_positive"
                        ]
                    ),

                "vh_confirmed":
                    bool(
                        evidence[
                            "VH"
                        ][
                            "confirmed_positive"
                        ]
                    ),
            },

            "interpretation": (
                "Advanced retinal evidence model output. "
                "ALERT is an engineering safety-routing signal; "
                "CONFIRMED is stronger model corroboration. "
                "Neither is an autonomous clinical diagnosis."
            ),
        }


    # ========================================================
    # PREDICT FILE
    # ========================================================

    def predict_path(
        self,
        image_path,
    ):

        image_path = Path(
            image_path
        )


        image = cv2.imread(
            str(
                image_path
            )
        )


        if image is None:

            raise RuntimeError(
                f"Could not read image: {image_path}"
            )


        result = self.predict(
            image
        )


        result[
            "image"
        ] = str(
            image_path
        )


        return result