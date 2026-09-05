import cv2
import numpy as np


class FundusQualityEngine:

    @staticmethod
    def _clip01(x):
        return float(np.clip(x, 0.0, 1.0))

    def _retina_mask(self, image_bgr):
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

        mask = (gray > 15).astype(np.uint8) * 255

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            np.ones((21, 21), np.uint8)
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return mask

        largest = max(contours, key=cv2.contourArea)

        clean = np.zeros_like(mask)

        cv2.drawContours(
            clean,
            [largest],
            -1,
            255,
            thickness=-1
        )

        return clean

    def analyze(self, image_bgr):

        if image_bgr is None:
            raise ValueError("Invalid image")

        gray = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2GRAY
        )

        mask = self._retina_mask(image_bgr)

        pixels = gray[mask > 0]

        if len(pixels) < 100:
            return {
                "status": "UNGRADEABLE",
                "score": 0.0,
                "focus": 0.0,
                "illumination": 0.0,
                "contrast": 0.0,
                "fov": 0.0,
                "reasons": ["Retinal field not detected"],
                "raw": {}
            }

        green = image_bgr[:, :, 1]

        lap = cv2.Laplacian(
            green,
            cv2.CV_64F
        )

        lap_values = lap[mask > 0]

        lap_var = float(
            np.var(lap_values)
        )

        focus = (
            np.log1p(lap_var)
            - np.log1p(2.0)
        ) / (
            np.log1p(80.0)
            - np.log1p(2.0)
        )

        focus = self._clip01(focus)

        mean_lum = float(
            np.mean(pixels)
        )

        illumination = 1.0 - (
            abs(mean_lum - 95.0) / 95.0
        )

        illumination = self._clip01(
            illumination
        )

        contrast_raw = float(
            np.std(pixels)
        )

        contrast = self._clip01(
            contrast_raw / 45.0
        )

        fov_fraction = float(
            np.count_nonzero(mask)
        ) / mask.size

        fov = self._clip01(
            fov_fraction / 0.55
        )

        quality_score = (
            0.25 * focus
            + 0.30 * illumination
            + 0.20 * contrast
            + 0.25 * fov
        )

        reasons = []

        if focus < 0.25:
            reasons.append(
                "Reduced retinal sharpness"
            )

        if illumination < 0.35:
            reasons.append(
                "Poor illumination"
            )

        if contrast < 0.25:
            reasons.append(
                "Low retinal contrast"
            )

        if fov < 0.50:
            reasons.append(
                "Incomplete retinal field"
            )

        critical_failure = (
            fov < 0.35
            or illumination < 0.18
        )

        if critical_failure:
            status = "UNGRADEABLE"

        elif (
            quality_score >= 0.55
            and focus >= 0.20
        ):
            status = "GRADEABLE"

        else:
            status = "BORDERLINE"

        return {
            "status": status,
            "score": round(quality_score, 4),
            "focus": round(focus, 4),
            "illumination": round(illumination, 4),
            "contrast": round(contrast, 4),
            "fov": round(fov, 4),
            "reasons": reasons,
            "raw": {
                "laplacian_variance": round(lap_var, 3),
                "mean_luminance": round(mean_lum, 3),
                "contrast_std": round(contrast_raw, 3),
                "retinal_fov_fraction": round(fov_fraction, 3)
            }
        }


def enhance_borderline(image_bgr):

    lab = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2LAB
    )

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=1.8,
        tileGridSize=(8, 8)
    )

    l2 = clahe.apply(l)

    enhanced = cv2.merge(
        [l2, a, b]
    )

    return cv2.cvtColor(
        enhanced,
        cv2.COLOR_LAB2BGR
    )