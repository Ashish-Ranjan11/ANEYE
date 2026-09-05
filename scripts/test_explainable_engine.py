from pprint import pprint

from sih_dr.engine.explainable_dr_engine import (
    ExplainableDREngine
)


engine = ExplainableDREngine(
    grader_checkpoint=(
        "checkpoints/sih_dr/grading/"
        "global_final.pth"
    ),

    lesion_checkpoint=(
        "checkpoints/sih_dr/lesions/"
        "lesion_final.pth"
    )
)


result = engine.analyze(
    "datasets/raw/APTOS2019/"
    "train_images/000c1434d8d7.png"
)


print("\n=== TRACE-DR RESULT ===\n")

pprint(result)