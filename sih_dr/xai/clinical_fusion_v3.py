import numpy as np

from sih_dr.xai.clinical_fusion_v2 import (
    grade_evidence_concordance_v2,
)


CONCORDANCE_VERSION = "CONCORDANCE_V3"


# ============================================================
# HELPERS
# ============================================================

def _clip01(value):

    return float(
        np.clip(
            float(value),
            0.0,
            1.0,
        )
    )


def _advanced_item(
    advanced_evidence,
    name,
):

    if advanced_evidence is None:

        return None


    evidence = advanced_evidence.get(
        "evidence",
        {}
    )


    item = evidence.get(
        name
    )


    if not isinstance(
        item,
        dict,
    ):

        return None


    return item


def _state(
    item
):

    if item is None:

        return "UNAVAILABLE"


    state = str(
        item.get(
            "state",
            "UNAVAILABLE",
        )
    ).upper()


    if state not in (
        "CONFIRMED",
        "ALERT_ONLY",
        "BELOW_ALERT",
    ):

        return "UNAVAILABLE"


    return state


def _strength(
    item
):
    """
    Engineering evidence strength.

    IMPORTANT:
    This is NOT calibrated disease probability.

    CONFIRMED:
        Strong model corroboration.

    ALERT_ONLY:
        Safety-routing signal with partial evidence strength.

    BELOW_ALERT:
        No operating-point alert.

    UNAVAILABLE:
        Evidence branch unavailable.
    """

    state = _state(
        item
    )


    if state == "CONFIRMED":

        return 1.0


    if state == "ALERT_ONLY":

        return 0.55


    if state == "BELOW_ALERT":

        return 0.0


    return None


def _raw_score(
    item
):

    if item is None:

        return None


    value = item.get(
        "probability_raw"
    )


    if value is None:

        return None


    return _clip01(
        value
    )


# ============================================================
# CONCORDANCE V3
# ============================================================

def grade_evidence_concordance_v3(
    grade,
    lesions,
    advanced_evidence=None,
):
    """
    NetraAI Concordance V3.

    Extends V2 by incorporating independently trained
    advanced retinal evidence:

        VB_IRMA
        NV
        VH

    IMPORTANT CLAIM LIMITS
    ----------------------
    - Advanced model sigmoid scores are uncalibrated.
    - ALERT / CONFIRMED are engineering operating states.
    - VB_IRMA does NOT establish the full clinical 4-2-1 rule.
    - NV/VH evidence supports review/corroboration but does not
      constitute autonomous diagnosis.
    - Global ICDR prediction is never overwritten here.
    """

    ma = _clip01(
        lesions.get(
            "ma_evidence",
            0.0,
        )
    )

    he = _clip01(
        lesions.get(
            "he_evidence",
            0.0,
        )
    )

    ex = _clip01(
        lesions.get(
            "ex_evidence",
            0.0,
        )
    )

    se = _clip01(
        lesions.get(
            "se_evidence",
            0.0,
        )
    )


    # ========================================================
    # ADVANCED EVIDENCE
    # ========================================================

    vb_item = _advanced_item(
        advanced_evidence,
        "VB_IRMA",
    )

    nv_item = _advanced_item(
        advanced_evidence,
        "NV",
    )

    vh_item = _advanced_item(
        advanced_evidence,
        "VH",
    )


    vb_state = _state(
        vb_item
    )

    nv_state = _state(
        nv_item
    )

    vh_state = _state(
        vh_item
    )


    vb_strength = _strength(
        vb_item
    )

    nv_strength = _strength(
        nv_item
    )

    vh_strength = _strength(
        vh_item
    )


    pathology = max(
        ma,
        he,
        ex,
        se,
    )


    support = []

    conflict = []

    limitations = []


    # ========================================================
    # FALLBACK â€” ADVANCED MODEL UNAVAILABLE
    # ========================================================

    if (
        vb_strength is None
        and
        nv_strength is None
        and
        vh_strength is None
    ):

        result = (
            grade_evidence_concordance_v2(
                grade=grade,
                lesions=lesions,
                nv_evidence=None,
                severe_criteria=None,
            )
        )


        result[
            "version"
        ] = CONCORDANCE_VERSION


        result[
            "limitations"
        ].append(
            "Advanced VB/IRMA, NV and VH evidence unavailable; "
            "Concordance V3 fell back to legacy lesion evidence."
        )


        result[
            "advanced_evidence_snapshot"
        ] = {
            "VB_IRMA": {
                "state":
                    "UNAVAILABLE",
            },

            "NV": {
                "state":
                    "UNAVAILABLE",
            },

            "VH": {
                "state":
                    "UNAVAILABLE",
            },
        }


        return result


    # Missing individual branches are conservative.
    vb_strength_value = (
        0.0
        if vb_strength is None
        else vb_strength
    )

    nv_strength_value = (
        0.0
        if nv_strength is None
        else nv_strength
    )

    vh_strength_value = (
        0.0
        if vh_strength is None
        else vh_strength
    )


    # ========================================================
    # GRADE 0
    # ========================================================

    if grade == 0:

        score = (
            1.0
            -
            pathology
        )


        if pathology > 0.45:

            conflict.append(
                "Retinal lesion evidence is present despite "
                "a Grade-0 prediction."
            )

        else:

            support.append(
                "No strong conventional DR-lesion evidence "
                "supports the Grade-0 prediction."
            )


        if (
            nv_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
            or
            vh_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "Advanced NV/VH evidence is incompatible with "
                "a Grade-0 screening prediction."
            )

            score = min(
                score,
                0.49,
            )


        elif (
            vb_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "VB/IRMA advanced-pattern evidence is present "
                "despite a Grade-0 prediction."
            )

            score = min(
                score,
                0.69,
            )


    # ========================================================
    # GRADE 1
    # ========================================================

    elif grade == 1:

        non_ma = max(
            he,
            ex,
            se,
        )


        score = (
            0.65
            *
            ma
            +
            0.35
            *
            (
                1.0
                -
                non_ma
            )
        )


        if ma > 0.35:

            support.append(
                "Microaneurysm evidence supports mild NPDR."
            )


        if non_ma > 0.55:

            conflict.append(
                "Additional conventional lesion evidence is "
                "stronger than expected for an MA-dominant "
                "mild pattern."
            )


        if (
            nv_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
            or
            vh_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "Advanced NV/VH evidence suggests pathology "
                "beyond a mild-NPDR pattern."
            )

            score = min(
                score,
                0.49,
            )


        elif (
            vb_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "VB/IRMA advanced-pattern evidence may exceed "
                "the expected mild-NPDR pattern."
            )

            score = min(
                score,
                0.69,
            )


    # ========================================================
    # GRADE 2
    # ========================================================

    elif grade == 2:

        additional = max(
            he,
            ex,
            se,
        )


        score = (
            0.45
            *
            ma
            +
            0.55
            *
            additional
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
                "Weak additional lesion evidence for a "
                "moderate-NPDR prediction."
            )


        # NV / VH signals are potentially more advanced
        # than the Grade-2 prediction.
        if (
            nv_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
            or
            vh_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "Advanced NV/VH evidence may indicate disease "
                "beyond the predicted moderate-NPDR grade."
            )

            score = min(
                score,
                0.49,
            )


        if vb_state == "CONFIRMED":

            limitations.append(
                "Strong VB/IRMA model evidence is present, but the "
                "detector is not quadrant-aware and therefore does not "
                "independently establish severe NPDR or contradict "
                "a Grade-2 prediction."
            )


        elif vb_state == "ALERT_ONLY":

            limitations.append(
                "VB/IRMA safety-alert evidence is present. Because "
                "the detector is not quadrant-aware, this alert does "
                "not independently establish severe NPDR."
            )



    # ========================================================
    # GRADE 3 â€” SEVERE NPDR
    # ========================================================

    elif grade == 3:

        generic_burden = float(
            np.mean(
                sorted(
                    [
                        ma,
                        he,
                        ex,
                        se,
                    ],
                    reverse=True,
                )[
                    :3
                ]
            )
        )


        score = (
            0.55
            *
            generic_burden
            +
            0.45
            *
            vb_strength_value
        )


        # We still do NOT independently measure
        # full quadrant-aware 4-2-1 criteria.
        #
        # Therefore V3 intentionally cannot claim
        # HIGH concordance for Grade 3 solely from
        # this branch.
        score = min(
            score,
            0.74,
        )


        limitations.append(
            "VB/IRMA evidence does not independently establish "
            "the complete quadrant-aware clinical 4-2-1 rule."
        )


        if vb_state == "CONFIRMED":

            support.append(
                "Strong independent VB/IRMA model evidence "
                "supports an advanced non-proliferative pattern."
            )


        elif vb_state == "ALERT_ONLY":

            support.append(
                "VB/IRMA safety-alert evidence provides partial "
                "support for an advanced non-proliferative pattern."
            )


        else:

            if generic_burden < 0.40:

                conflict.append(
                    "Severe-grade prediction has weak conventional "
                    "lesion burden and no VB/IRMA alert evidence."
                )


        # Grade 3 versus possible proliferative evidence.
        if (
            nv_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
            or
            vh_state
            in (
                "ALERT_ONLY",
                "CONFIRMED",
            )
        ):

            conflict.append(
                "NV/VH advanced evidence may indicate proliferative "
                "pathology beyond a Grade-3 prediction."
            )

            score = min(
                score,
                0.49,
            )


    # ========================================================
    # GRADE 4 â€” PDR
    # ========================================================

    else:

        advanced_burden = max(
            he,
            ex,
            se,
        )


        score = (
            0.70
            *
            nv_strength_value
            +
            0.15
            *
            vh_strength_value
            +
            0.15
            *
            advanced_burden
        )


        if nv_state == "CONFIRMED":

            support.append(
                "Strong independent neovascularization model "
                "evidence supports the Grade-4 prediction."
            )


        elif nv_state == "ALERT_ONLY":

            support.append(
                "Neovascularization safety-alert evidence is "
                "present but does not meet the stronger "
                "confirmation operating point."
            )

            limitations.append(
                "NV evidence is ALERT_ONLY; PDR support requires "
                "human review."
            )

            score = min(
                score,
                0.69,
            )


        else:

            conflict.append(
                "Grade-4 prediction has no independent NV "
                "safety-alert evidence."
            )

            score = min(
                score,
                0.49,
            )


        if vh_state == "CONFIRMED":

            support.append(
                "Strong vitreous-hemorrhage model evidence "
                "supports advanced proliferative pathology."
            )


        elif vh_state == "ALERT_ONLY":

            support.append(
                "Vitreous-hemorrhage safety-alert evidence "
                "provides additional advanced-pathology support."
            )


        if advanced_burden > 0.50:

            support.append(
                "Conventional lesion burden also supports "
                "advanced retinal pathology."
            )


    # ========================================================
    # FINAL SCORE
    # ========================================================

    score = _clip01(
        score
    )


    score_100 = round(
        score
        *
        100.0,
        1,
    )


    if (
        score_100
        >=
        75.0
        and
        not conflict
    ):

        status = "HIGH"


    elif score_100 >= 50.0:

        status = "MODERATE"


    else:

        status = "LOW"


    # ========================================================
    # SERIALIZABLE ADVANCED SNAPSHOT
    # ========================================================

    advanced_snapshot = {}


    for (
        name,
        item,
    ) in (
        (
            "VB_IRMA",
            vb_item,
        ),
        (
            "NV",
            nv_item,
        ),
        (
            "VH",
            vh_item,
        ),
    ):

        if item is None:

            advanced_snapshot[
                name
            ] = {
                "state":
                    "UNAVAILABLE",

                "raw_score":
                    None,

                "calibration_status":
                    None,
            }

        else:

            advanced_snapshot[
                name
            ] = {
                "state":
                    _state(
                        item
                    ),

                "raw_score":
                    None
                    if _raw_score(
                        item
                    ) is None
                    else round(
                        _raw_score(
                            item
                        ),
                        6,
                    ),

                "calibration_status":
                    item.get(
                        "calibration_status"
                    ),

                "alert_threshold":
                    item.get(
                        "alert_threshold"
                    ),

                "confirm_threshold":
                    item.get(
                        "confirm_threshold"
                    ),
            }


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
                round(
                    ma
                    *
                    100.0,
                    1,
                ),

            "HE":
                round(
                    he
                    *
                    100.0,
                    1,
                ),

            "EX":
                round(
                    ex
                    *
                    100.0,
                    1,
                ),

            "SE":
                round(
                    se
                    *
                    100.0,
                    1,
                ),
        },

        "advanced_evidence_snapshot":
            advanced_snapshot,

        "interpretation":
            (
                "Engineering concordance index comparing the "
                "global ICDR prediction with independently "
                "measured conventional and advanced retinal "
                "evidence. It is not a clinical probability "
                "or autonomous diagnosis."
            ),
    }
