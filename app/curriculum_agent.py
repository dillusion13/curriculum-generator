"""
Curriculum Agent - LLM integration for curriculum generation.
Supports multiple providers via LiteLLM.
"""
import asyncio
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import litellm
from dotenv import load_dotenv

load_dotenv()

# Available models for curriculum generation
AVAILABLE_MODELS = {
    "claude-sonnet-4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5",
        "provider": "Anthropic",
    },
    "gemini-3-pro": {
        "id": "gemini/gemini-3-pro-preview",
        "name": "Gemini 3.0 Pro",
        "provider": "Google",
    },
}

DEFAULT_MODEL = "gemini-3-pro"


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


def _inject_prompt_data(base_prompt: str, grade: int = None, subject: str = None) -> str:
    """Inject standards and pedagogical data into a prompt template."""
    standards_json = load_standards_json(grade, subject)
    pedagogical_json = load_pedagogical_approaches_json()

    return (base_prompt
            .replace("{{STANDARDS_JSON}}", standards_json)
            .replace("{{PEDAGOGICAL_APPROACHES_JSON}}", pedagogical_json))


def load_curriculum_prompt(grade: int = None, subject: str = None) -> str:
    """Load the curriculum agent system prompt with filtered standards."""
    return _inject_prompt_data(_load_prompt_template("curriculum_agent_prompt.md"), grade, subject)


def load_teacher_guide_prompt(grade: int = None, subject: str = None) -> str:
    """Load the teacher guide prompt with filtered standards."""
    return _inject_prompt_data(_load_prompt_template("teacher_guide_prompt.md"), grade, subject)


def load_student_materials_prompt(grade: int = None, subject: str = None) -> str:
    """Load the student materials prompt with filtered standards."""
    return _inject_prompt_data(_load_prompt_template("student_materials_prompt.md"), grade, subject)


def _get_model_id(model_key: str = None) -> str:
    """Get the LiteLLM model ID from a model key, with validation."""
    if model_key is None:
        model_key = DEFAULT_MODEL

    model_config = AVAILABLE_MODELS.get(model_key)
    if not model_config:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")

    return model_config["id"]


def generate_curriculum(teacher_input: dict[str, Any], model_key: str = None) -> dict[str, Any]:
    """
    Generate curriculum using LiteLLM (supports multiple providers).

    Args:
        teacher_input: Dictionary with teacher's class information
        model_key: Key from AVAILABLE_MODELS (e.g., "claude-sonnet-4.5", "gemini-3-pro")

    Returns:
        Dictionary containing teacher_guide and student_materials
    """
    model_id = _get_model_id(model_key)
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")

    system_prompt = load_curriculum_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    response = litellm.completion(
        model=model_id,
        max_tokens=16000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate curriculum for this class:\n\n```json\n{user_message}\n```"}
        ]
    )

    response_text = response.choices[0].message.content
    return _parse_json_response(response_text)


def generate_curriculum_streaming(teacher_input: dict[str, Any], model_key: str = None):
    """
    Generate curriculum with streaming progress updates.

    Yields:
        dict: Progress updates with type and data fields
    """
    model_id = _get_model_id(model_key)
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")

    yield {"type": "progress", "stage": "loading", "message": "Loading standards..."}

    system_prompt = load_curriculum_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    yield {"type": "progress", "stage": "generating", "message": "Generating curriculum..."}

    response = litellm.completion(
        model=model_id,
        max_tokens=16000,
        stream=True,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate curriculum for this class:\n\n```json\n{user_message}\n```"}
        ]
    )

    # Collect streamed content
    response_text = ""
    chunk_count = 0
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            response_text += chunk.choices[0].delta.content
            chunk_count += 1
            if chunk_count % 50 == 0:
                yield {"type": "progress", "stage": "generating", "message": f"Generating curriculum... ({len(response_text)} chars)"}

    yield {"type": "progress", "stage": "parsing", "message": "Parsing response..."}

    curriculum = _parse_json_response(response_text)
    yield {"type": "curriculum", "data": curriculum}


def _parse_json_response(response_text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    return json.loads(response_text)


async def generate_teacher_guide_async(
    teacher_input: dict[str, Any],
    model_id: str
) -> dict[str, Any]:
    """Async generation of teacher guide only."""
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")

    system_prompt = load_teacher_guide_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    response = await litellm.acompletion(
        model=model_id,
        max_tokens=8000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the teacher guide for this class:\n\n```json\n{user_message}\n```"}
        ]
    )

    return _parse_json_response(response.choices[0].message.content)


async def generate_student_materials_async(
    teacher_input: dict[str, Any],
    model_id: str
) -> dict[str, Any]:
    """Async generation of student materials only."""
    grade = teacher_input.get("grade")
    subject = teacher_input.get("subject")

    system_prompt = load_student_materials_prompt(grade=grade, subject=subject)
    user_message = json.dumps(teacher_input, indent=2)

    response = await litellm.acompletion(
        model=model_id,
        max_tokens=10000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the four differentiated student handouts for this class:\n\n```json\n{user_message}\n```"}
        ]
    )

    return _parse_json_response(response.choices[0].message.content)


def _merge_parallel_results(teacher_result: dict, student_result: dict) -> dict:
    """Merge teacher guide and student materials results into a single curriculum object."""
    return {
        "teacher_guide": teacher_result.get("teacher_guide", teacher_result),
        "student_materials": student_result.get("student_materials", student_result),
    }


async def generate_curriculum_parallel(
    teacher_input: dict[str, Any],
    model_key: str = None
) -> dict[str, Any]:
    """
    Generate curriculum using parallel LLM calls for teacher guide and student materials.

    This is faster than the single-call approach because both generations run concurrently.
    """
    model_id = _get_model_id(model_key)

    teacher_result, student_result = await asyncio.gather(
        generate_teacher_guide_async(teacher_input, model_id),
        generate_student_materials_async(teacher_input, model_id)
    )

    return _merge_parallel_results(teacher_result, student_result)


async def generate_curriculum_parallel_streaming(
    teacher_input: dict[str, Any],
    model_key: str = None
):
    """
    Generate curriculum with parallel LLM calls and streaming progress updates.

    Yields progress updates while running teacher guide and student materials
    generation in parallel.
    """
    model_id = _get_model_id(model_key)

    yield {"type": "progress", "stage": "loading", "message": "Loading standards..."}
    yield {"type": "progress", "stage": "generating", "message": "Generating curriculum (parallel)..."}

    teacher_task = asyncio.create_task(generate_teacher_guide_async(teacher_input, model_id))
    student_task = asyncio.create_task(generate_student_materials_async(teacher_input, model_id))

    teacher_done = False
    student_done = False
    teacher_result = None
    student_result = None

    while not (teacher_done and student_done):
        await asyncio.sleep(0.5)

        if not teacher_done and teacher_task.done():
            teacher_done = True
            teacher_result = teacher_task.result()
            yield {"type": "progress", "stage": "generating", "message": "Teacher guide complete, waiting for student materials..."}

        if not student_done and student_task.done():
            student_done = True
            student_result = student_task.result()
            message = "Student materials complete!" if teacher_done else "Student materials complete, waiting for teacher guide..."
            yield {"type": "progress", "stage": "generating", "message": message}

    yield {"type": "progress", "stage": "parsing", "message": "Merging results..."}
    yield {"type": "curriculum", "data": _merge_parallel_results(teacher_result, student_result)}
