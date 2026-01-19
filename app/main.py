"""
Curriculum Generator - FastAPI Application
"""
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .curriculum_agent import (
    generate_curriculum,
    generate_curriculum_streaming,
    generate_curriculum_parallel_streaming,
)
from .pdf_generator import generate_all_pdfs

app = FastAPI(
    title="Curriculum Generator",
    description="Generate differentiated, standards-aligned K-12 curriculum"
)

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
async def generate(
    grade: int = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    session_length: int = Form(15),
    learning_goal_type: str = Form("practice"),
    group_format: str = Form("small_group"),
    pedagogical_approach: str = Form(None),
    include_udl_docs: bool = Form(False),
    model: str = Form(None),
):
    """Generate curriculum and PDFs from teacher input."""
    teacher_input = _build_teacher_input(
        grade, subject, topic, session_length, learning_goal_type, group_format, pedagogical_approach
    )

    try:
        curriculum = generate_curriculum(teacher_input, model_key=model)
        session_id = str(uuid.uuid4())[:8]
        pdf_files = generate_all_pdfs(curriculum, session_id, str(outputs_dir), include_udl_docs)

        return {
            "success": True,
            "session_id": session_id,
            "files": pdf_files,
            "curriculum": curriculum,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _format_sse(data: dict) -> str:
    """Format a dictionary as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


@app.post("/generate-stream")
async def generate_stream(
    grade: int = Form(...),
    subject: str = Form(...),
    topic: str = Form(...),
    session_length: int = Form(15),
    learning_goal_type: str = Form("practice"),
    group_format: str = Form("small_group"),
    pedagogical_approach: str = Form(None),
    include_udl_docs: bool = Form(False),
    model: str = Form(None),
    parallel: bool = Form(True),
):
    """Generate curriculum with streaming progress updates via SSE.

    Uses parallel generation by default (2 concurrent LLM calls) for faster response.
    Set parallel=False to use the original single-call approach.
    """
    teacher_input = _build_teacher_input(
        grade, subject, topic, session_length, learning_goal_type, group_format, pedagogical_approach
    )
    session_id = str(uuid.uuid4())[:8]

    async def event_generator():
        try:
            curriculum = None

            # Choose generator based on parallel flag
            if parallel:
                generator = generate_curriculum_parallel_streaming(teacher_input, model_key=model)
            else:
                generator = generate_curriculum_streaming(teacher_input, model_key=model)

            # Process updates from the generator
            async_gen = parallel
            if async_gen:
                async for update in generator:
                    if update["type"] == "curriculum":
                        curriculum = update["data"]
                        yield _format_sse({"type": "progress", "stage": "curriculum_complete", "message": "Curriculum generated!"})
                    else:
                        yield _format_sse(update)
            else:
                for update in generator:
                    if update["type"] == "curriculum":
                        curriculum = update["data"]
                        yield _format_sse({"type": "progress", "stage": "curriculum_complete", "message": "Curriculum generated!"})
                    else:
                        yield _format_sse(update)

            if curriculum:
                yield _format_sse({"type": "progress", "stage": "pdf", "message": "Generating PDFs..."})
                pdf_files = generate_all_pdfs(curriculum, session_id, str(outputs_dir), include_udl_docs)
                yield _format_sse({"type": "progress", "stage": "complete", "message": "Complete!"})
                yield _format_sse({
                    "type": "result",
                    "success": True,
                    "session_id": session_id,
                    "files": pdf_files,
                    "curriculum": curriculum,
                })

        except Exception as e:
            yield _format_sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Download a generated PDF file."""
    file_path = outputs_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
