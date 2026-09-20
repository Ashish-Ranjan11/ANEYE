import cv2
import numpy as np

from sih_dr.xai.gradcam import (
    GlobalDRGradCAM,
    resize_heatmap,
)


class StabilityEvaluator:
    """
    NetraAI benign-perturbation stability evaluator.

    Measures:
      1. ICDR grade consistency
      2. RDR route consistency
      3. calibrated RDR probability stability
      4. Grad-CAM spatial stability

    This is an engineering reliability test,
    not a clinical validation metric.
    """

    VERSION = "STABILITY_V1"


    def __init__(
        self,
        calibrated_global_engine
    ):

        self.engine = (
            calibrated_global_engine
        )

        self.gradcam = GlobalDRGradCAM(
            self.engine.model
        )


    @staticmethod
    def _brightness(
        image,
        factor,
    ):

        result = (
            image
            .astype(
                np.float32
            )
            *
            factor
        )

        return np.clip(
            result,
            0,
            255
        ).astype(
            np.uint8
        )


    @staticmethod
    def _rotate(
        image,
        angle,
    ):

        h, w = image.shape[
            :2
        ]

        center = (
            w / 2.0,
            h / 2.0
        )

        matrix = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0,
        )

        return cv2.warpAffine(
            image,
            matrix,
            (
                w,
                h
            ),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(
                0,
                0,
                0
            ),
        )


    @staticmethod
    def _jpeg(
        image,
        quality=90,
    ):

        success, encoded = (
            cv2.imencode(
                ".jpg",
                image,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    quality
                ],
            )
        )

        if not success:

            raise RuntimeError(
                "JPEG perturbation failed"
            )

        decoded = cv2.imdecode(
            encoded,
            cv2.IMREAD_COLOR,
        )

        return decoded


    def _perturbations(
        self,
        image
    ):

        return [
            {
                "name":
                    "brightness_minus_10",

                "image":
                    self._brightness(
                        image,
                        0.90,
                    ),

                "rotation":
                    0.0,
            },

            {
                "name":
                    "brightness_plus_10",

                "image":
                    self._brightness(
                        image,
                        1.10,
                    ),

                "rotation":
                    0.0,
            },

            {
                "name":
                    "rotation_minus_2",

                "image":
                    self._rotate(
                        image,
                        -2.0,
                    ),

                "rotation":
                    -2.0,
            },

            {
                "name":
                    "rotation_plus_2",

                "image":
                    self._rotate(
                        image,
                        2.0,
                    ),

                "rotation":
                    2.0,
            },

            {
                "name":
                    "jpeg_q90",

                "image":
                    self._jpeg(
                        image,
                        90,
                    ),

                "rotation":
                    0.0,
            },
        ]


    @staticmethod
    def _cam_similarity(
        base_heatmap,
        other_heatmap,
        inverse_rotation=0.0,
        size=384,
    ):

        base = resize_heatmap(
            base_heatmap,
            size,
            size,
        ).astype(
            np.float32
        )

        other = resize_heatmap(
            other_heatmap,
            size,
            size,
        ).astype(
            np.float32
        )

        if abs(
            inverse_rotation
        ) > 1e-6:

            center = (
                size / 2.0,
                size / 2.0
            )

            matrix = (
                cv2.getRotationMatrix2D(
                    center,
                    inverse_rotation,
                    1.0,
                )
            )

            other = cv2.warpAffine(
                other,
                matrix,
                (
                    size,
                    size
                ),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )

        a = base.reshape(
            -1
        )

        b = other.reshape(
            -1
        )

        denominator = (
            np.linalg.norm(
                a
            )
            *
            np.linalg.norm(
                b
            )
        )

        if denominator <= 1e-12:

            if (
                np.linalg.norm(a)
                <= 1e-12
                and
                np.linalg.norm(b)
                <= 1e-12
            ):
                return 1.0

            return 0.0

        similarity = float(
            np.dot(
                a,
                b
            )
            /
            denominator
        )

        return float(
            np.clip(
                similarity,
                0.0,
                1.0,
            )
        )


    def evaluate(
        self,
        image_bgr,
    ):

        base = self.engine.predict(
            image_bgr
        )

        base_grade = int(
            base[
                "grade"
            ]
        )

        base_rdr = float(
            base[
                "rdr_probability_calibrated"
            ]
        )

        base_route = bool(
            base[
                "referable_dr"
            ]
        )

        base_cam = (
            self.gradcam.generate(
                base[
                    "tensor"
                ],
                class_idx=
                    base_grade,
            )[
                "heatmap"
            ]
        )

        rows = []

        grade_matches = []
        route_matches = []
        rdr_deltas = []
        cam_similarities = []


        for item in self._perturbations(
            image_bgr
        ):

            result = (
                self.engine.predict(
                    item[
                        "image"
                    ]
                )
            )

            grade = int(
                result[
                    "grade"
                ]
            )

            rdr = float(
                result[
                    "rdr_probability_calibrated"
                ]
            )

            route = bool(
                result[
                    "referable_dr"
                ]
            )

            perturbed_cam = (
                self.gradcam.generate(
                    result[
                        "tensor"
                    ],
                    class_idx=
                        base_grade,
                )[
                    "heatmap"
                ]
            )

            # Undo image rotation before CAM comparison.
            cam_similarity = (
                self._cam_similarity(
                    base_cam,
                    perturbed_cam,
                    inverse_rotation=
                        -float(
                            item[
                                "rotation"
                            ]
                        ),
                )
            )

            grade_match = (
                grade
                ==
                base_grade
            )

            route_match = (
                route
                ==
                base_route
            )

            rdr_delta = abs(
                rdr
                -
                base_rdr
            )

            grade_matches.append(
                float(
                    grade_match
                )
            )

            route_matches.append(
                float(
                    route_match
                )
            )

            rdr_deltas.append(
                float(
                    rdr_delta
                )
            )

            cam_similarities.append(
                float(
                    cam_similarity
                )
            )

            rows.append({
                "perturbation":
                    item[
                        "name"
                    ],

                "grade":
                    grade,

                "grade_match":
                    grade_match,

                "rdr_probability_calibrated":
                    round(
                        rdr,
                        6
                    ),

                "rdr_absolute_delta":
                    round(
                        rdr_delta,
                        6
                    ),

                "referable_dr":
                    route,

                "route_match":
                    route_match,

                "gradcam_similarity":
                    round(
                        cam_similarity,
                        4
                    ),
            })


        grade_consistency = float(
            np.mean(
                grade_matches
            )
        )

        route_consistency = float(
            np.mean(
                route_matches
            )
        )

        mean_rdr_delta = float(
            np.mean(
                rdr_deltas
            )
        )

        rdr_probability_stability = float(
            np.clip(
                1.0
                -
                mean_rdr_delta,
                0.0,
                1.0,
            )
        )

        gradcam_stability = float(
            np.mean(
                cam_similarities
            )
        )


        stability = float(
            np.mean([
                grade_consistency,
                route_consistency,
                rdr_probability_stability,
                gradcam_stability,
            ])
        )


        score = round(
            stability
            * 100.0,
            1
        )


        if score >= 80.0:

            level = "HIGH"

        elif score >= 60.0:

            level = "MODERATE"

        else:

            level = "LOW"


        return {
            "version":
                self.VERSION,

            "score":
                score,

            "level":
                level,

            "base": {
                "grade":
                    base_grade,

                "rdr_probability_calibrated":
                    round(
                        base_rdr,
                        6
                    ),

                "referable_dr":
                    base_route,
            },

            "components": {
                "grade_consistency":
                    round(
                        grade_consistency
                        * 100.0,
                        1
                    ),

                "rdr_route_consistency":
                    round(
                        route_consistency
                        * 100.0,
                        1
                    ),

                "rdr_probability_stability":
                    round(
                        rdr_probability_stability
                        * 100.0,
                        1
                    ),

                "gradcam_stability":
                    round(
                        gradcam_stability
                        * 100.0,
                        1
                    ),

                "mean_rdr_absolute_delta":
                    round(
                        mean_rdr_delta,
                        6
                    ),
            },

            "perturbations":
                rows,

            "interpretation":
                (
                    "Prototype benign-transform "
                    "case stability index; "
                    "not a clinical validation metric."
                ),
        }


    def close(
        self
    ):

        self.gradcam.close()
