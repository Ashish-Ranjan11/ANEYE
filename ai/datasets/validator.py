from pathlib import Path
from PIL import Image
import cv2
import numpy as np


class ImageValidator:

    def __init__(self):
        pass

    def validate(self, image_path):

        result = {
            "valid": True,
            "width": None,
            "height": None,
            "channels": None,
            "blur_score": None,
            "brightness": None,
            "contrast": None,
            "error": None
        }

        try:

            image = Image.open(image_path)

            width, height = image.size

            result["width"] = width
            result["height"] = height

            img = cv2.imread(str(image_path))

            if img is None:

                result["valid"] = False
                result["error"] = "Unreadable image"

                return result

            result["channels"] = img.shape[2]

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            result["blur_score"] = cv2.Laplacian(
                gray,
                cv2.CV_64F
            ).var()

            result["brightness"] = np.mean(gray)

            result["contrast"] = np.std(gray)

        except Exception as e:

            result["valid"] = False

            result["error"] = str(e)

        return result