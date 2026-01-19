# Curriculum Generator

California K-12 curriculum generation tool with differentiated lesson plans.

**Live:** https://curriculum-generator-iuxx.onrender.com
**Repo:** https://github.com/dillusion13/curriculum-generator

## Quick Start
```bash
docker compose up --build
# Open http://localhost:8000
```

## Docker-First Development
**All commands must run inside Docker.** Do not install dependencies locally.

```bash
# Run tests
docker compose exec web python test_curriculum.py

# Run with specific approach
docker compose exec web python test_curriculum.py --approach 5e_lessons

# Compare models
docker compose exec web python test_curriculum.py --compare-models
```

## Architecture
- **Backend**: FastAPI + LiteLLM for multi-provider LLM support
- **PDF Generation**: ReportLab
- **Frontend**: Vanilla HTML/CSS/JS with Material Symbols

### Multi-Model Support
Models configured in `app/curriculum_agent.py`:
- `gemini-3-pro` (default) - Google
- `claude-sonnet-4.5` - Anthropic

Add new models to `AVAILABLE_MODELS` dict. Change default via `DEFAULT_MODEL`.

## Key Files

### Backend (`app/`)
| File | Purpose |
|------|---------|
| `main.py` | FastAPI routes, form handling |
| `curriculum_agent.py` | LLM integration via LiteLLM |
| `pdf_generator.py` | ReportLab PDF creation |

### Data (`files/`)
| File | Purpose |
|------|---------|
| `pedagogical_approaches.json` | 20 teaching methodologies with lesson structures |
| `curriculum_agent_prompt.md` | System prompt with UDL framework |
| `ca_k12_standards_enhanced.json` | California standards |
| `topic_standards_mapping_6_8.json` | Topic-to-standard lookups |

### Frontend (`app/templates/`, `app/static/`)
| File | Purpose |
|------|---------|
| `index.html` | Teacher input form |
| `style.css` | "Scholarly Modern" design system |

## Form Features

### Pedagogical Approaches (20 total)
Organized into 6 categories in dropdown:
- Inquiry & Problem-Based
- Project & Passion-Driven
- Collaborative Learning
- Creative & Performance
- Engagement & Skills
- Civic & Cultural

### UDL Integration
- All lessons apply UDL Guidelines 3.0 principles
- Optional checkbox to include explicit UDL documentation in PDFs
- Framework defined in `curriculum_agent_prompt.md`

## Environment
```env
ANTHROPIC_API_KEY=your-key   # Required for Claude
GEMINI_API_KEY=your-key      # Required for Gemini
```

## API Endpoints
- `GET /` - Teacher input form
- `POST /generate` - Generate curriculum and PDFs (blocking)
- `POST /generate-stream` - Generate with SSE progress updates (used by frontend)
- `GET /download/{filename}` - Download generated PDF
- `GET /health` - Health check

## Deployment
Hosted on Render with auto-deploy from `main` branch. Config in `render.yaml`.

## Conventions
- Use type hints in Python
- Keep PDF logic in `pdf_generator.py`
- Standards data loaded from `files/` at startup
- Test new features with Docker: `docker compose exec web python test_curriculum.py`
