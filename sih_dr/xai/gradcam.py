import cv2
import numpy as np
import torch


class GlobalDRGradCAM:
    """
    Grad-CAM for the EfficientNet global DR branch.
    Uses the final convolutional feature block.
    """

    def __init__(self, model):
        self.model = model

        self.activations = None
        self.gradients = None

        # timm EfficientNet-B0 final convolution
        self.target_layer = model.encoder.conv_head

        self.forward_handle = self.target_layer.register_forward_hook(
            self._forward_hook
        )

        self.backward_handle = self.target_layer.register_full_backward_hook(
            self._backward_hook
        )

    def _forward_hook(self, module, inputs, output):
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, image_tensor, class_idx=None):
        """
        image_tensor:
            [1, 3, H, W]

        class_idx:
            ICDR class 0-4.
            If None, uses predicted grade.
        """

        self.model.eval()

        self.model.zero_grad(set_to_none=True)

        output = self.model(image_tensor)

        logits = output["grade_logits"]

        if class_idx is None:
            class_idx = int(
                logits.argmax(dim=1).item()
            )

        score = logits[0, class_idx]

        score.backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError(
                "Grad-CAM hooks did not capture activations/gradients."
            )

        # Global-average-pool gradients
        weights = self.gradients.mean(
            dim=(2, 3),
            keepdim=True
        )

        cam = (
            weights * self.activations
        ).sum(dim=1)

        cam = torch.relu(cam)

        cam = cam[0].cpu().numpy()

        cam -= cam.min()

        max_value = cam.max()

        if max_value > 0:
            cam /= max_value

        return {
            "class_idx": class_idx,
            "heatmap": cam
        }

    def close(self):
        self.forward_handle.remove()
        self.backward_handle.remove()


def resize_heatmap(heatmap, width, height):
    return cv2.resize(
        heatmap,
        (width, height),
        interpolation=cv2.INTER_CUBIC
    )


def create_gradcam_overlay(
    image_bgr,
    heatmap,
    alpha=0.40
):
    h, w = image_bgr.shape[:2]

    heatmap = resize_heatmap(
        heatmap,
        w,
        h
    )

    heatmap_uint8 = np.uint8(
        np.clip(heatmap, 0, 1) * 255
    )

    colored = cv2.applyColorMap(
        heatmap_uint8,
        cv2.COLORMAP_JET
    )

    overlay = cv2.addWeighted(
        image_bgr,
        1.0 - alpha,
        colored,
        alpha,
        0
    )

    return overlay


def attribution_in_fov(
    heatmap,
    fundus_mask
):
    """
    Fraction of total attribution that lies inside the retinal FOV.
    """

    h, w = fundus_mask.shape[:2]

    hm = resize_heatmap(
        heatmap,
        w,
        h
    )

    mask = (
        fundus_mask > 0
    ).astype(np.float32)

    total = float(hm.sum()) + 1e-8

    inside = float(
        (hm * mask).sum()
    )

    return float(
        np.clip(
            inside / total,
            0,
            1
        )
    )


def lesion_attribution_overlap(
    heatmap,
    lesion_mask
):
    """
    Measures how much Grad-CAM attribution falls on predicted lesion regions.

    This is an XAI-integrity indicator, not proof of causal faithfulness.
    """

    h, w = lesion_mask.shape[:2]

    hm = resize_heatmap(
        heatmap,
        w,
        h
    )

    lesion = (
        lesion_mask > 0
    ).astype(np.float32)

    total = float(
        hm.sum()
    ) + 1e-8

    overlap = float(
        (hm * lesion).sum()
    )

    return float(
        np.clip(
            overlap / total,
            0,
            1
        )
    )