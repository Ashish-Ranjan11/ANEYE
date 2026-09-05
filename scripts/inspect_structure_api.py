from pathlib import Path
import json

path = Path(
    "artifacts/netraai_structure_api.json"
)

data = json.loads(
    path.read_text(
        encoding="utf-8"
    )
)

print()
print("=" * 70)
print("NETRAAI STRUCTURAL API RESULT")
print("=" * 70)

structure = data.get(
    "structure",
    {}
)

print()
print(
    "STATUS:",
    structure.get("status")
)

print()
print(
    "OPTIC DISC:"
)
print(
    json.dumps(
        structure.get(
            "optic_disc"
        ),
        indent=2
    )
)

print()
print(
    "FOVEA:"
)
print(
    json.dumps(
        structure.get(
            "fovea"
        ),
        indent=2
    )
)

print()
print(
    "VESSELS:"
)
print(
    json.dumps(
        structure.get(
            "vessels"
        ),
        indent=2
    )
)

print()
print(
    "ARTIFACTS:"
)
print(
    json.dumps(
        data.get(
            "artifacts",
            {}
        ),
        indent=2
    )
)
