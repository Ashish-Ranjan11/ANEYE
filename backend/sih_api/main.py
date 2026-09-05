from contextlib import asynccontextmanager
from pathlib import Path
import shutil
import threading
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sih_dr.engine.explainable_dr_engine import ExplainableDREngine
from sih_dr.structure.structural_engine import StructuralRetinaEngine
from sih_dr.reports.pdf_report import generate_trace_report


ROOT = Path(__file__).resolve().parents[2]

GRADER_CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "grading"
    / "global_final.pth"
)

LESION_CHECKPOINT = (
    ROOT
    / "checkpoints"
    / "sih_dr"
    / "lesions"
    / "lesion_final.pth"
)

UPLOAD_DIR = (
    ROOT
    / "results"
    / "sih_dr"
    / "uploads"
)

CASE_DIR = (
    ROOT
    / "results"
    / "sih_dr"
    / "cases"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


engine = None
structure_engine = None

# Prevent two GPU analyses from running simultaneously.
inference_lock = threading.Lock()


def artifact_url(path_string):
    if not path_string:
        return None

    path = Path(path_string)

    if not path.is_absolute():
        path = ROOT / path

    try:
        relative = path.resolve().relative_to(
            CASE_DIR.resolve()
        )

        return (
            "/artifacts/"
            + relative.as_posix()
        )

    except ValueError:
        return None


def prepare_response(result):
    """
    Convert local filesystem artifact paths into URLs
    the React frontend can access.
    """

    if result.get("artifacts"):

        converted = {}

        for key, value in result[
            "artifacts"
        ].items():

            converted[key] = (
                artifact_url(value)
            )

        result["artifacts"] = converted

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):

    global engine, structure_engine

    print("\n================================")
    print("       STARTING TRACE-DR")
    print("================================")

    print(
        "Global checkpoint:",
        GRADER_CHECKPOINT
    )

    print(
        "Lesion checkpoint:",
        LESION_CHECKPOINT
    )

    if not GRADER_CHECKPOINT.exists():
        raise RuntimeError(
            f"Missing grader checkpoint: "
            f"{GRADER_CHECKPOINT}"
        )

    if not LESION_CHECKPOINT.exists():
        raise RuntimeError(
            f"Missing lesion checkpoint: "
            f"{LESION_CHECKPOINT}"
        )

    engine = ExplainableDREngine(
        grader_checkpoint=str(
            GRADER_CHECKPOINT
        ),

        lesion_checkpoint=str(
            LESION_CHECKPOINT
        ),

        output_dir=str(
            CASE_DIR
        ),
    )


    structure_engine = StructuralRetinaEngine()

    print(
        "Structural retinal layer: READY"
    )

    print("\nTRACE-DR API READY\n")

    yield

    if (
        engine is not None
        and hasattr(engine, "gradcam")
    ):

        try:
            engine.gradcam.close()
        except Exception:
            pass


app = FastAPI(
    title="TRACE-DR API",
    description=(
        "Evidence-grounded explainable "
        "diabetic retinopathy screening API"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/artifacts",
    StaticFiles(
        directory=str(
            CASE_DIR
        )
    ),
    name="artifacts",
)


@app.get("/")
def root():
    return {
        "system": "TRACE-DR",
        "status": "online",
        "purpose": (
            "Explainable AI for "
            "Diabetic Retinopathy Screening"
        ),
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",

        "engine_loaded":
            engine is not None,

        "global_model":
            GRADER_CHECKPOINT.exists(),

        "lesion_model":
            LESION_CHECKPOINT.exists(),

        "structural_layer":
            structure_engine is not None,
    }


@app.post("/api/analyze")
def analyze_fundus(
    file: UploadFile = File(...)
):

    if (
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

    allowed = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
    }

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, PNG, BMP or TIFF."
            ),
        )

    case_uuid = uuid.uuid4().hex[:12]

    upload_path = (
        UPLOAD_DIR
        / f"{case_uuid}{suffix}"
    )

    try:

        with open(
            upload_path,
            "wb"
        ) as output:

            shutil.copyfileobj(
                file.file,
                output
            )

        with inference_lock:

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
            CASE_DIR
            / result["case_id"]
            / "trace_dr_report.pdf"
        )

        generate_trace_report(
            result=result,
            original_image_path=upload_path,
            output_path=report_path,
        )

        result.setdefault(
            "artifacts",
            {}
        )["report"] = str(report_path)

        result = prepare_response(
            result
        )

        result["source"] = {
            "original_filename":
                file.filename,

            "analysis_id":
                case_uuid,
        }

        return result

    except Exception as exc:

        print(
            "\nTRACE-DR ANALYSIS ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    finally:

        try:
            file.file.close()
        except Exception:
            pass

        try:
            upload_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass
