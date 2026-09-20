from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sih_dr.xai.clinical_fusion_v2 import (
    pathology_score_v2,
    grade_evidence_concordance_v2,
    trust_score_v2,
)


print("\n=== NETRAAI FUSION V2 SMOKE TEST ===")


# Current Grade-2 reference-case lesion evidence
lesions = {
    "ma_evidence": 0.8389,
    "he_evidence": 0.9206,
    "ex_evidence": 0.9514,
    "se_evidence": 0.0,
}


p = pathology_score_v2(
    lesions,
    nv_evidence=None,
)


c = grade_evidence_concordance_v2(
    grade=2,
    lesions=lesions,
    nv_evidence=None,
)


# TEMPORARY ONLY:
# raw confidence + placeholder stability are used here
# just to smoke-test the V2 calculation.
# Both will be replaced by real calibrated confidence
# and measured stability next.
t = trust_score_v2(
    image_reliability=0.6168,
    calibrated_confidence=0.8653,
    concordance=c["score"] / 100.0,
    xai_integrity=0.509,
    stability=0.90,
)


print("\nP-SCORE:")
print(p)

print("\nCONCORDANCE:")
print(c)

print("\nT-SCORE:")
print(t)


print("\n--- GRADE 4 WITHOUT NV ---")

c4_missing_nv = (
    grade_evidence_concordance_v2(
        grade=4,
        lesions=lesions,
        nv_evidence=None,
    )
)

print(c4_missing_nv)


print("\n--- GRADE 4 WITH STRONG NV ---")

c4_nv = (
    grade_evidence_concordance_v2(
        grade=4,
        lesions=lesions,
        nv_evidence=0.91,
    )
)

print(c4_nv)


print("\n=== TEST COMPLETE ===")
