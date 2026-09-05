from pathlib import Path
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, white, black


PAGE_W, PAGE_H = A4

# ---------------------------------------------------------
# BRAND / COLORS
# ---------------------------------------------------------

NAVY = HexColor("#0B1F33")
BLUE = HexColor("#2563EB")
CYAN = HexColor("#0891B2")
GREEN = HexColor("#059669")
AMBER = HexColor("#D97706")
RED = HexColor("#DC2626")
PURPLE = HexColor("#7C3AED")

LIGHT_BLUE = HexColor("#EFF6FF")
LIGHT_CYAN = HexColor("#ECFEFF")
LIGHT_GREEN = HexColor("#ECFDF5")
LIGHT_AMBER = HexColor("#FFFBEB")
LIGHT_RED = HexColor("#FEF2F2")
LIGHT_GRAY = HexColor("#F5F7FA")

MID_GRAY = HexColor("#64748B")
DARK_GRAY = HexColor("#334155")
LINE = HexColor("#D9E2EC")


GRADE_NAMES = {
    0: "No apparent DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}


GRADE_SHORT = [
    "Grade 0",
    "Grade 1",
    "Grade 2",
    "Grade 3",
    "Grade 4",
]


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def _resolve(path):
    if not path:
        return None

    p = Path(path)

    if p.exists():
        return p

    root = Path.cwd()

    candidate = root / p

    if candidate.exists():
        return candidate

    return None


def _fit_image(c, path, x, y, w, h):
    path = _resolve(path)

    if path is None:
        c.setFillColor(LIGHT_GRAY)
        c.rect(x, y, w, h, fill=1, stroke=0)

        c.setFillColor(MID_GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            x + w / 2,
            y + h / 2,
            "Image unavailable"
        )
        return

    try:
        img = ImageReader(str(path))
        iw, ih = img.getSize()

        scale = min(
            w / iw,
            h / ih
        )

        nw = iw * scale
        nh = ih * scale

        c.drawImage(
            img,
            x + (w - nw) / 2,
            y + (h - nh) / 2,
            nw,
            nh,
            preserveAspectRatio=True,
            mask="auto"
        )

    except Exception:
        c.setFillColor(LIGHT_GRAY)
        c.rect(x, y, w, h, fill=1, stroke=0)


def _text(
    c,
    text,
    x,
    y,
    width_chars=90,
    font="Helvetica",
    size=8,
    color=DARK_GRAY,
    leading=None,
    max_lines=None,
):
    if text is None:
        return y

    if leading is None:
        leading = size + 3

    lines = []

    for paragraph in str(text).split("\n"):
        lines.extend(
            wrap(
                paragraph,
                width=width_chars
            )
            or [""]
        )

    if max_lines:
        lines = lines[:max_lines]

    c.setFont(
        font,
        size
    )

    c.setFillColor(
        color
    )

    yy = y

    for line in lines:
        c.drawString(
            x,
            yy,
            line
        )
        yy -= leading

    return yy


def _section_title(
    c,
    title,
    y
):
    c.setFillColor(NAVY)
    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        34,
        y,
        title
    )

    c.setStrokeColor(LINE)

    c.line(
        34,
        y - 6,
        PAGE_W - 34,
        y - 6
    )

    return y - 22


def _header(
    c,
    page_title,
    page_number,
    case_id
):
    c.setFillColor(NAVY)

    c.rect(
        0,
        PAGE_H - 74,
        PAGE_W,
        74,
        fill=1,
        stroke=0
    )

    c.setFillColor(white)

    c.setFont(
        "Helvetica-Bold",
        19
    )

    c.drawString(
        34,
        PAGE_H - 33,
        "NetraAI"
    )

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        34,
        PAGE_H - 50,
        "TRACE-DR Explainable Retinal Screening"
    )

    c.setFont(
        "Helvetica",
        8
    )

    c.drawRightString(
        PAGE_W - 34,
        PAGE_H - 31,
        page_title
    )

    c.drawRightString(
        PAGE_W - 34,
        PAGE_H - 46,
        f"Case: {case_id}"
    )

    c.drawRightString(
        PAGE_W - 34,
        PAGE_H - 60,
        f"Page {page_number} of 4"
    )


def _footer(c):
    c.setStrokeColor(LINE)

    c.line(
        34,
        38,
        PAGE_W - 34,
        38
    )

    c.setFillColor(MID_GRAY)

    c.setFont(
        "Helvetica-Oblique",
        6.5
    )

    c.drawCentredString(
        PAGE_W / 2,
        25,
        "NetraAI is a research screening decision-support prototype and is not a definitive autonomous clinical diagnosis."
    )

    c.drawCentredString(
        PAGE_W / 2,
        15,
        "P-Score and T-Score are transparent prototype indices and are not established clinical scoring systems."
    )


def _metric_card(
    c,
    x,
    y,
    w,
    h,
    title,
    value,
    subtitle="",
    fill=LIGHT_GRAY,
    value_color=NAVY,
):
    c.setFillColor(fill)

    c.roundRect(
        x,
        y,
        w,
        h,
        7,
        fill=1,
        stroke=0
    )

    c.setFillColor(MID_GRAY)

    c.setFont(
        "Helvetica-Bold",
        7
    )

    c.drawString(
        x + 9,
        y + h - 15,
        title.upper()
    )

    c.setFillColor(
        value_color
    )

    c.setFont(
        "Helvetica-Bold",
        13
    )

    c.drawString(
        x + 9,
        y + h - 34,
        str(value)
    )

    if subtitle:
        c.setFillColor(MID_GRAY)

        c.setFont(
            "Helvetica",
            6.5
        )

        c.drawString(
            x + 9,
            y + 8,
            str(subtitle)[:44]
        )


def _horizontal_bar(
    c,
    x,
    y,
    w,
    label,
    value,
    max_value=100.0,
    suffix="%",
    bar_color=BLUE,
):
    value = float(value or 0)

    ratio = 0

    if max_value > 0:
        ratio = max(
            0,
            min(
                value / max_value,
                1
            )
        )

    c.setFillColor(DARK_GRAY)

    c.setFont(
        "Helvetica-Bold",
        7
    )

    c.drawString(
        x,
        y + 7,
        label
    )

    c.setFillColor(
        LIGHT_GRAY
    )

    c.roundRect(
        x + 92,
        y,
        w - 140,
        12,
        5,
        fill=1,
        stroke=0
    )

    if ratio > 0:
        c.setFillColor(
            bar_color
        )

        c.roundRect(
            x + 92,
            y,
            (w - 140) * ratio,
            12,
            5,
            fill=1,
            stroke=0
        )

    c.setFillColor(
        DARK_GRAY
    )

    c.setFont(
        "Helvetica-Bold",
        7
    )

    c.drawRightString(
        x + w,
        y + 3,
        f"{value:.1f}{suffix}"
    )


def _vertical_bar_chart(
    c,
    x,
    y,
    w,
    h,
    labels,
    values,
    title,
    suffix="",
    max_value=None,
):
    values = [
        float(v or 0)
        for v in values
    ]

    if max_value is None:
        max_value = max(
            max(values, default=1),
            1
        )

    c.setFillColor(NAVY)

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        x,
        y + h + 10,
        title
    )

    plot_h = h - 25

    c.setStrokeColor(LINE)

    c.line(
        x + 24,
        y + 19,
        x + w,
        y + 19
    )

    n = max(
        len(values),
        1
    )

    gap = 9

    available = (
        w - 35 - gap * (n - 1)
    )

    bar_w = available / n

    for i, (
        label,
        value
    ) in enumerate(
        zip(
            labels,
            values
        )
    ):
        bx = (
            x
            + 28
            + i * (
                bar_w + gap
            )
        )

        ratio = min(
            value / max_value,
            1
        )

        bh = (
            plot_h - 32
        ) * ratio

        c.setFillColor(
            BLUE
        )

        c.roundRect(
            bx,
            y + 20,
            bar_w,
            max(
                bh,
                1
            ),
            3,
            fill=1,
            stroke=0
        )

        c.setFillColor(
            DARK_GRAY
        )

        c.setFont(
            "Helvetica-Bold",
            6.5
        )

        c.drawCentredString(
            bx + bar_w / 2,
            y + 8,
            label
        )

        c.setFont(
            "Helvetica",
            6
        )

        c.drawCentredString(
            bx + bar_w / 2,
            y + 23 + bh,
            f"{value:.2f}{suffix}"
        )


def _decision_box(
    c,
    x,
    y,
    w,
    title,
    description,
    status_color,
):
    c.setFillColor(
        LIGHT_GRAY
    )

    c.roundRect(
        x,
        y,
        w,
        56,
        6,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        status_color
    )

    c.roundRect(
        x,
        y,
        7,
        56,
        4,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        8
    )

    c.drawString(
        x + 16,
        y + 38,
        title
    )

    _text(
        c,
        description,
        x + 16,
        y + 25,
        width_chars=58,
        size=6.7,
        leading=8,
        max_lines=3
    )


# ---------------------------------------------------------
# CLINICAL EXPLANATION
# ---------------------------------------------------------

def _build_reasoning(result):
    prediction = (
        result.get(
            "prediction"
        )
        or {}
    )

    lesions = (
        result.get(
            "lesions"
        )
        or {}
    )

    concordance = (
        result.get(
            "concordance"
        )
        or {}
    )

    trust = (
        result.get(
            "t_score"
        )
        or {}
    )

    xai = (
        result.get(
            "xai_integrity"
        )
        or {}
    )

    grade = prediction.get(
        "icdr_grade"
    )

    grade_name = prediction.get(
        "grade_name",
        GRADE_NAMES.get(
            grade,
            "Unknown"
        )
    )

    rdr = prediction.get(
        "referable_dr",
        False
    )

    detected = []

    lesion_full = {
        "MA":
            "microaneurysm",
        "HE":
            "hemorrhage",
        "EX":
            "hard exudate",
        "SE":
            "soft exudate",
    }

    for key, human in (
        lesion_full.items()
    ):
        info = lesions.get(
            key,
            {}
        )

        if (
            info.get(
                "count",
                0
            )
            > 0
        ):
            detected.append(
                human
            )

    if detected:
        lesion_text = (
            ", ".join(
                detected
            )
        )
    else:
        lesion_text = (
            "no thresholded lesion regions"
        )

    summary = (
        f"NetraAI classified the retinal image as ICDR Grade {grade} "
        f"({grade_name}). The referable-DR branch returned "
        f"{'a positive' if rdr else 'a negative'} screening result. "
        f"Local lesion analysis identified {lesion_text}. "
        f"Pathology-grade concordance was {concordance.get('status', 'unknown')} "
        f"at {concordance.get('score', '-')}%. "
        f"The resulting TRACE-DR trust assessment was "
        f"{trust.get('level', 'unknown')} at {trust.get('score', '-')} / 100."
    )

    integrity = (
        f"Grad-CAM attribution remained {xai.get('attribution_in_retinal_fov', '-')}% "
        f"inside the detected retinal field of view, while "
        f"{xai.get('attribution_lesion_overlap', '-')}% of the attribution overlapped "
        f"the segmented lesion regions. This yields an XAI integrity score of "
        f"{xai.get('score', '-')} / 100. Low attribution-lesion overlap does not "
        f"automatically reverse the prediction; instead, it reduces explanation "
        f"reliability and is surfaced to the reviewer."
    )

    return summary, integrity


# ---------------------------------------------------------
# PAGE 1
# ---------------------------------------------------------

def _page_overview(
    c,
    result,
    original_image_path
):
    case_id = result.get(
        "case_id",
        "-"
    )

    _header(
        c,
        "Screening Overview",
        1,
        case_id
    )

    prediction = (
        result.get(
            "prediction"
        )
        or {}
    )

    quality = (
        result.get(
            "quality"
        )
        or {}
    )

    recommendation = (
        result.get(
            "recommendation"
        )
        or {}
    )

    summary, _ = (
        _build_reasoning(
            result
        )
    )

    y = PAGE_H - 100

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        13
    )

    c.drawString(
        34,
        y,
        "Retinal Screening Summary"
    )

    y -= 20

    # Original image
    img_x = 34
    img_y = 405
    img_w = 255
    img_h = 280

    c.setFillColor(
        LIGHT_GRAY
    )

    c.roundRect(
        img_x,
        img_y,
        img_w,
        img_h,
        7,
        fill=1,
        stroke=0
    )

    _fit_image(
        c,
        original_image_path,
        img_x + 7,
        img_y + 7,
        img_w - 14,
        img_h - 14
    )

    # right metrics
    rx = 308
    rw = PAGE_W - rx - 34

    grade = prediction.get(
        "icdr_grade",
        "-"
    )

    grade_name = prediction.get(
        "grade_name",
        "-"
    )

    _metric_card(
        c,
        rx,
        622,
        rw,
        63,
        "Predicted ICDR grade",
        f"Grade {grade}",
        grade_name,
        fill=LIGHT_BLUE,
        value_color=BLUE
    )

    _metric_card(
        c,
        rx,
        548,
        rw,
        63,
        "Referable DR",
        "YES"
        if prediction.get(
            "referable_dr"
        )
        else "NO",
        f"Probability: {100 * float(prediction.get('rdr_probability', 0)):.2f}%",
        fill=(
            LIGHT_RED
            if prediction.get(
                "referable_dr"
            )
            else LIGHT_GREEN
        ),
        value_color=(
            RED
            if prediction.get(
                "referable_dr"
            )
            else GREEN
        )
    )

    _metric_card(
        c,
        rx,
        474,
        rw,
        63,
        "Model confidence",
        f"{100 * float(prediction.get('grade_confidence', 0)):.2f}%",
        "Raw model confidence - temperature calibration not yet applied",
        fill=LIGHT_CYAN,
        value_color=CYAN
    )

    _metric_card(
        c,
        rx,
        400,
        rw,
        63,
        "Image quality",
        quality.get(
            "status",
            "-"
        ),
        f"Reliability score: {100 * float(quality.get('score', 0)):.2f}%",
        fill=LIGHT_GREEN,
        value_color=GREEN
    )

    # Recommendation
    y2 = 372

    c.setFillColor(
        LIGHT_RED
        if recommendation.get(
            "priority"
        ) == "HIGH"
        else LIGHT_AMBER
    )

    c.roundRect(
        34,
        y2,
        PAGE_W - 68,
        72,
        7,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        RED
        if recommendation.get(
            "priority"
        ) == "HIGH"
        else AMBER
    )

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        46,
        y2 + 50,
        "NETRAAI SCREENING ACTION"
    )

    c.setFont(
        "Helvetica-Bold",
        14
    )

    c.drawString(
        46,
        y2 + 30,
        recommendation.get(
            "action",
            "-"
        )
    )

    _text(
        c,
        recommendation.get(
            "reason",
            "-"
        ),
        46,
        y2 + 15,
        width_chars=90,
        size=7,
        color=DARK_GRAY,
        max_lines=1
    )

    y3 = _section_title(
        c,
        "Automated Clinical Rationale",
        338
    )

    _text(
        c,
        summary,
        34,
        y3,
        width_chars=112,
        size=8.3,
        leading=12,
        max_lines=7
    )

    # Quality breakdown
    y4 = 210

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        34,
        y4,
        "Image Quality Analysis"
    )

    _horizontal_bar(
        c,
        34,
        y4 - 26,
        PAGE_W - 68,
        "Focus",
        100 * float(
            quality.get(
                "focus",
                0
            )
        ),
        bar_color=BLUE
    )

    _horizontal_bar(
        c,
        34,
        y4 - 48,
        PAGE_W - 68,
        "Illumination",
        100 * float(
            quality.get(
                "illumination",
                0
            )
        ),
        bar_color=CYAN
    )

    _horizontal_bar(
        c,
        34,
        y4 - 70,
        PAGE_W - 68,
        "Contrast",
        100 * float(
            quality.get(
                "contrast",
                0
            )
        ),
        bar_color=PURPLE
    )

    _horizontal_bar(
        c,
        34,
        y4 - 92,
        PAGE_W - 68,
        "Retinal FOV",
        100 * float(
            quality.get(
                "fov",
                0
            )
        ),
        bar_color=GREEN
    )

    _footer(c)

    c.showPage()


# ---------------------------------------------------------
# PAGE 2
# ---------------------------------------------------------

def _page_lesions(
    c,
    result,
    original_image_path
):
    case_id = result.get(
        "case_id",
        "-"
    )

    _header(
        c,
        "Pathological Evidence Analysis",
        2,
        case_id
    )

    lesions = (
        result.get(
            "lesions"
        )
        or {}
    )

    artifacts = (
        result.get(
            "artifacts"
        )
        or {}
    )

    y = PAGE_H - 102

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        34,
        y,
        "Retinal Lesion Localization"
    )

    # image side-by-side
    box_y = 470
    box_h = 245
    gap = 14
    box_w = (
        PAGE_W - 68 - gap
    ) / 2

    c.setFillColor(
        LIGHT_GRAY
    )

    c.roundRect(
        34,
        box_y,
        box_w,
        box_h,
        7,
        fill=1,
        stroke=0
    )

    c.roundRect(
        34 + box_w + gap,
        box_y,
        box_w,
        box_h,
        7,
        fill=1,
        stroke=0
    )

    _fit_image(
        c,
        original_image_path,
        40,
        box_y + 24,
        box_w - 12,
        box_h - 32
    )

    _fit_image(
        c,
        artifacts.get(
            "lesion_overlay"
        ),
        40 + box_w + gap,
        box_y + 24,
        box_w - 12,
        box_h - 32
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        7.5
    )

    c.drawCentredString(
        34 + box_w / 2,
        box_y + 8,
        "Original Fundus"
    )

    c.drawCentredString(
        34 + box_w + gap + box_w / 2,
        box_y + 8,
        "NetraAI Lesion Overlay"
    )

    # lesion table
    table_y = 438

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        34,
        table_y,
        "Quantitative Lesion Summary"
    )

    headers = [
        "Lesion",
        "Count",
        "Area (px)",
        "Retinal burden",
        "Mean conf.",
        "Peak conf.",
    ]

    widths = [
        55,
        55,
        80,
        90,
        90,
        90
    ]

    x0 = 34
    header_y = table_y - 25
    row_h = 22

    c.setFillColor(
        NAVY
    )

    c.rect(
        x0,
        header_y,
        sum(widths),
        row_h,
        fill=1,
        stroke=0
    )

    cx = x0

    c.setFillColor(
        white
    )

    c.setFont(
        "Helvetica-Bold",
        6.7
    )

    for label, width in zip(
        headers,
        widths
    ):
        c.drawString(
            cx + 5,
            header_y + 8,
            label
        )

        cx += width

    lesion_order = [
        "MA",
        "HE",
        "EX",
        "SE"
    ]

    for i, name in enumerate(
        lesion_order
    ):
        info = lesions.get(
            name,
            {}
        )

        yy = (
            header_y
            - (i + 1)
            * row_h
        )

        if i % 2:
            c.setFillColor(
                LIGHT_GRAY
            )

            c.rect(
                x0,
                yy,
                sum(widths),
                row_h,
                fill=1,
                stroke=0
            )

        values = [
            name,
            str(
                info.get(
                    "count",
                    0
                )
            ),
            str(
                info.get(
                    "area_px",
                    0
                )
            ),
            f"{100 * float(info.get('retinal_area_fraction', 0)):.4f}%",
            f"{100 * float(info.get('mean_confidence', 0)):.2f}%",
            f"{100 * float(info.get('peak_confidence', 0)):.2f}%",
        ]

        cx = x0

        c.setFillColor(
            DARK_GRAY
        )

        c.setFont(
            "Helvetica",
            7
        )

        for value, width in zip(
            values,
            widths
        ):
            c.drawString(
                cx + 5,
                yy + 8,
                value
            )

            cx += width

    # charts
    chart_y = 125
    chart_h = 140

    counts = [
        lesions.get(
            x,
            {}
        ).get(
            "count",
            0
        )
        for x in lesion_order
    ]

    burdens = [
        100 * float(
            lesions.get(
                x,
                {}
            ).get(
                "retinal_area_fraction",
                0
            )
        )
        for x in lesion_order
    ]

    confs = [
        100 * float(
            lesions.get(
                x,
                {}
            ).get(
                "mean_confidence",
                0
            )
        )
        for x in lesion_order
    ]

    chart_w = 160

    _vertical_bar_chart(
        c,
        34,
        chart_y,
        chart_w,
        chart_h,
        lesion_order,
        counts,
        "Lesion count",
        max_value=max(
            max(
                counts,
                default=1
            ),
            1
        )
    )

    _vertical_bar_chart(
        c,
        215,
        chart_y,
        chart_w,
        chart_h,
        lesion_order,
        burdens,
        "Retinal burden",
        suffix="%",
        max_value=max(
            max(
                burdens,
                default=1
            ),
            1
        )
    )

    _vertical_bar_chart(
        c,
        396,
        chart_y,
        chart_w,
        chart_h,
        lesion_order,
        confs,
        "Mean lesion confidence",
        suffix="%",
        max_value=100
    )

    c.setFillColor(
        MID_GRAY
    )

    c.setFont(
        "Helvetica",
        6.6
    )

    c.drawString(
        34,
        103,
        "MA = microaneurysm | HE = hemorrhage | EX = hard exudate | SE = soft exudate"
    )

    c.drawString(
        34,
        92,
        "Lesion counts represent connected predicted regions after thresholding and component filtering."
    )

    _footer(c)

    c.showPage()


# ---------------------------------------------------------
# PAGE 3
# ---------------------------------------------------------

def _page_classifier_xai(
    c,
    result
):
    case_id = result.get(
        "case_id",
        "-"
    )

    _header(
        c,
        "Classification and Explainability",
        3,
        case_id
    )

    prediction = (
        result.get(
            "prediction"
        )
        or {}
    )

    artifacts = (
        result.get(
            "artifacts"
        )
        or {}
    )

    xai = (
        result.get(
            "xai_integrity"
        )
        or {}
    )

    y = PAGE_H - 104

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        34,
        y,
        "ICDR Classification Distribution"
    )

    probs = prediction.get(
        "grade_probabilities",
        [0, 0, 0, 0, 0]
    )

    probs_pct = [
        100 * float(v)
        for v in probs
    ]

    _vertical_bar_chart(
        c,
        34,
        500,
        260,
        180,
        GRADE_SHORT,
        probs_pct,
        "Probability by ICDR grade",
        suffix="%",
        max_value=100
    )

    # prediction summary
    _metric_card(
        c,
        324,
        620,
        235,
        60,
        "Selected grade",
        f"Grade {prediction.get('icdr_grade', '-')}",
        prediction.get(
            "grade_name",
            "-"
        ),
        fill=LIGHT_BLUE,
        value_color=BLUE
    )

    _metric_card(
        c,
        324,
        548,
        235,
        60,
        "Raw grade confidence",
        f"{100 * float(prediction.get('grade_confidence', 0)):.2f}%",
        "Temperature calibration not yet applied",
        fill=LIGHT_CYAN,
        value_color=CYAN
    )

    _metric_card(
        c,
        324,
        476,
        235,
        60,
        "Referable DR probability",
        f"{100 * float(prediction.get('rdr_probability', 0)):.2f}%",
        "Referable DR = ICDR Grade 2 or higher",
        fill=LIGHT_RED,
        value_color=RED
    )

    y2 = _section_title(
        c,
        "Grad-CAM Attention Analysis",
        452
    )

    gx = 34
    gy = 202
    gw = 265
    gh = 220

    c.setFillColor(
        LIGHT_GRAY
    )

    c.roundRect(
        gx,
        gy,
        gw,
        gh,
        7,
        fill=1,
        stroke=0
    )

    _fit_image(
        c,
        artifacts.get(
            "gradcam"
        ),
        gx + 7,
        gy + 7,
        gw - 14,
        gh - 14
    )

    # XAI bars
    rx = 322
    rw = 237

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        rx,
        407,
        "Attention integrity indicators"
    )

    _horizontal_bar(
        c,
        rx,
        371,
        rw,
        "Inside retinal FOV",
        float(
            xai.get(
                "attribution_in_retinal_fov",
                0
            )
        ),
        bar_color=GREEN
    )

    _horizontal_bar(
        c,
        rx,
        339,
        rw,
        "Lesion overlap",
        float(
            xai.get(
                "attribution_lesion_overlap",
                0
            )
        ),
        bar_color=AMBER
    )

    _horizontal_bar(
        c,
        rx,
        307,
        rw,
        "XAI integrity",
        float(
            xai.get(
                "score",
                0
            )
        ),
        bar_color=PURPLE
    )

    _, integrity_text = (
        _build_reasoning(
            result
        )
    )

    c.setFillColor(
        LIGHT_AMBER
    )

    c.roundRect(
        rx,
        205,
        rw,
        82,
        7,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        AMBER
    )

    c.setFont(
        "Helvetica-Bold",
        8
    )

    c.drawString(
        rx + 10,
        269,
        "Interpretation"
    )

    _text(
        c,
        integrity_text,
        rx + 10,
        254,
        width_chars=48,
        size=6.4,
        leading=8,
        max_lines=7
    )

    c.setFillColor(
        LIGHT_BLUE
    )

    c.roundRect(
        34,
        77,
        PAGE_W - 68,
        100,
        7,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        46,
        157,
        "Why NetraAI does not rely on Grad-CAM alone"
    )

    explanation = (
        "Grad-CAM identifies where the global classifier concentrated its attention, "
        "but spatial attention alone does not identify retinal pathology. NetraAI's "
        "TRACE-DR layer therefore compares global attention with independently generated "
        "lesion evidence, image quality, prediction confidence and pathology-grade "
        "concordance. Discordance reduces trust and can trigger human review rather than "
        "silently accepting a high-confidence prediction."
    )

    _text(
        c,
        explanation,
        46,
        140,
        width_chars=104,
        size=7.3,
        leading=10,
        max_lines=6
    )

    _footer(c)

    c.showPage()


# ---------------------------------------------------------
# PAGE 4
# ---------------------------------------------------------

def _page_reliability(
    c,
    result
):
    case_id = result.get(
        "case_id",
        "-"
    )

    _header(
        c,
        "TRACE-DR Reliability and Decision Analysis",
        4,
        case_id
    )

    quality = (
        result.get(
            "quality"
        )
        or {}
    )

    prediction = (
        result.get(
            "prediction"
        )
        or {}
    )

    concordance = (
        result.get(
            "concordance"
        )
        or {}
    )

    xai = (
        result.get(
            "xai_integrity"
        )
        or {}
    )

    trust = (
        result.get(
            "t_score"
        )
        or {}
    )

    recommendation = (
        result.get(
            "recommendation"
        )
        or {}
    )

    p_score = float(
        result.get(
            "p_score",
            0
        )
        or 0
    )

    y = PAGE_H - 104

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        34,
        y,
        "Reliability Profile"
    )

    values = [
        (
            "Image reliability",
            100
            * float(
                quality.get(
                    "score",
                    0
                )
            ),
            GREEN
        ),
        (
            "Model confidence",
            100
            * float(
                prediction.get(
                    "grade_confidence",
                    0
                )
            ),
            BLUE
        ),
        (
            "Evidence concordance",
            float(
                concordance.get(
                    "score",
                    0
                )
            ),
            CYAN
        ),
        (
            "XAI integrity",
            float(
                xai.get(
                    "score",
                    0
                )
            ),
            PURPLE
        ),
        (
            "T-Score",
            float(
                trust.get(
                    "score",
                    0
                )
            ),
            AMBER
        ),
    ]

    yy = 674

    for label, value, color in values:
        _horizontal_bar(
            c,
            34,
            yy,
            PAGE_W - 68,
            label,
            value,
            bar_color=color
        )

        yy -= 32

    # P/T cards
    _metric_card(
        c,
        34,
        460,
        250,
        74,
        "P-Score - Pathology Evidence",
        f"{p_score:.1f} / 100",
        "Transparent prototype summary of lesion evidence",
        fill=LIGHT_CYAN,
        value_color=CYAN
    )

    _metric_card(
        c,
        305,
        460,
        254,
        74,
        "T-Score - Trustworthiness",
        f"{trust.get('score', '-')} / 100",
        f"Reliability level: {trust.get('level', '-')}",
        fill=LIGHT_AMBER,
        value_color=AMBER
    )

    y2 = _section_title(
        c,
        "TRACE-DR Decision Chain",
        432
    )

    grade = prediction.get(
        "icdr_grade",
        "-"
    )

    rdr = prediction.get(
        "referable_dr",
        False
    )

    chain = [
        (
            "1. Image Quality Gate",
            (
                f"{quality.get('status', '-')} | "
                f"quality reliability {100 * float(quality.get('score', 0)):.1f}%"
            ),
            GREEN
            if quality.get(
                "status"
            ) == "GRADEABLE"
            else AMBER
        ),
        (
            "2. Global DR Classification",
            (
                f"ICDR Grade {grade} - "
                f"{prediction.get('grade_name', '-')} | "
                f"RDR {'positive' if rdr else 'negative'}"
            ),
            RED
            if rdr
            else GREEN
        ),
        (
            "3. Pathology-Grade Concordance",
            (
                f"{concordance.get('status', '-')} | "
                f"{concordance.get('score', '-')} / 100"
            ),
            GREEN
            if concordance.get(
                "status"
            ) == "HIGH"
            else AMBER
        ),
        (
            "4. Explanation Integrity",
            (
                f"XAI integrity {xai.get('score', '-')} / 100 | "
                f"lesion overlap {xai.get('attribution_lesion_overlap', '-')}%"
            ),
            PURPLE
        ),
        (
            "5. Final Reliability Routing",
            (
                f"T-Score {trust.get('score', '-')} / 100 - "
                f"{trust.get('level', '-')} | "
                f"Action: {recommendation.get('action', '-')}"
            ),
            RED
            if recommendation.get(
                "priority"
            ) == "HIGH"
            else AMBER
        ),
    ]

    yy = 340

    for title, desc, color in chain:
        _decision_box(
            c,
            34,
            yy,
            PAGE_W - 68,
            title,
            desc,
            color
        )

        yy -= 61

    # rationale
    summary, _ = (
        _build_reasoning(
            result
        )
    )

    c.setFillColor(
        LIGHT_BLUE
    )

    c.roundRect(
        34,
        62,
        PAGE_W - 68,
        74,
        7,
        fill=1,
        stroke=0
    )

    c.setFillColor(
        NAVY
    )

    c.setFont(
        "Helvetica-Bold",
        8
    )

    c.drawString(
        46,
        118,
        "Reviewer-facing explanation"
    )

    _text(
        c,
        summary,
        46,
        104,
        width_chars=103,
        size=6.6,
        leading=8,
        max_lines=5
    )

    _footer(c)

    c.showPage()


# ---------------------------------------------------------
# PUBLIC GENERATOR
# ---------------------------------------------------------

def generate_trace_report(
    result,
    original_image_path,
    output_path
):
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    c = canvas.Canvas(
        str(output_path),
        pagesize=A4
    )

    c.setTitle(
        "NetraAI TRACE-DR Explainable Retinal Screening Report"
    )

    c.setAuthor(
        "NetraAI"
    )

    c.setSubject(
        "Explainable AI analysis for diabetic retinopathy screening"
    )

    _page_overview(
        c,
        result,
        original_image_path
    )

    _page_lesions(
        c,
        result,
        original_image_path
    )

    _page_classifier_xai(
        c,
        result
    )

    _page_reliability(
        c,
        result
    )

    c.save()

    return str(
        output_path
    )
