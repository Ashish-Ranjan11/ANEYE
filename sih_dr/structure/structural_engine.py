from pathlib import Path
import cv2
import numpy as np


class StructuralRetinaEngine:
    """
    Lightweight structural retinal analysis for the NetraAI MVP.

    Outputs:
      - retinal FOV mask
      - optic-disc localization
      - fovea anatomical estimate
      - retinal-vessel mask
      - vessel density
      - annotated structural overlay

    IMPORTANT:
      This is a prototype structural-localization module.
      It is not presented as clinically validated anatomical segmentation.
    """

    def __init__(self, max_side=1400):
        self.max_side = max_side


    # -------------------------------------------------------
    # RESIZE
    # -------------------------------------------------------

    def _resize_for_analysis(self, image):
        h, w = image.shape[:2]

        scale = min(
            1.0,
            self.max_side / max(h, w)
        )

        if scale == 1.0:
            return image.copy(), 1.0

        resized = cv2.resize(
            image,
            (
                int(round(w * scale)),
                int(round(h * scale))
            ),
            interpolation=cv2.INTER_AREA
        )

        return resized, scale


    # -------------------------------------------------------
    # RETINAL FIELD MASK
    # -------------------------------------------------------

    def _retina_mask(self, image):
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (9, 9),
            0
        )

        # Separate retinal field from dark fundus-camera border.
        _, mask = cv2.threshold(
            gray,
            8,
            255,
            cv2.THRESH_BINARY
        )

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (15, 15)
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2
        )

        # Retain largest component only.
        n, labels, stats, _ = (
            cv2.connectedComponentsWithStats(
                mask,
                connectivity=8
            )
        )

        if n <= 1:
            return mask

        largest = (
            1 +
            np.argmax(
                stats[1:, cv2.CC_STAT_AREA]
            )
        )

        final = np.zeros_like(mask)

        final[
            labels == largest
        ] = 255

        return final


    # -------------------------------------------------------
    # OPTIC DISC
    # -------------------------------------------------------

    def _optic_disc(self, image, retina_mask):
        h, w = image.shape[:2]

        # Optic disc is generally strongly represented
        # in a smoothed red-channel brightness map.
        red = image[:, :, 2]

        smooth = cv2.GaussianBlur(
            red,
            (0, 0),
            sigmaX=max(7, min(h, w) * 0.012)
        )

        valid = (
            retina_mask > 0
        )

        values = smooth[valid]

        if values.size == 0:
            return None

        threshold = np.percentile(
            values,
            97.5
        )

        candidate = np.zeros_like(red)

        candidate[
            (smooth >= threshold)
            & valid
        ] = 255

        kernel_size = max(
            7,
            int(
                min(h, w) * 0.012
            )
        )

        if kernel_size % 2 == 0:
            kernel_size += 1

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (
                kernel_size,
                kernel_size
            )
        )

        candidate = cv2.morphologyEx(
            candidate,
            cv2.MORPH_CLOSE,
            kernel
        )

        contours, _ = cv2.findContours(
            candidate,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        best = None
        best_score = -1.0

        retina_area = max(
            1,
            np.count_nonzero(valid)
        )

        for contour in contours:
            area = cv2.contourArea(
                contour
            )

            if area <= 0:
                continue

            area_fraction = (
                area / retina_area
            )

            # Reject tiny bright lesions and huge regions.
            if not (
                0.0005
                <= area_fraction
                <= 0.05
            ):
                continue

            perimeter = cv2.arcLength(
                contour,
                True
            )

            if perimeter <= 0:
                continue

            circularity = (
                4.0
                * np.pi
                * area
                / (perimeter ** 2)
            )

            M = cv2.moments(
                contour
            )

            if M["m00"] == 0:
                continue

            cx = (
                M["m10"]
                / M["m00"]
            )

            cy = (
                M["m01"]
                / M["m00"]
            )

            contour_mask = np.zeros_like(
                red
            )

            cv2.drawContours(
                contour_mask,
                [contour],
                -1,
                255,
                -1
            )

            mean_brightness = float(
                smooth[
                    contour_mask > 0
                ].mean()
            ) / 255.0

            # Optic disc tends to be:
            # - bright
            # - fairly compact/circular
            # - large enough not to be an exudate speck
            score = (
                0.65
                * mean_brightness
                +
                0.35
                * np.clip(
                    circularity,
                    0,
                    1
                )
            )

            if score > best_score:
                best_score = score

                equivalent_radius = np.sqrt(
                    area / np.pi
                )

                best = {
                    "center_x": float(cx),
                    "center_y": float(cy),
                    "radius": float(
                        equivalent_radius
                    ),
                    "confidence": float(
                        np.clip(
                            score,
                            0,
                            1
                        )
                    )
                }


        # Fallback: maximum of heavily smoothed red channel
        if best is None:

            masked = smooth.copy()

            masked[
                retina_mask == 0
            ] = 0

            _, max_val, _, max_loc = (
                cv2.minMaxLoc(
                    masked
                )
            )

            cx, cy = max_loc

            best = {
                "center_x": float(cx),
                "center_y": float(cy),
                "radius": float(
                    min(h, w) * 0.045
                ),
                "confidence": float(
                    np.clip(
                        max_val / 255.0
                        * 0.55,
                        0,
                        0.55
                    )
                )
            }

        return best


    # -------------------------------------------------------
    # FOVEA ESTIMATE
    # -------------------------------------------------------

    def _fovea_from_disc(
        self,
        disc,
        image_shape
    ):
        h, w = image_shape[:2]

        cx = disc["center_x"]
        cy = disc["center_y"]

        diameter = max(
            disc["radius"] * 2.0,
            min(h, w) * 0.06
        )

        # Determine temporal direction from optic-disc position.
        #
        # Disc on right side of image:
        # fovea expected to its left.
        #
        # Disc on left side:
        # fovea expected to its right.
        temporal_direction = (
            -1
            if cx > w / 2
            else 1
        )

        fx = (
            cx
            +
            temporal_direction
            * 2.5
            * diameter
        )

        # Fovea is commonly slightly inferior
        # to optic-disc center.
        fy = (
            cy
            +
            0.25
            * diameter
        )

        fx = float(
            np.clip(
                fx,
                0,
                w - 1
            )
        )

        fy = float(
            np.clip(
                fy,
                0,
                h - 1
            )
        )

        confidence = float(
            np.clip(
                disc["confidence"]
                * 0.65,
                0,
                0.70
            )
        )

        return {
            "center_x": fx,
            "center_y": fy,
            "confidence": confidence,
            "method":
                "DISC_RELATIVE_ANATOMICAL_ESTIMATE"
        }


    # -------------------------------------------------------
    # VESSEL SEGMENTATION
    # -------------------------------------------------------

    def _vessels(
        self,
        image,
        retina_mask,
        optic_disc
    ):
        h, w = image.shape[:2]

        # Green channel usually gives strongest vessel/background
        # contrast in colour fundus photography.
        green = image[:, :, 1]

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(
            green
        )

        # Multi-scale black-hat vessel enhancement.
        responses = []

        for size in (9, 15, 25):

            kernel = (
                cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (size, size)
                )
            )

            blackhat = (
                cv2.morphologyEx(
                    enhanced,
                    cv2.MORPH_BLACKHAT,
                    kernel
                )
            )

            responses.append(
                blackhat
            )

        vessel_response = np.maximum.reduce(
            responses
        )

        # Add local background subtraction.
        background = cv2.GaussianBlur(
            enhanced,
            (0, 0),
            sigmaX=7
        )

        local_dark = cv2.subtract(
            background,
            enhanced
        )

        vessel_response = cv2.addWeighted(
            vessel_response,
            0.72,
            local_dark,
            0.28,
            0
        )

        vessel_response = cv2.normalize(
            vessel_response,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)

        # Remove FOV boundary where false vessel responses occur.
        boundary_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (15, 15)
        )

        inner_retina = cv2.erode(
            retina_mask,
            boundary_kernel,
            iterations=2
        )

        valid_values = vessel_response[
            inner_retina > 0
        ]

        if valid_values.size == 0:
            return (
                np.zeros_like(
                    vessel_response
                ),
                {
                    "density": 0.0,
                    "confidence": 0.0
                }
            )

        # Otsu threshold from retinal pixels only.
        otsu_input = (
            valid_values
            .reshape(-1, 1)
            .astype(np.uint8)
        )

        threshold, _ = cv2.threshold(
            otsu_input,
            0,
            255,
            cv2.THRESH_BINARY
            + cv2.THRESH_OTSU
        )

        # Avoid an overly permissive Otsu threshold.
        percentile_threshold = np.percentile(
            valid_values,
            72
        )

        final_threshold = max(
            threshold * 0.90,
            percentile_threshold
        )

        vessels = np.zeros_like(
            vessel_response
        )

        vessels[
            (vessel_response >= final_threshold)
            &
            (inner_retina > 0)
        ] = 255

        # Morphological cleanup.
        small_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (3, 3)
        )

        vessels = cv2.morphologyEx(
            vessels,
            cv2.MORPH_OPEN,
            small_kernel
        )

        vessels = cv2.morphologyEx(
            vessels,
            cv2.MORPH_CLOSE,
            small_kernel
        )

        # Remove tiny connected components.
        n, labels, stats, _ = (
            cv2.connectedComponentsWithStats(
                vessels,
                connectivity=8
            )
        )

        filtered = np.zeros_like(
            vessels
        )

        min_component = max(
            12,
            int(
                h * w * 0.00001
            )
        )

        for component_id in range(
            1,
            n
        ):

            area = int(
                stats[
                    component_id,
                    cv2.CC_STAT_AREA
                ]
            )

            if area >= min_component:
                filtered[
                    labels
                    ==
                    component_id
                ] = 255

        retina_pixels = max(
            1,
            np.count_nonzero(
                retina_mask
            )
        )

        vessel_pixels = np.count_nonzero(
            filtered
        )

        density = float(
            vessel_pixels
            / retina_pixels
        )

        # Heuristic reliability indicator.
        # Typical plausible vessel masks should not cover
        # almost none or most of the retina.
        if 0.02 <= density <= 0.25:
            confidence = 0.75
        elif 0.01 <= density <= 0.35:
            confidence = 0.55
        else:
            confidence = 0.30

        return (
            filtered,
            {
                "density": round(
                    density,
                    5
                ),
                "pixel_count":
                    int(vessel_pixels),
                "confidence":
                    confidence,
                "method":
                    "GREEN_CHANNEL_CLAHE_MULTI_SCALE_MORPHOLOGY"
            }
        )


    # -------------------------------------------------------
    # PUBLIC ANALYSIS
    # -------------------------------------------------------

    def analyze(
        self,
        image_path,
        output_dir=None
    ):

        image_path = Path(
            image_path
        )

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            raise ValueError(
                f"Could not read image: {image_path}"
            )

        original_h, original_w = (
            image.shape[:2]
        )

        working, scale = (
            self._resize_for_analysis(
                image
            )
        )

        retina_mask = (
            self._retina_mask(
                working
            )
        )

        disc = self._optic_disc(
            working,
            retina_mask
        )

        fovea = self._fovea_from_disc(
            disc,
            working.shape
        )

        vessels, vessel_info = (
            self._vessels(
                working,
                retina_mask,
                disc
            )
        )

        inv_scale = (
            1.0 / scale
        )

        # Convert structural coordinates back
        # to original full-retina coordinates.
        disc_full = {
            "center_x":
                round(
                    disc["center_x"]
                    * inv_scale,
                    1
                ),

            "center_y":
                round(
                    disc["center_y"]
                    * inv_scale,
                    1
                ),

            "radius_px":
                round(
                    disc["radius"]
                    * inv_scale,
                    1
                ),

            "confidence":
                round(
                    disc["confidence"],
                    3
                ),

            "method":
                "BRIGHTNESS_CIRCULARITY_PROTOTYPE"
        }

        fovea_full = {
            "center_x":
                round(
                    fovea["center_x"]
                    * inv_scale,
                    1
                ),

            "center_y":
                round(
                    fovea["center_y"]
                    * inv_scale,
                    1
                ),

            "confidence":
                round(
                    fovea["confidence"],
                    3
                ),

            "method":
                fovea["method"]
        }


        # ---------------------------------------------------
        # FULL-RES VESSEL MASK
        # ---------------------------------------------------

        vessel_full = cv2.resize(
            vessels,
            (
                original_w,
                original_h
            ),
            interpolation=
                cv2.INTER_NEAREST
        )


        artifacts = {}

        if output_dir is not None:

            output_dir = Path(
                output_dir
            )

            output_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            vessel_path = (
                output_dir
                / "vessel_mask.png"
            )

            cv2.imwrite(
                str(vessel_path),
                vessel_full
            )


            # -----------------------------------------------
            # STRUCTURAL OVERLAY
            # -----------------------------------------------

            overlay = image.copy()

            vessel_color = np.zeros_like(
                overlay
            )

            vessel_color[
                vessel_full > 0
            ] = (
                255,
                220,
                40
            )

            overlay = cv2.addWeighted(
                overlay,
                1.0,
                vessel_color,
                0.48,
                0
            )

            dc = (
                int(
                    disc_full["center_x"]
                ),
                int(
                    disc_full["center_y"]
                )
            )

            dr = int(
                disc_full["radius_px"]
            )

            cv2.circle(
                overlay,
                dc,
                dr,
                (
                    0,
                    255,
                    255
                ),
                max(
                    2,
                    original_w // 900
                )
            )

            cv2.putText(
                overlay,
                "OPTIC DISC",
                (
                    dc[0] + dr + 10,
                    dc[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                max(
                    0.55,
                    original_w / 4500
                ),
                (
                    0,
                    255,
                    255
                ),
                max(
                    1,
                    original_w // 1600
                ),
                cv2.LINE_AA
            )


            fc = (
                int(
                    fovea_full["center_x"]
                ),
                int(
                    fovea_full["center_y"]
                )
            )

            cross = max(
                18,
                original_w // 90
            )

            cv2.line(
                overlay,
                (
                    fc[0] - cross,
                    fc[1]
                ),
                (
                    fc[0] + cross,
                    fc[1]
                ),
                (
                    255,
                    70,
                    230
                ),
                max(
                    2,
                    original_w // 1000
                )
            )

            cv2.line(
                overlay,
                (
                    fc[0],
                    fc[1] - cross
                ),
                (
                    fc[0],
                    fc[1] + cross
                ),
                (
                    255,
                    70,
                    230
                ),
                max(
                    2,
                    original_w // 1000
                )
            )

            cv2.putText(
                overlay,
                "FOVEA EST.",
                (
                    fc[0] + cross + 10,
                    fc[1]
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                max(
                    0.55,
                    original_w / 4500
                ),
                (
                    255,
                    70,
                    230
                ),
                max(
                    1,
                    original_w // 1600
                ),
                cv2.LINE_AA
            )


            overlay_path = (
                output_dir
                / "structural_overlay.png"
            )

            cv2.imwrite(
                str(overlay_path),
                overlay
            )

            artifacts = {
                "vessel_mask":
                    str(vessel_path),

                "structural_overlay":
                    str(overlay_path)
            }


        retina_coverage = float(
            np.count_nonzero(
                retina_mask
            )
            / retina_mask.size
        )

        return {
            "status":
                "STRUCTURAL_PROTOTYPE",

            "image_width":
                original_w,

            "image_height":
                original_h,

            "retinal_fov": {
                "coverage":
                    round(
                        retina_coverage,
                        4
                    )
            },

            "optic_disc":
                disc_full,

            "fovea":
                fovea_full,

            "vessels":
                vessel_info,

            "artifacts":
                artifacts,

            "limitations": [
                "Optic-disc localization is prototype image-processing localization.",
                "Fovea position is an anatomical estimate relative to the detected optic disc.",
                "Vessel mask is classical image-processing segmentation and is not yet clinically validated."
            ]
        }
