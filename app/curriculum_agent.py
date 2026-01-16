"""
Curriculum Agent - LLM integration for curriculum generation.
Supports multiple providers via LiteLLM.
"""
import json
import os
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

DEFAULT_MODEL = "claude-sonnet-4.5"


@lru_cache(maxsize=1)
def load_standards_json() -> str:
    """Load and combine all standards JSON files."""
    files_dir = Path(__file__).parent.parent / "files"

    standards_data = {}

    # Load each standards file
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
                # Use filename (without extension) as key
                key = filename.replace(".json", "")
                standards_data[key] = data

    return json.dumps(standards_data, indent=2)


@lru_cache(maxsize=1)
def load_pedagogical_approaches_json() -> str:
    """Load the pedagogical approaches JSON file."""
    files_dir = Path(__file__).parent.parent / "files"
    filepath = files_dir / "pedagogical_approaches.json"

    if filepath.exists():
        with open(filepath, "r") as f:
            return f.read()
    return "{}"


@lru_cache(maxsize=1)
def load_curriculum_prompt() -> str:
    """Load the curriculum agent system prompt."""
    prompt_path = Path(__file__).parent.parent / "files" / "curriculum_agent_prompt.md"

    with open(prompt_path, "r") as f:
        prompt = f.read()

    # Inject standards JSON into the prompt
    standards_json = load_standards_json()
    prompt = prompt.replace("{{STANDARDS_JSON}}", standards_json)

    # Inject pedagogical approaches JSON into the prompt
    pedagogical_json = load_pedagogical_approaches_json()
    prompt = prompt.replace("{{PEDAGOGICAL_APPROACHES_JSON}}", pedagogical_json)

    return prompt


def generate_curriculum(teacher_input: dict[str, Any], model_key: str = None) -> dict[str, Any]:
    """
    Generate curriculum using LiteLLM (supports multiple providers).

    Args:
        teacher_input: Dictionary with teacher's class information
        model_key: Key from AVAILABLE_MODELS (e.g., "claude-sonnet-4.5", "gemini-3-pro")

    Returns:
        Dictionary containing teacher_guide and student_materials
    """
    # Get model configuration
    if model_key is None:
        model_key = DEFAULT_MODEL

    model_config = AVAILABLE_MODELS.get(model_key)
    if not model_config:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")

    model_id = model_config["id"]

    system_prompt = load_curriculum_prompt()
    user_message = json.dumps(teacher_input, indent=2)

    # Use LiteLLM for unified API across providers
    response = litellm.completion(
        model=model_id,
        max_tokens=16000,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Generate curriculum for this class:\n\n```json\n{user_message}\n```"
            }
        ]
    )

    # Extract the response text
    response_text = response.choices[0].message.content

    # Parse JSON from response (handle potential markdown code blocks)
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    curriculum = json.loads(response_text)

    return curriculum
