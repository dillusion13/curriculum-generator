# Curriculum Generator

California K-12 curriculum generation tool with differentiated lesson plans.

## Quick Start
```bash
docker compose up --build
# Open http://localhost:8000
```

## Architecture
- FastAPI backend with Claude Sonnet for curriculum generation
- ReportLab for PDF generation
- Vanilla HTML/CSS/JS frontend

## Key Directories
- `app/` - Python backend code
- `files/` - CA standards JSON data (standards, readiness indicators, topic mappings)
- `outputs/` - Generated PDFs

## Environment
Requires `ANTHROPIC_API_KEY` in `.env`

## API Endpoints
- `GET /` - Teacher input form
- `POST /generate` - Generate curriculum and PDFs
- `GET /download/{filename}` - Download generated PDF

## Conventions
- Use type hints in Python
- Keep PDF generation logic in pdf_generator.py
- Standards data loaded from files/ at startup
- Curriculum agent prompt in files/curriculum_agent_prompt.md
