"""
Curriculum Agent - LLM integration for curriculum generation.
Supports multiple providers via LiteLLM.
"""
import json
import logging
import re
from functools import lru_cache
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
import litellm
import litellm.exceptions
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Available models for curriculum generation
AVAILABLE_MODELS = {
    "claude-sonnet-4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5",
        "provider": "Anthropic",
    },
    "claude-haiku": {
        "id": "claude-haiku-4-5-20251001",
        "name": "Claude Haiku 4.5",
        "provider": "Anthropic",
    },
    "gemini-2.5-flash": {
        "id": "gemini/gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google",
    },
    "gemini-3-flash": {
        "id": "gemini/gemini-3-flash-preview",
        "name": "Gemini 3 Flash (Preview)",
        "provider": "Google",
    },
    "gemini-3-pro": {
        "id": "gemini/gemini-3-pro-preview",
        "name": "Gemini 3 Pro (Preview)",
        "provider": "Google",
    },
}

DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "claude-haiku"


def _get_model_display_name(model_key: str) -> str:
    """Get a human-readable name for a model key."""
    model_config = AVAILABLE_MODELS.get(model_key)
    if model_config:
        return model_config["name"]
    return model_key


def _should_fallback(current_model: str) -> bool:
    """Check if fallback is available for the current model."""
    return current_model != FALLBACK_MODEL


@lru_cache(maxsize=1)
def _load_raw_standards() -> dict:
    """Load raw standards data from JSON files (cached)."""
    files_dir = Path(__file__).parent.parent / "files"
    standards_data = {}

    json_files = [
        "ca_k12_standards_enhanced.json",
        "ca_k12_standards_readiness.json",
        "topic_standards_mapping_6_8.json",
    ]

    for filename in json_files:
        filepath = files_dir / filename
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
                key = filename.replace(".json", "")
                standards_data[key] = data

    return standards_data


def _filter_standards_by_grade_subject(standards: dict, grade: int, subject: str) -> dict:
    """Filter standards data to only include relevant grade and subject."""
    filtered = {}
    subject_lower = subject.lower()

    # Map common subject names
    subject_map = {
        "math": ["math", "mathematics"],
        "ela": ["ela", "english", "reading", "writing", "language arts"],
        "science": ["science"],
        "history": ["history", "social studies", "social science"],
    }

    # Determine subject category
    subject_category = None
    for cat, names in subject_map.items():
        if any(name in subject_lower for name in names):
            subject_category = cat
            break

    for key, data in standards.items():
        if key == "ca_k12_standards_enhanced":
            # Filter enhanced standards by grade
            filtered_enhanced = {"metadata": data.get("metadata", {})}

            # Determine which section to include based on grade
            if 6 <= grade <= 8:
                grade_key = f"grade_{grade}"
                if subject_category == "math" and "math_6_8_detailed" in data:
                    math_data = data["math_6_8_detailed"]
                    if grade_key in math_data:
                        filtered_enhanced["math_detailed"] = {grade_key: math_data[grade_key]}
                if subject_category == "ela" and "ela_6_8_detailed" in data:
                    ela_data = data["ela_6_8_detailed"]
                    if grade_key in ela_data:
                        filtered_enhanced["ela_detailed"] = {grade_key: ela_data[grade_key]}
                if subject_category == "science" and "science_ms" in data:
                    filtered_enhanced["science"] = data["science_ms"]
                if subject_category == "history" and "history_social_science" in data:
                    hss = data["history_social_science"]
                    if grade_key in hss:
                        filtered_enhanced["history_social_science"] = {grade_key: hss[grade_key]}
            else:
                # For other grades, include grade band summaries
                if grade <= 5 and "elementary_summary" in data:
                    filtered_enhanced["elementary_summary"] = data["elementary_summary"]
                elif grade >= 9 and "high_school_summary" in data:
                    filtered_enhanced["high_school_summary"] = data["high_school_summary"]

            filtered[key] = filtered_enhanced

        elif key == "ca_k12_standards_readiness":
            # Filter readiness indicators by grade
            if "readiness_indicators" in data:
                indicators = data["readiness_indicators"]
                grade_key = f"grade_{grade}"
                if grade_key in indicators:
                    filtered[key] = {
                        "readiness_indicators": {grade_key: indicators[grade_key]}
                    }

        elif key == "topic_standards_mapping_6_8":
            # Filter topic mappings by subject if in grade 6-8
            if 6 <= grade <= 8 and subject_category:
                if subject_category in data:
                    filtered[key] = {subject_category: data[subject_category]}
                elif "metadata" in data:
                    filtered[key] = {"metadata": data["metadata"]}

    return filtered


def load_standards_json(grade: int = None, subject: str = None) -> str:
    """Load and optionally filter standards JSON by grade and subject."""
    raw_standards = _load_raw_standards()

    if grade is not None and subject is not None:
        # Filter standards to reduce token usage
        filtered = _filter_standards_by_grade_subject(raw_standards, grade, subject)
        return json.dumps(filtered, indent=2)

    # Return all standards if no filter specified
    return json.dumps(raw_standards, indent=2)


@lru_cache(maxsize=1)
def load_pedagogical_approaches_json() -> str:
    """Load the pedagogical approaches JSON file."""
    files_dir = Path(__file__).parent.parent / "files"
    filepath = files_dir / "pedagogical_approaches.json"

    if filepath.exists():
        with open(filepath, "r") as f:
            return f.read()
    return "{}"


@lru_cache(maxsize=3)
def _load_prompt_template(filename: str) -> str:
    """Load a prompt template file (cached)."""
    prompt_path = Path(__file__).parent.parent / "files" / filename
    with open(prompt_path, "r") as f:
        return f.read()


# Jinja2 environment for prompt templates
_jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent.parent / "files"),
    autoescape=False,  # Prompts don't need HTML escaping
)


def _inject_prompt_data(template_name: str, grade: int = None, subject: str = None) -> str:
    """Render prompt template with Jinja2.

    Supports both legacy {{VAR}} syntax and Jinja2 {{ VAR }} syntax for backwards compatibility.
    """
    # Try to load as Jinja2 template
    try:
        template = _jinja_env.get_template(template_name)
        return template.render(
            STANDARDS_JSON=load_standards_json(grade, subject),
            PEDAGOGICAL_APPROACHES_JSON=load_pedagogical_approaches_json(),
            grade=grade,
            subject=subject
        )
    except Exception:
        # Fallback to legacy string replacement for backwards compatibility
        base_prompt = _load_prompt_template(template_name)
        standards_json = load_standards_json(grade, subject)
        pedagogical_json = load_pedagogical_approaches_json()

        return (base_prompt
                .replace("{{STANDARDS_JSON}}", standards_json)
                .replace("{{PEDAGOGICAL_APPROACHES_JSON}}", pedagogical_json)
                .replace("{{ STANDARDS_JSON }}", standards_json)
                .replace("{{ PEDAGOGICAL_APPROACHES_JSON }}", pedagogical_json))


def load_curriculum_prompt(grade: int = None, subject: str = None) -> str:
    """Load the curriculum agent system prompt with filtered standards."""
    return _inject_prompt_data("curriculum_agent_prompt.md", grade, subject)


def load_teacher_guide_prompt(grade: int = None, subject: str = None) -> str:
    """Load the teacher guide prompt with filtered standards."""
    return _inject_prompt_data("teacher_guide_prompt.md", grade, subject)


def load_student_materials_prompt(grade: int = None, subject: str = None) -> str:
    """Load the student materials prompt with filtered standards."""
    return _inject_prompt_data("student_materials_prompt.md", grade, subject)


def _get_model_id(model_key: str = None) -> str:
    """Get the LiteLLM model ID from a model key, with validation."""
    if model_key is None:
        model_key = DEFAULT_MODEL

    model_config = AVAILABLE_MODELS.get(model_key)
    if not model_config:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")

    return model_config["id"]


# ============================================================================
# LLM CALL WITH RETRY LOGIC
# ============================================================================
# Retry configuration for transient API failures
RETRY_EXCEPTIONS = (
    litellm.exceptions.RateLimitError,
    litellm.exceptions.APIConnectionError,
    litellm.exceptions.Timeout,
    litellm.exceptions.ServiceUnavailableError,
    litellm.InternalServerError,  # Handles 503 "model overloaded" from Gemini
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    before_sleep=lambda retry_state: logger.warning(
        f"LLM call failed, retrying ({retry_state.attempt_number}/3)..."
    )
)
def _call_llm_sync(
    model_id: str,
    messages: list,
    max_tokens: int,
    stream: bool = False
):
    """Synchronous LLM call with automatic retry on transient failures."""
    return litellm.completion(
        model=model_id,
        messages=messages,
        max_tokens=max_tokens,
        stream=stream,
        timeout=240  # 4 minute timeout
    )


def _calculate_max_tokens(num_days: int) -> int:
    """Calculate max tokens based on number of days.

    More days = more content = more tokens needed.
    Base: 16000 tokens for single day, +8000 per additional day.
    """
    base_tokens = 16000
    additional_per_day = 8000
    return base_tokens + (num_days - 1) * additional_per_day


def generate_curriculum(teacher_input: dict[str, Any], model_key: str = None) -> dict[str, Any]:
    """
    Generate curriculum using LiteLLM (supports multiple providers).

    Args:
        teacher_input: Dictionary with teacher's class information
        model_key: Key from AVAILABLE_MODELS (e.g., "claude-sonnet-4.5", "gemini-3-flash")

    Returns:
        Dictionary containing teacher_guide and student_materials
    """
    current_model = model_key or DEFAULT_MODEL
    model_id = _get_model_id(current_model)
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")
    num_days = teacher_input.get("num_days", 1)
    max_tokens = _calculate_max_tokens(num_days)

    system_prompt = load_curriculum_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate curriculum for this class:\n\n```json\n{user_message}\n```"}
    ]

    try:
        response = _call_llm_sync(
            model_id=model_id,
            messages=messages,
            max_tokens=max_tokens
        )
        response_text = response.choices[0].message.content
        return _parse_json_response(response_text)

    except Exception as e:
        if not _should_fallback(current_model):
            raise

        primary_name = _get_model_display_name(current_model)
        fallback_name = _get_model_display_name(FALLBACK_MODEL)
        logger.warning(f"{primary_name} failed: {e}. Falling back to {fallback_name}")
        return generate_curriculum(teacher_input, model_key=FALLBACK_MODEL)


def generate_curriculum_streaming(teacher_input: dict[str, Any], model_key: str = None):
    """
    Generate curriculum with streaming progress updates.

    Yields:
        dict: Progress updates with type and data fields
    """
    current_model = model_key or DEFAULT_MODEL
    model_id = _get_model_id(current_model)
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")
    num_days = teacher_input.get("num_days", 1)
    max_tokens = _calculate_max_tokens(num_days)

    yield {"type": "progress", "stage": "loading", "message": "Loading standards..."}

    system_prompt = load_curriculum_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    days_msg = f" ({num_days}-day lesson)" if num_days > 1 else ""
    yield {"type": "progress", "stage": "generating", "message": f"Generating curriculum{days_msg}..."}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate curriculum for this class:\n\n```json\n{user_message}\n```"}
    ]

    try:
        response = _call_llm_sync(
            model_id=model_id,
            messages=messages,
            max_tokens=max_tokens,
            stream=True
        )

        response_text = ""
        chunk_count = 0
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
                chunk_count += 1
                if chunk_count % 50 == 0:
                    progress_msg = f"Generating curriculum... ({len(response_text)} chars)"
                    yield {"type": "progress", "stage": "generating", "message": progress_msg}

        yield {"type": "progress", "stage": "parsing", "message": "Parsing response..."}

        curriculum = _parse_json_response(response_text)
        yield {"type": "curriculum", "data": curriculum}

    except Exception as e:
        if not _should_fallback(current_model):
            raise

        primary_name = _get_model_display_name(current_model)
        fallback_name = _get_model_display_name(FALLBACK_MODEL)
        logger.warning(f"{primary_name} failed: {e}. Falling back to {fallback_name}")
        yield {"type": "progress", "stage": "fallback", "message": f"{primary_name} unavailable, trying {fallback_name}..."}

        for update in generate_curriculum_streaming(teacher_input, model_key=FALLBACK_MODEL):
            yield update


def _parse_json_response(response_text: str) -> dict:
    """Parse JSON from LLM response with robust error handling.

    Handles various formats including markdown code fences.
    """
    original = response_text

    # Try extracting from markdown code fence
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
    ]

    for pattern in patterns:
        match = re.search(pattern, response_text)
        if match:
            response_text = match.group(1).strip()
            break

    try:
        return json.loads(response_text)
    except JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nResponse preview: {original[:500]}")
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
