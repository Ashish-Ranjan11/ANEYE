import numpy as np


GRADE_NAMES = {
    0: "No apparent DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


def pathology_score(lesions):
    """
    Prototype evidence score.

    Inputs are normalized lesion evidence values 0..1.
    This is a transparent system-derived index, not a clinical score.
    """

    ma = float(lesions.get("ma_evidence", 0.0))
    he = float(lesions.get("he_evidence", 0.0))
    ex = float(lesions.get("ex_evidence", 0.0))
    se = float(lesions.get("se_evidence", 0.0))

    score = (
        0.30 * ma
        + 0.30 * he
        + 0.25 * ex
        + 0.15 * se
    )

    return round(
        100 * float(np.clip(score, 0, 1)),
        1
    )


def grade_evidence_concordance(grade, lesions):
    ma = float(lesions.get("ma_evidence", 0.0))
    he = float(lesions.get("he_evidence", 0.0))
    ex = float(lesions.get("ex_evidence", 0.0))
    se = float(lesions.get("se_evidence", 0.0))

    pathology = max(ma, he, ex, se)

    support = []
    conflict = []

    if grade == 0:
        score = 1.0 - pathology

        if pathology > 0.45:
            conflict.append(
                "Lesion evidence detected despite predicted No DR"
            )

    elif grade == 1:
        score = (
            0.65 * ma
            + 0.35 * (1.0 - max(he, ex, se))
        )

        if ma > 0.35:
            support.append("Microaneurysm evidence supports mild NPDR")

        if max(he, ex, se) > 0.55:
            conflict.append(
                "Additional lesion burden exceeds expected mild pattern"
            )

    elif grade == 2:
        additional = max(he, ex, se)

        score = (
            0.45 * ma
            + 0.55 * additional
        )

        if ma > 0.30:
            support.append("Microaneurysm evidence detected")

        if he > 0.35:
            support.append("Hemorrhage evidence detected")

        if ex > 0.35:
            support.append("Hard exudate evidence detected")

        if additional < 0.25:
            conflict.append(
                "Weak supporting lesion evidence for moderate NPDR"
            )

    elif grade == 3:
        burden = np.mean(
            sorted([ma, he, ex, se], reverse=True)[:3]
        )

        score = float(burden)

        if he > 0.55:
            support.append("High hemorrhage burden")

        if burden < 0.40:
            conflict.append(
                "Advanced grade with weak lesion burden"
            )

    else:
        # Current lesion branch has no independently supervised NV output.
        burden = max(ma, he, ex, se)

        score = 0.55 * burden

        support.append(
            "Advanced retinal pathology evidence present"
        )

        conflict.append(
            "Neovascularization evidence not independently supervised; specialist verification required"
        )

    score = float(np.clip(score, 0, 1))

    if score >= 0.75 and not conflict:
        status = "HIGH"
    elif score >= 0.50:
        status = "MODERATE"
    else:
        status = "LOW"

    return {
        "score": round(score * 100, 1),
        "status": status,
        "supporting_evidence": support,
        "conflicting_evidence": conflict
    }


def trust_score(
    image_reliability,
    calibrated_confidence,
    concordance,
    xai_integrity,
    stability=0.90,
):
    """
    Transparent prototype trust index.
    """

    value = (
        0.25 * image_reliability
        + 0.25 * calibrated_confidence
        + 0.30 * concordance
        + 0.15 * xai_integrity
        + 0.05 * stability
    )

    value = float(np.clip(value, 0, 1))

    score = round(value * 100, 1)

    if score >= 80:
        level = "HIGH"
    elif score >= 60:
        level = "MODERATE"
    else:
        level = "LOW"

    return {
        "score": score,
        "level": level
    }