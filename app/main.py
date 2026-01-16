"""
Curriculum Generator - FastAPI Application
"""
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .curriculum_agent import generate_curriculum
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

    # Build the input structure
    teacher_input = {
        "grade": grade,
        "subject": subject,
        "topic": topic,
        "session_length_minutes": session_length,
        "learning_goal_type": learning_goal_type,
        "group_format": group_format,
    }

    # Add pedagogical approach if specified
    if pedagogical_approach:
        teacher_input["pedagogical_approach"] = pedagogical_approach

    try:
        # Generate curriculum using selected model
        curriculum = generate_curriculum(teacher_input, model_key=model)

        # Generate unique session ID for file naming
        session_id = str(uuid.uuid4())[:8]

        # Generate PDFs
        pdf_files = generate_all_pdfs(curriculum, session_id, str(outputs_dir), include_udl_docs)

        return {
            "success": True,
            "session_id": session_id,
            "files": pdf_files,
            "curriculum": curriculum,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
