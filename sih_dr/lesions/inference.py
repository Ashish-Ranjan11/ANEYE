from pathlib import Path

import cv2
import numpy as np
import torch
import segmentation_models_pytorch as smp


LESION_NAMES = ["MA", "HE", "EX", "SE"]

# BGR colors for OpenCV
LESION_COLORS = {
    "MA": (0, 0, 255),       # red
    "HE": (255, 80, 0),      # blue
    "EX": (0, 255, 255),     # yellow
    "SE": (255, 255, 0),     # cyan
}


class LesionInferenceEngine:

    def __init__(
        self,
        checkpoint_path,
        device=None,
        tile_size=512,
        stride=256,
        thresholds=None,
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

        self.tile_size = tile_size
        self.stride = stride

        # Start with same threshold used for validation.
        self.thresholds = thresholds or {
            "MA": 0.50,
            "HE": 0.50,
            "EX": 0.50,
            "SE": 0.50,
        }

        print("Loading lesion checkpoint:", checkpoint_path)

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device
        )

        # EXACT training architecture
        self.model = smp.Unet(
            encoder_name="efficientnet-b0",
            encoder_weights=None,
            in_channels=3,
            classes=4,
            activation=None,
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.to(self.device)
        self.model.eval()

        print(
            "Lesion model loaded | "
            f"epoch={checkpoint.get('epoch')} | "
            f"macro_dice={checkpoint.get('macro_dice')}"
        )

    # -------------------------------------------------------
    # PREPROCESS
    # -------------------------------------------------------

    @staticmethod
    def _normalize(tile_rgb):

        x = tile_rgb.astype(np.float32) / 255.0

        mean = np.array(
            [0.485, 0.456, 0.406],
            dtype=np.float32
        )

        std = np.array(
            [0.229, 0.224, 0.225],
            dtype=np.float32
        )

        x = (x - mean) / std

        x = np.transpose(
            x,
            (2, 0, 1)
        )

        return torch.from_numpy(x).float()

    # -------------------------------------------------------
    # RETINAL MASK
    # -------------------------------------------------------

    @staticmethod
    def retinal_mask(image_bgr):

        gray = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2GRAY
        )

        mask = (
            gray > 12
        ).astype(np.uint8)

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            np.ones((25, 25), np.uint8)
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:

            largest = max(
                contours,
                key=cv2.contourArea
            )

            clean = np.zeros_like(mask)

            cv2.drawContours(
                clean,
                [largest],
                -1,
                1,
                thickness=-1
            )

            mask = clean

        return mask

    # -------------------------------------------------------
    # TILE POSITIONS
    # -------------------------------------------------------

    def _positions(
        self,
        length
    ):

        if length <= self.tile_size:
            return [0]

        positions = list(
            range(
                0,
                length - self.tile_size + 1,
                self.stride
            )
        )

        last = (
            length
            - self.tile_size
        )

        if positions[-1] != last:
            positions.append(last)

        return positions

    # -------------------------------------------------------
    # FULL-RETINA INFERENCE
    # -------------------------------------------------------

    @torch.no_grad()
    def predict(
        self,
        image_bgr
    ):

        if image_bgr is None:
            raise ValueError(
                "Invalid retinal image"
            )

        original_h, original_w = (
            image_bgr.shape[:2]
        )

        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB
        )

        retina_mask = self.retinal_mask(
            image_bgr
        )

        # Pad only if dimensions are smaller than tile.
        pad_h = max(
            0,
            self.tile_size - original_h
        )

        pad_w = max(
            0,
            self.tile_size - original_w
        )

        if pad_h or pad_w:

            image_rgb = cv2.copyMakeBorder(
                image_rgb,
                0,
                pad_h,
                0,
                pad_w,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0)
            )

            retina_mask = cv2.copyMakeBorder(
                retina_mask,
                0,
                pad_h,
                0,
                pad_w,
                cv2.BORDER_CONSTANT,
                value=0
            )

        h, w = image_rgb.shape[:2]

        probability_sum = np.zeros(
            (4, h, w),
            dtype=np.float32
        )

        coverage = np.zeros(
            (h, w),
            dtype=np.float32
        )

        ys = self._positions(h)
        xs = self._positions(w)

        total_tiles = len(ys) * len(xs)

        used_tiles = 0

        print(
            f"Full retina: {original_w}x{original_h}"
        )

        print(
            f"Tiles available: {total_tiles}"
        )

        for y in ys:

            for x in xs:

                tile_mask = retina_mask[
                    y:y+self.tile_size,
                    x:x+self.tile_size
                ]

                retinal_fraction = (
                    np.count_nonzero(tile_mask)
                    / tile_mask.size
                )

                # Skip tiles almost entirely outside retina
                if retinal_fraction < 0.05:
                    continue

                tile = image_rgb[
                    y:y+self.tile_size,
                    x:x+self.tile_size
                ]

                tensor = (
                    self._normalize(tile)
                    .unsqueeze(0)
                    .to(
                        self.device,
                        non_blocking=True
                    )
                )

                with torch.autocast(
                    device_type="cuda",
                    dtype=torch.float16,
                    enabled=(
                        self.device.type
                        == "cuda"
                    ),
                ):

                    logits = self.model(
                        tensor
                    )

                    probs = torch.sigmoid(
                        logits
                    )

                probs = (
                    probs[0]
                    .float()
                    .cpu()
                    .numpy()
                )

                probability_sum[
                    :,
                    y:y+self.tile_size,
                    x:x+self.tile_size
                ] += probs

                coverage[
                    y:y+self.tile_size,
                    x:x+self.tile_size
                ] += 1.0

                used_tiles += 1

        print(
            f"Tiles processed: {used_tiles}"
        )

        # Avoid division by zero
        valid_coverage = np.maximum(
            coverage,
            1.0
        )

        probabilities = (
            probability_sum
            / valid_coverage[None, :, :]
        )

        # Remove anything outside retinal FOV
        probabilities *= (
            retina_mask[None, :, :]
        )

        # Restore original image dimensions
        probabilities = probabilities[
            :,
            :original_h,
            :original_w
        ]

        retina_mask = retina_mask[
            :original_h,
            :original_w
        ]

        masks = np.zeros_like(
            probabilities,
            dtype=np.uint8
        )

        for i, name in enumerate(
            LESION_NAMES
        ):

            masks[i] = (
                probabilities[i]
                >= self.thresholds[name]
            ).astype(np.uint8)

        evidence = self._extract_evidence(
            probabilities,
            masks,
            retina_mask
        )

        return {
            "probabilities":
                probabilities,

            "masks":
                masks,

            "retina_mask":
                retina_mask,

            "evidence":
                evidence,

            "tiles_processed":
                used_tiles
        }

    # -------------------------------------------------------
    # LESION EVIDENCE
    # -------------------------------------------------------

    def _extract_evidence(
        self,
        probabilities,
        masks,
        retina_mask
    ):

        retina_pixels = max(
            int(retina_mask.sum()),
            1
        )

        results = {}

        # Minimum connected region sizes.
        #
        # Keep MA extremely small because they are tiny.
        min_component_area = {
            "MA": 2,
            "HE": 4,
            "EX": 4,
            "SE": 4,
        }

        for i, name in enumerate(
            LESION_NAMES
        ):

            mask = masks[i].copy()

            probability = (
                probabilities[i]
            )

            num_labels, labels, stats, centroids = (
                cv2.connectedComponentsWithStats(
                    mask,
                    connectivity=8
                )
            )

            components = []

            filtered_mask = np.zeros_like(
                mask
            )

            for component_id in range(
                1,
                num_labels
            ):

                area = int(
                    stats[
                        component_id,
                        cv2.CC_STAT_AREA
                    ]
                )

                if (
                    area
                    <
                    min_component_area[name]
                ):
                    continue

                component_pixels = (
                    labels
                    == component_id
                )

                confidence = float(
                    probability[
                        component_pixels
                    ].mean()
                )

                peak_confidence = float(
                    probability[
                        component_pixels
                    ].max()
                )

                cx, cy = centroids[
                    component_id
                ]

                filtered_mask[
                    component_pixels
                ] = 1

                components.append({
                    "x":
                        round(float(cx), 1),

                    "y":
                        round(float(cy), 1),

                    "area_px":
                        area,

                    "confidence":
                        round(confidence, 4),

                    "peak_confidence":
                        round(
                            peak_confidence,
                            4
                        )
                })

            masks[i][:] = (
                filtered_mask
            )

            pixel_area = int(
                filtered_mask.sum()
            )

            lesion_fraction = (
                pixel_area
                / retina_pixels
            )

            if pixel_area > 0:

                mean_confidence = float(
                    probability[
                        filtered_mask > 0
                    ].mean()
                )

                peak = float(
                    probability[
                        filtered_mask > 0
                    ].max()
                )

            else:

                mean_confidence = 0.0
                peak = 0.0

            # Evidence is NOT merely number of lesions.
            #
            # combines:
            # confidence
            # presence
            # relative burden
            burden_component = np.clip(
                lesion_fraction * 1000.0,
                0.0,
                1.0
            )

            presence_component = min(
                len(components) / 5.0,
                1.0
            )

            evidence_score = (
                0.55 * mean_confidence
                +
                0.25 * burden_component
                +
                0.20 * presence_component
            )

            evidence_score = float(
                np.clip(
                    evidence_score,
                    0,
                    1
                )
            )

            components.sort(
                key=lambda item:
                    item[
                        "peak_confidence"
                    ],
                reverse=True
            )

            results[name] = {
                "count":
                    len(components),

                "area_px":
                    pixel_area,

                "retinal_area_fraction":
                    round(
                        lesion_fraction,
                        7
                    ),

                "mean_confidence":
                    round(
                        mean_confidence,
                        4
                    ),

                "peak_confidence":
                    round(
                        peak,
                        4
                    ),

                "evidence":
                    round(
                        evidence_score,
                        4
                    ),

                # strongest candidates only
                "components":
                    components
            }

        return results


# -------------------------------------------------------
# VISUAL OVERLAY
# -------------------------------------------------------

def create_lesion_overlay(
    image_bgr,
    masks,
    alpha=0.45
):

    output = image_bgr.copy()

    for i, name in enumerate(
        LESION_NAMES
    ):

        mask = (
            masks[i] > 0
        )

        if not np.any(mask):
            continue

        layer = np.zeros_like(
            output
        )

        layer[mask] = (
            LESION_COLORS[name]
        )

        output = cv2.addWeighted(
            output,
            1.0,
            layer,
            alpha,
            0
        )

    return output


def draw_lesion_contours(
    image_bgr,
    masks
):

    output = image_bgr.copy()

    for i, name in enumerate(
        LESION_NAMES
    ):

        binary = (
            masks[i] * 255
        ).astype(np.uint8)

        contours, _ = (
            cv2.findContours(
                binary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
        )

        cv2.drawContours(
            output,
            contours,
            -1,
            LESION_COLORS[name],
            1
        )

    return output