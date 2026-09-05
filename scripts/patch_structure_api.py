from pathlib import Path

path = Path("backend/sih_api/main.py")
text = path.read_text(encoding="utf-8")


# ==========================================================
# 1. IMPORT STRUCTURAL ENGINE
# ==========================================================

import_line = (
    "from sih_dr.structure.structural_engine "
    "import StructuralRetinaEngine"
)

anchor = (
    "from sih_dr.engine.explainable_dr_engine "
    "import ExplainableDREngine"
)

if import_line not in text:

    if anchor not in text:
        raise RuntimeError(
            "Could not find ExplainableDREngine import."
        )

    text = text.replace(
        anchor,
        anchor + "\n" + import_line,
        1
    )

    print("ADDED: StructuralRetinaEngine import")

else:
    print("OK: structural import already exists")


# ==========================================================
# 2. GLOBAL STRUCTURAL ENGINE
# ==========================================================

if "structure_engine = None" not in text:

    if "engine = None" not in text:
        raise RuntimeError(
            "Could not find global engine variable."
        )

    text = text.replace(
        "engine = None",
        "engine = None\nstructure_engine = None",
        1
    )

    print("ADDED: structure_engine global")

else:
    print("OK: structure_engine global exists")


# ==========================================================
# 3. LIFESPAN GLOBAL
# ==========================================================

if "global engine, structure_engine" not in text:

    text = text.replace(
        "    global engine\n",
        "    global engine, structure_engine\n",
        1
    )

    print("UPDATED: lifespan globals")

else:
    print("OK: lifespan globals already updated")


# ==========================================================
# 4. INITIALIZE STRUCTURAL ENGINE
# ==========================================================

ready_anchor = '    print("\\nTRACE-DR API READY\\n")'

structure_init = '''
    structure_engine = StructuralRetinaEngine()

    print(
        "Structural retinal layer: READY"
    )

'''

if (
    "Structural retinal layer: READY"
    not in text
):

    if ready_anchor not in text:
        raise RuntimeError(
            "Could not locate API READY print."
        )

    text = text.replace(
        ready_anchor,
        structure_init + ready_anchor,
        1
    )

    print("ADDED: structural engine initialization")

else:
    print("OK: structural engine initialization exists")


# ==========================================================
# 5. HEALTH ENDPOINT
# ==========================================================

health_anchor = '''
        "lesion_model":
            LESION_CHECKPOINT.exists(),
'''

health_replacement = '''
        "lesion_model":
            LESION_CHECKPOINT.exists(),

        "structural_layer":
            structure_engine is not None,
'''

if '"structural_layer":' not in text:

    if health_anchor not in text:
        raise RuntimeError(
            "Could not locate lesion_model health field."
        )

    text = text.replace(
        health_anchor,
        health_replacement,
        1
    )

    print("ADDED: structural health status")

else:
    print("OK: health status already exists")


# ==========================================================
# 6. MAKE ANALYZE REQUIRE BOTH ENGINES
# ==========================================================

old_ready = '''    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="TRACE-DR engine is not ready."
        )
'''

new_ready = '''    if (
        engine is None
        or structure_engine is None
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "NetraAI analysis engines "
                "are not ready."
            )
        )
'''

if old_ready in text:

    text = text.replace(
        old_ready,
        new_ready,
        1
    )

    print("UPDATED: engine readiness check")

elif (
    "or structure_engine is None"
    in text
):
    print("OK: readiness check already updated")

else:
    print(
        "WARNING: readiness block not changed."
    )


# ==========================================================
# 7. STRUCTURAL ANALYSIS AFTER GLOBAL/LESION ENGINE
# ==========================================================

analysis_anchor = '''        with inference_lock:

            result = engine.analyze(
                str(upload_path)
            )

        report_path = (
'''

analysis_replacement = '''        with inference_lock:

            result = engine.analyze(
                str(upload_path)
            )

        # --------------------------------------------------
        # STRUCTURAL RETINAL ANALYSIS
        # --------------------------------------------------

        structural_case_dir = (
            CASE_DIR
            / result["case_id"]
        )

        try:

            structural_result = (
                structure_engine.analyze(
                    str(upload_path),
                    structural_case_dir
                )
            )

            structural_artifacts = (
                structural_result.pop(
                    "artifacts",
                    {}
                )
                or {}
            )

            result["structure"] = (
                structural_result
            )

            result.setdefault(
                "artifacts",
                {}
            ).update(
                structural_artifacts
            )

        except Exception as structural_error:

            print(
                "STRUCTURAL ANALYSIS ERROR:",
                structural_error
            )

            # Do not destroy the main DR result if
            # the prototype structural layer fails.
            result["structure"] = {
                "status":
                    "STRUCTURAL_ANALYSIS_FAILED",

                "error":
                    str(structural_error),

                "optic_disc":
                    None,

                "fovea":
                    None,

                "vessels":
                    None,
            }

        report_path = (
'''

if "STRUCTURAL RETINAL ANALYSIS" not in text:

    if analysis_anchor not in text:
        raise RuntimeError(
            "Could not locate engine.analyze block."
        )

    text = text.replace(
        analysis_anchor,
        analysis_replacement,
        1
    )

    print(
        "ADDED: structural analysis to /api/analyze"
    )

else:
    print(
        "OK: structural analysis already integrated"
    )


path.write_text(
    text,
    encoding="utf-8"
)

print()
print("=" * 60)
print("NETRAAI STRUCTURAL API PATCH COMPLETE")
print("=" * 60)
