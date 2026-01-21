"""
Curriculum Generator - FastAPI Application
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
import litellm.exceptions

from .curriculum_agent import (
    AVAILABLE_MODELS,
    generate_curriculum,
    generate_curriculum_streaming,
    load_pedagogical_approaches_json,
)
from .docx_generator import save_combined_document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Curriculum Generator",
    description="Generate differentiated, standards-aligned K-12 curriculum"
)

# Add rate limiter to app state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ============================================================================
# INPUT VALIDATION
# ============================================================================
# Load valid pedagogical approaches at startup
_approaches_data = json.loads(load_pedagogical_approaches_json())
VALID_APPROACHES = set(a["id"] for a in _approaches_data.get("pedagogical_approaches", []))


class CurriculumRequest(BaseModel):
    """Validated curriculum generation request."""
    grade: int = Field(..., ge=0, le=12, description="Grade level (K=0, 1-12)")
    subject: str = Field(..., pattern="^(Math|ELA|Science|History)$", description="Subject area")
    topic: str = Field(..., max_length=500, description="Topic to teach")
    session_length: int = Field(45, ge=5, le=120, description="Session length in minutes")
    num_days: int = Field(1, ge=1, le=3, description="Number of days for the lesson")
    learning_goal_type: str = Field("practice", pattern="^(introduce|practice|assess|remediate)$")
    group_format: str = Field("small_group", pattern="^(individual|small_group|whole_class)$")
    pedagogical_approach: Optional[str] = None
    include_udl_docs: bool = False
    model: Optional[str] = None

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Reject newlines and carriage returns to prevent prompt injection."""
        if '\n' in v or '\r' in v:
            raise ValueError("Topic cannot contain line breaks")
        return v.strip()

    @field_validator('pedagogical_approach')
    @classmethod
    def validate_pedagogical_approach(cls, v: Optional[str]) -> Optional[str]:
        """Validate against available pedagogical approaches."""
        if v is None or v == "":
            return None
        if v not in VALID_APPROACHES:
            raise ValueError(f"Unknown pedagogical approach: {v}")
        return v

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Validate against available models."""
        if v is not None and v not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {v}. Available: {list(AVAILABLE_MODELS.keys())}")
        return v

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
outputs_dir = Path(__file__).parent.parent / "outputs"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Ensure outputs directory exists
outputs_dir.mkdir(exist_ok=True)


def _build_teacher_input(
    grade: int,
    subject: str,
    topic: str,
    session_length: int,
    num_days: int,
    learning_goal_type: str,
    group_format: str,
    pedagogical_approach: str = None
) -> dict:
    """Build the teacher input dictionary from form fields."""
    teacher_input = {
        "grade": grade,
        "subject": subject,
        "topic": topic,
        "session_length_minutes": session_length,
        "num_days": num_days,
        "learning_goal_type": learning_goal_type,
        "group_format": group_format,
    }
    if pedagogical_approach:
        teacher_input["pedagogical_approach"] = pedagogical_approach
    return teacher_input


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the teacher input form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
@limiter.limit("10/minute")
async def generate(
    request: Request,
    grade: int = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    session_length: int = Form(45),
    num_days: int = Form(1),
    learning_goal_type: str = Form("practice"),
    group_format: str = Form("small_group"),
    pedagogical_approach: str = Form(None),
    include_udl_docs: bool = Form(False),
    model: str = Form(None),
):
    """Generate curriculum and PDFs from teacher input."""
    # Validate input using Pydantic model
    try:
        validated = CurriculumRequest(
            grade=grade,
            subject=subject,
            topic=topic,
            session_length=session_length,
            num_days=num_days,
            learning_goal_type=learning_goal_type,
            group_format=group_format,
            pedagogical_approach=pedagogical_approach,
            include_udl_docs=include_udl_docs,
            model=model,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    teacher_input = _build_teacher_input(
        validated.grade, validated.subject, validated.topic, validated.session_length,
        validated.num_days, validated.learning_goal_type, validated.group_format, validated.pedagogical_approach
    )

    try:
        curriculum = generate_curriculum(teacher_input, model_key=validated.model)
        session_id = str(uuid.uuid4())  # Full UUID for security

        # Generate combined DOCX document
        docx_filename = save_combined_document(
            curriculum,
            str(outputs_dir),
            include_udl=validated.include_udl_docs
        )

        return {
            "success": True,
            "session_id": session_id,
            "document": docx_filename,
            "curriculum": curriculum,
        }

    except Exception as e:
        logger.exception("Curriculum generation failed")
        raise HTTPException(status_code=500, detail="Generation failed. Please try again.")


def _format_sse(data: dict) -> str:
    """Format a dictionary as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


@app.post("/generate-stream")
@limiter.limit("10/minute")
async def generate_stream(
    request: Request,
    grade: int = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    session_length: int = Form(45),
    num_days: int = Form(1),
    learning_goal_type: str = Form("practice"),
    group_format: str = Form("small_group"),
    pedagogical_approach: str = Form(None),
    include_udl_docs: bool = Form(False),
    model: str = Form(None),
):
    """Generate curriculum with streaming progress updates via SSE."""
    # Validate input using Pydantic model
    try:
        validated = CurriculumRequest(
            grade=grade,
            subject=subject,
            topic=topic,
            session_length=session_length,
            num_days=num_days,
            learning_goal_type=learning_goal_type,
            group_format=group_format,
            pedagogical_approach=pedagogical_approach,
            include_udl_docs=include_udl_docs,
            model=model,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    teacher_input = _build_teacher_input(
        validated.grade, validated.subject, validated.topic, validated.session_length,
        validated.num_days, validated.learning_goal_type, validated.group_format, validated.pedagogical_approach
    )
    session_id = str(uuid.uuid4())  # Full UUID for security

    async def event_generator():
        try:
            curriculum = None

            for update in generate_curriculum_streaming(teacher_input, model_key=validated.model):
                if update["type"] == "curriculum":
                    curriculum = update["data"]
                    yield _format_sse({"type": "progress", "stage": "curriculum_complete", "message": "Curriculum generated!"})
                else:
                    yield _format_sse(update)

            if curriculum:
                yield _format_sse({"type": "progress", "stage": "docx", "message": "Generating document..."})
                docx_filename = save_combined_document(
                    curriculum,
                    str(outputs_dir),
                    include_udl=validated.include_udl_docs
                )
                yield _format_sse({"type": "progress", "stage": "complete", "message": "Complete!"})
                yield _format_sse({
                    "type": "result",
                    "success": True,
                    "session_id": session_id,
                    "document": docx_filename,
                    "curriculum": curriculum,
                })

        except litellm.exceptions.Timeout:
            logger.warning("Generation timed out after 4 minutes")
            yield _format_sse({"type": "error", "message": "Generation timed out. Try again or select a different model."})
        except Exception as e:
            logger.exception("Streaming generation failed")
            yield _format_sse({"type": "error", "message": "Generation failed. Please try again."})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file (DOCX or PDF)."""
    # Resolve to absolute path to prevent path traversal attacks
    file_path = (outputs_dir / filename).resolve()

    # Security: Ensure the resolved path is still within outputs_dir
    if not file_path.is_relative_to(outputs_dir.resolve()):
        logger.warning(f"Path traversal attempt blocked: {filename}")
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type based on file extension
    if filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
