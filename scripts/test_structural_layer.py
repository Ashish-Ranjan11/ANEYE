from pathlib import Path
import sys
import json

# Add ANEYE repository root to Python import path
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sih_dr.structure.structural_engine import (
    StructuralRetinaEngine
)

IMAGE = ROOT / "datasets" / "raw" / "APTOS2019" / "train_images" / "000c1434d8d7.png"

OUT = ROOT / "artifacts" / "structure_test"

engine = StructuralRetinaEngine()

result = engine.analyze(
    IMAGE,
    OUT
)

print(
    json.dumps(
        result,
        indent=2
    )
)

print()
print("=" * 60)
print("STRUCTURAL TEST COMPLETE")
print("=" * 60)

print(
    "Optic Disc:",
    result.get("optic_disc")
)

print(
    "Fovea:",
    result.get("fovea")
)

print(
    "Vessels:",
    result.get("vessels")
)

print()
print(
    "Overlay:",
    OUT / "structural_overlay.png"
)

print(
    "Vessel mask:",
    OUT / "vessel_mask.png"
)
