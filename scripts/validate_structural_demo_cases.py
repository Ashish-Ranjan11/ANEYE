from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sih_dr.structure.structural_engine import StructuralRetinaEngine

CASES = [
    ("grade0", "002c21358ce6.png"),
    ("grade1", "0024cdab0c1e.png"),
    ("grade2", "000c1434d8d7.png"),
]

engine = StructuralRetinaEngine()

for label, filename in CASES:

    image = (
        ROOT
        / "datasets"
        / "raw"
        / "APTOS2019"
        / "train_images"
        / filename
    )

    out = (
        ROOT
        / "artifacts"
        / "structure_validation"
        / label
    )

    result = engine.analyze(
        image,
        out
    )

    print()
    print("=" * 65)
    print(label.upper(), filename)
    print("=" * 65)

    print(
        "OPTIC DISC:",
        result["optic_disc"]
    )

    print(
        "FOVEA:",
        result["fovea"]
    )

    print(
        "VESSELS:",
        result["vessels"]
    )

    print(
        "OVERLAY:",
        out / "structural_overlay.png"
    )

print()
print("THREE-CASE STRUCTURAL CHECK COMPLETE")
