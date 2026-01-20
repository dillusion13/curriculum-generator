# Curriculum Generator App Review

## Executive Summary
The Curriculum Generator is a well-structured, modern web application that effectively leverages LLMs to solve a specific educational pain point. The use of **FastAPI** for the backend, **LiteLLM** for model agility, and **ReportLab** for professional PDF output is a strong technical choice. The application supports advanced features like parallel processing, streaming updates, and differentiation logic out of the box.

However, there are areas where the codebase could be more robust, specifically regarding code duplication in PDF generation, error handling for LLM outputs, and the lack of unit tests.

## Architecture & Code Quality

### Strengths
- **Modular Design**: Clear separation of concerns between API (`main.py`), Agent Logic (`curriculum_agent.py`), and Output Generation (`pdf_generator.py`).
- **Parallel Processing**: effectively uses `asyncio.gather` and `ThreadPoolExecutor` to parallelize prompt generation and PDF creation, which is crucial for latency in LLM apps.
- **Model Agnostic**: Using `LiteLLM` allows easy switching between Claude and Gemini, future-proofing the app.
- **Caching**: Good use of `lru_cache` for loading static resources (standards, prompts).
- **Type Hinting**: Consistent use of Python type hints (`mypy` ready).

### Weaknesses
- **Code Duplication**: The PDF styling logic (colors, styles, table formatting) is duplicated across `app/pdf_generator.py`, `generate_research_pdf.py`, and `generate_comparison_report.py`. This violates DRY (Don't Repeat Yourself) and makes maintaining the "Scholarly Modern" aesthetic difficult.
- **Prompt Management**: Prompts are stored as Markdown files but populated using simple string `.replace()`. This is fragile. If a placeholder name changes or is typoed, it will fail silently or leave artifacts.
- **Error Handling**: `_parse_json_response` relies on the LLM generating perfectly formatted JSON (or wrapped in markdown blocks). While `json.loads` is used, there's no retry mechanism or robust parsing for malformed JSON, which LLMs occasionally produce.
- **Hardcoded Logic**: Some logic regarding subject categories and standard filtering is hardcoded in `curriculum_agent.py`'s `_filter_standards_by_grade_subject`. As standards evolve, this maintenance burden will grow.

## Execution & User Experience

### Strengths
- **Streaming UI**: The frontend implementation using Server-Sent Events (SSE) provides excellent feedback to the user, showing real-time progress which masks the inherent latency of LLM calls.
- **Professional Output**: The generated PDFs are high-quality, not just simple text dumps. The design system ("Scholarly Modern") looks professional and credible.
- **Interactive Form**: The frontend form is dynamic and user-friendly, with good use of categories and independent toggles (UDL, etc.).

### Risks & UX Gaps
- **Security**: The `/generate` endpoints are unauthenticated and rate-unlimited. If exposed publicly, this could lead to high API costs.
- **Accessibility**: The frontend functionality (esp. the streaming updates and dynamic form) works well but relies heavily on JavaScript.
- **Mobile Experience**: The Preview Sidebar is sticky but might take up too much space on smaller screens (based on code review of `index.html` structure).

## Detailed Recommendations

### 1. Refactor PDF Generation
Create a shared `styles.py` or module within `app` that exports the `COLORS`, `get_styles()`, and common component functions (loops, headers). Import this in both the main app and standalone scripts.

### 2. Robust JSON Parsing
Implement a more resilient parser (or use a library like `instructor` or `pydantic` capabilities with LiteLLM) to guarantee valid JSON output. Add a retry loop (max 1-2 retries) if parsing fails.

### 3. Move to Template Engine for Prompts
Use `jinja2` (which is already installed for FastAPI templates) to render the system prompts. This allows for logic within prompts (e.g., "if grade < 3, include X") and safer variable substitution.

### 4. Add Unit Tests
The current `test_curriculum.py` is an end-to-end integration test requiring API keys. Add unit tests for:
- `_filter_standards_by_grade_subject` (verify logic without loading files)
- `_parse_json_response` (test with various messy LLM outputs)
- PDF generation functions (test they run without error on mock data)

### 5. Security Hardening
Add a simple API key check or rate limiter to `main.py` if this is intended for any public or multi-user deployment.
