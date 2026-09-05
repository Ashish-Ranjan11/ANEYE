from pathlib import Path

# =========================================================
# 1. LESION INFERENCE
#    Return all connected lesion components, not only top 50
# =========================================================

lesion_path = Path("sih_dr/lesions/inference.py")
text = lesion_path.read_text(encoding="utf-8")

old = '"components":\n                    components[:50]'
new = '"components":\n                    components'

if old in text:
    text = text.replace(old, new, 1)
    print("PATCHED: lesion inference now returns all components")
elif '"components":\n                    components' in text:
    print("OK: lesion components already unrestricted")
else:
    print("WARNING: components[:50] pattern not found")

lesion_path.write_text(text, encoding="utf-8")


# =========================================================
# 2. UNIFIED ENGINE
#    Preserve components in serializable lesion summary
# =========================================================

engine_path = Path(
    "sih_dr/engine/explainable_dr_engine.py"
)

text = engine_path.read_text(encoding="utf-8")

if '"components":' not in text[text.find("SERIALIZABLE LESION SUMMARY"):text.find("FINAL RESULT")]:
    target = '''                "peak_confidence":
                    info[
                        "peak_confidence"
                    ],
            }'''

    replacement = '''                "peak_confidence":
                    info[
                        "peak_confidence"
                    ],

                "components":
                    info.get(
                        "components",
                        []
                    ),
            }'''

    if target not in text:
        raise RuntimeError(
            "Could not find lesion_summary insertion point."
        )

    text = text.replace(
        target,
        replacement,
        1
    )

    print(
        "PATCHED: lesion components preserved "
        "in unified result"
    )
else:
    print(
        "OK: lesion summary already contains components"
    )


# =========================================================
# 3. IMAGE DIMENSIONS
#    Needed to convert absolute lesion x/y → normalized retina
# =========================================================

result_section = text[text.find("# FINAL RESULT"):]

if '"image_width":' not in result_section:

    target = '''            "case_id":
                case_id,

            "quality": {'''

    replacement = '''            "case_id":
                case_id,

            "image_width":
                int(
                    working_image.shape[1]
                ),

            "image_height":
                int(
                    working_image.shape[0]
                ),

            "quality": {'''

    if target not in text:
        raise RuntimeError(
            "Could not find final result insertion point."
        )

    text = text.replace(
        target,
        replacement,
        1
    )

    print(
        "PATCHED: image_width and image_height added"
    )

else:
    print(
        "OK: image dimensions already present"
    )


engine_path.write_text(
    text,
    encoding="utf-8"
)

print()
print("REGIONAL ANALYSIS PATCH COMPLETE")
