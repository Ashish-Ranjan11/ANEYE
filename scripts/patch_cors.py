from pathlib import Path
import re

path = Path("backend/sih_api/main.py")
text = path.read_text(encoding="utf-8")

pattern = r'allow_origins\s*=\s*\[[\s\S]*?\]'

replacement = '''allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]'''

new_text, count = re.subn(
    pattern,
    replacement,
    text,
    count=1
)

if count == 0:
    raise RuntimeError(
        "Could not locate allow_origins in main.py"
    )

path.write_text(
    new_text,
    encoding="utf-8"
)

print("CORS PATCHED FOR LOCALHOST + 127.0.0.1")
