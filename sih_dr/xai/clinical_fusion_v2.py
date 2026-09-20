import numpy as np


P_SCORE_VERSION = "P_SCORE_V2"
CONCORDANCE_VERSION = "CONCORDANCE_V2"
T_SCORE_VERSION = "T_SCORE_V2"


def _clip01(value):
    return float(np.clip(float(value), 0.0, 1.0))


def _band(score, high=80.0, moderate=60.0):
    if score >= high:
        return "HIGH"
    if score >= moderate:
        return "MODERATE"
    return "LOW"


# ============================================================
# P-SCORE
# ============================================================

def pathology_score_v2(
    lesions,
    nv_evidence=None,
):
    """
    NetraAI pathology evidence index.

    IMPORTANT:
    - Engineering index, not a clinical DR score.
    - Existing MA/HE/EX/SE weighting is preserved.
    - NV is deliberately NOT folded into the weighted P-score.
      It is exposed separately as advanced evidence.
    """

    ma = _clip01(
        lesions.get(
            "ma_evidence",
            0.0
        )
    )

    he = _clip01(
        lesions.get(
            "he_evidence",
            0.0
        )
    )

    ex = _clip01(
        lesions.get(
            "ex_evidence",
            0.0
        )
    )

    se = _clip01(
        lesions.get(
            "se_evidence",
            0.0
        )
    )

    weighted = (
        0.30 * ma
        + 0.30 * he
        + 0.25 * ex
        + 0.15 * se
    )

    score = round(
        100.0 * _clip01(weighted),
        1
    )

    advanced = {
        "nv_available":
            nv_evidence is not None,

        "nv_evidence":
            None
            if nv_evidence is None
            else round(
                100.0
                * _clip01(nv_evidence),
                1
            ),

        "nv_positive":
            None
            if nv_evidence is None
            else bool(
                _clip01(nv_evidence)
                >= 0.50
            )
    }

    return {
        "version":
            P_SCORE_VERSION,

        "score":
            score,

        "level":
            _band(score),

        "components": {
            "MA":
                round(ma * 100.0, 1),

            "HE":
                round(he * 100.0, 1),

            "EX":
                round(ex * 100.0, 1),

            "SE":
                round(se * 100.0, 1),
        },

        "weights": {
            "MA": 0.30,
            "HE": 0.30,
            "EX": 0.25,
            "SE": 0.15,
        },

        "advanced_evidence":
            advanced,

        "interpretation":
            (
                "Prototype pathology-evidence index; "
                "not an ICDR grade or clinical biomarker."
            )
    }


# ============================================================
# CONCORDANCE
# ============================================================

def grade_evidence_concordance_v2(
    grade,
    lesions,
    nv_evidence=None,
    severe_criteria=None,
):
    """
    Checks whether independently measured retinal evidence
    is compatible with the global ICDR prediction.

    It does NOT overwrite the neural-network grade.

    severe_criteria can later contain:
      {
        "quadrant_he_ma": 0..1,
        "venous_beading": 0..1,
        "irma": 0..1
      }

    Until those are independently measured, Grade 3 evidence
    is intentionally treated conservatively.
    """

    ma = _clip01(
        lesions.get(
            "ma_evidence",
            0.0
        )
    )

    he = _clip01(
        lesions.get(
            "he_evidence",
            0.0
        )
    )

    ex = _clip01(
        lesions.get(
            "ex_evidence",
            0.0
        )
    )

    se = _clip01(
        lesions.get(
            "se_evidence",
            0.0
        )
    )

    nv = (
        None
        if nv_evidence is None
        else _clip01(nv_evidence)
    )

    pathology = max(
        ma,
        he,
        ex,
        se
    )

    support = []
    conflict = []
    limitations = []

    # --------------------------------------------------------
    # GRADE 0
    # --------------------------------------------------------

    if grade == 0:

        score = (
            1.0
            - pathology
        )

        if pathology > 0.45:

            conflict.append(
                "Retinal lesion evidence is present despite a Grade-0 prediction."
            )

        else:

            support.append(
                "No strong independently detected DR-lesion evidence."
            )

    # --------------------------------------------------------
    # GRADE 1
    # --------------------------------------------------------

    elif grade == 1:

        non_ma = max(
            he,
            ex,
            se
        )

        score = (
            0.65 * ma
            +
            0.35
            * (1.0 - non_ma)
        )

        if ma > 0.35:

            support.append(
                "Microaneurysm evidence supports mild NPDR."
            )

        if non_ma > 0.55:

            conflict.append(
                "Additional lesion evidence is stronger than expected for an MA-only mild pattern."
            )

    # --------------------------------------------------------
    # GRADE 2
    # --------------------------------------------------------

    elif grade == 2:

        additional = max(
            he,
            ex,
            se
        )

        score = (
            0.45 * ma
            +
            0.55 * additional
        )

        if ma > 0.30:

            support.append(
                "Microaneurysm evidence detected."
            )

        if he > 0.35:

            support.append(
                "Hemorrhage evidence detected."
            )

        if ex > 0.35:

            support.append(
                "Hard-exudate evidence detected."
            )

        if se > 0.35:

            support.append(
                "Soft-exudate evidence detected."
            )

        if additional < 0.25:

            conflict.append(
                "Weak additional lesion evidence for a moderate-NPDR prediction."
            )

    # --------------------------------------------------------
    # GRADE 3
    # --------------------------------------------------------

    elif grade == 3:

        generic_burden = float(
            np.mean(
                sorted(
                    [
                        ma,
                        he,
                        ex,
                        se
                    ],
                    reverse=True
                )[:3]
            )
        )

        if severe_criteria is None:

            # We currently do NOT independently measure
            # full 4-2-1 criteria.
            #
            # Generic lesion burden can support advanced
            # pathology, but it cannot prove severe NPDR.
            score = min(
                generic_burden,
                0.69
            )

            limitations.append(
                "Full quadrant-aware 4-2-1 evidence is not independently measured."
            )

            if he > 0.55:

                support.append(
                    "High hemorrhagic lesion evidence supports advanced retinal pathology."
                )

            if generic_burden < 0.40:

                conflict.append(
                    "Severe-grade prediction has weak supporting lesion burden."
                )

        else:

            quadrant = _clip01(
                severe_criteria.get(
                    "quadrant_he_ma",
                    0.0
                )
            )

            venous = _clip01(
                severe_criteria.get(
                    "venous_beading",
                    0.0
                )
            )

            irma = _clip01(
                severe_criteria.get(
                    "irma",
                    0.0
                )
            )

            severe_support = max(
                quadrant,
                venous,
                irma
            )

            score = (
                0.45 * generic_burden
                +
                0.55 * severe_support
            )

            if severe_support > 0.50:

                support.append(
                    "Independently measured severe-DR criterion supports the predicted grade."
                )

            else:

                conflict.append(
                    "Independent severe-DR criteria are weak."
                )

    # --------------------------------------------------------
    # GRADE 4
    # --------------------------------------------------------

    else:

        advanced_burden = max(
            he,
            ex,
            se
        )

        if nv is None:

            # Until the independent NV branch exists,
            # Grade 4 MUST remain evidence-incomplete.
            score = min(
                0.45 * pathology,
                0.49
            )

            limitations.append(
                "Independent neovascularization detector is not available."
            )

            conflict.append(
                "PDR prediction cannot be independently supported with NV evidence."
            )

            if advanced_burden > 0.50:

                support.append(
                    "Advanced retinal pathology evidence is present."
                )

        else:

            score = (
                0.70 * nv
                +
                0.30 * advanced_burden
            )

            if nv >= 0.50:

                support.append(
                    "Independent neovascularization evidence supports the PDR prediction."
                )

            else:

                conflict.append(
                    "PDR prediction has weak independent neovascularization evidence."
                )

    score = _clip01(
        score
    )

    score_100 = round(
        score * 100.0,
        1
    )

    # A contradiction must prevent HIGH concordance.
    if (
        score_100 >= 75.0
        and
        not conflict
    ):
        status = "HIGH"

    elif score_100 >= 50.0:
        status = "MODERATE"

    else:
        status = "LOW"

    return {
        "version":
            CONCORDANCE_VERSION,

        "score":
            score_100,

        "status":
            status,

        "supporting_evidence":
            support,

        "conflicting_evidence":
            conflict,

        "limitations":
            limitations,

        "evidence_snapshot": {
            "MA":
                round(ma * 100.0, 1),

            "HE":
                round(he * 100.0, 1),

            "EX":
                round(ex * 100.0, 1),

            "SE":
                round(se * 100.0, 1),

            "NV":
                None
                if nv is None
                else round(
                    nv * 100.0,
                    1
                )
        }
    }


# ============================================================
# T-SCORE
# ============================================================

def trust_score_v2(
    image_reliability,
    calibrated_confidence,
    concordance,
    xai_integrity,
    stability,
):
    """
    NetraAI case-level trust index.

    Inputs MUST all be normalized to 0..1.

    Unlike the old implementation:
    - no default/fixed stability value
    - caller must explicitly provide stability
    - caller should supply calibrated confidence
    """

    image_reliability = _clip01(
        image_reliability
    )

    calibrated_confidence = _clip01(
        calibrated_confidence
    )

    concordance = _clip01(
        concordance
    )

    xai_integrity = _clip01(
        xai_integrity
    )

    stability = _clip01(
        stability
    )

    value = (
        0.25
        * image_reliability

        +
        0.25
        * calibrated_confidence

        +
        0.30
        * concordance

        +
        0.15
        * xai_integrity

        +
        0.05
        * stability
    )

    value = _clip01(
        value
    )

    score = round(
        value * 100.0,
        1
    )

    return {
        "version":
            T_SCORE_VERSION,

        "score":
            score,

        "level":
            _band(score),

        "components": {
            "image_reliability":
                round(
                    image_reliability
                    * 100.0,
                    1
                ),

            "calibrated_confidence":
                round(
                    calibrated_confidence
                    * 100.0,
                    1
                ),

            "concordance":
                round(
                    concordance
                    * 100.0,
                    1
                ),

            "xai_integrity":
                round(
                    xai_integrity
                    * 100.0,
                    1
                ),

            "stability":
                round(
                    stability
                    * 100.0,
                    1
                ),
        },

        "weights": {
            "image_reliability":
                0.25,

            "calibrated_confidence":
                0.25,

            "concordance":
                0.30,

            "xai_integrity":
                0.15,

            "stability":
                0.05,
        },

        "interpretation":
            (
                "Prototype case-level trust index; "
                "not a clinical probability or validated medical score."
            )
    }
