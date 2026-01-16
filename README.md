# Curriculum Generator

California K-12 curriculum generation tool with differentiated lesson plans.

**Live Demo:** https://curriculum-generator-iuxx.onrender.com

## Features

- Generate standards-aligned lesson plans for grades K-12
- 4 differentiated student handouts (Below, Approaching, At, Above Level)
- 20 pedagogical approaches across 6 categories
- UDL (Universal Design for Learning) integration
- Multi-model support (Claude Sonnet 4.5, Gemini 3.0 Pro)
- Real-time progress streaming during generation

## Quick Start

```bash
# Clone the repo
git clone https://github.com/dillusion13/curriculum-generator.git
cd curriculum-generator

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY and GEMINI_API_KEY

# Run with Docker
docker compose up --build

# Open http://localhost:8000
```

## Tech Stack

- **Backend:** FastAPI + LiteLLM
- **PDF Generation:** ReportLab (parallel processing)
- **Frontend:** Vanilla HTML/CSS/JS
- **Deployment:** Render (Docker)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | For Claude models |
| `GEMINI_API_KEY` | Optional | For Gemini models |

## License

MIT
