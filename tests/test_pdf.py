"""
Tests for PDF generation.
"""
import pytest
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_generator import (
    create_teacher_guide,
    create_student_handout,
    generate_all_pdfs,
    create_workspace_box,
    create_quick_reference_box,
    create_differentiation_at_a_glance,
)
from app.pdf_styles import COLORS, LEVEL_COLORS, get_base_styles


class TestPdfStyles:
    """Tests for shared PDF styles module."""

    def test_colors_defined(self):
        """Should have all required colors defined."""
        required_colors = [
            "ink_900", "ink_700", "ink_500",
            "navy_700", "navy_100",
            "gold_600", "gold_100",
            "below", "below_light",
            "approaching", "approaching_light",
            "at", "at_light",
            "above", "above_light",
            "white",
        ]
        for color in required_colors:
            assert color in COLORS, f"Missing color: {color}"

    def test_level_colors_mapping(self):
        """Should have color mappings for all readiness levels."""
        expected_levels = ["below_level", "approaching_level", "at_level", "above_level"]
        for level in expected_levels:
            assert level in LEVEL_COLORS, f"Missing level: {level}"

    def test_get_base_styles_returns_styles_and_accent(self):
        """Should return styles dict and accent colors."""
        styles, accent, accent_light = get_base_styles()

        assert styles is not None
        assert "Title" in styles
        assert "BodyText" in styles
        assert accent is not None
        assert accent_light is not None

    def test_get_base_styles_with_level(self):
        """Should customize accent colors based on level."""
        styles_below, accent_below, _ = get_base_styles("below_level")
        styles_at, accent_at, _ = get_base_styles("at_level")

        # Accents should be different for different levels
        assert accent_below != accent_at


@pytest.fixture
def sample_teacher_guide_data():
    """Sample teacher guide data for testing."""
    return {
        "metadata": {
            "title": "Test Lesson: Equivalent Ratios",
            "grade": 6,
            "subject": "Math",
            "topic": "equivalent ratios",
            "duration_minutes": 15,
            "standards_addressed": ["6.RP.A.1", "6.RP.A.2"],
            "learning_goal_type": "practice",
            "group_format": "small_group",
            "pedagogical_approach": {
                "id": "5e_lessons",
                "name": "5E Lesson Model",
                "rationale": "Great for exploration"
            }
        },
        "learning_objectives": [
            {
                "objective": "Students will identify equivalent ratios",
                "success_criteria": "Students can generate 3 equivalent ratios"
            }
        ],
        "session_structure": {
            "phases": [
                {
                    "name": "Engage",
                    "duration_minutes": 3,
                    "description": "Hook activity",
                    "teacher_actions": "Present scenario",
                    "student_actions": "Discuss",
                    "key_points": ["Connect to prior knowledge"]
                },
                {
                    "name": "Explore",
                    "duration_minutes": 5,
                    "description": "Investigation",
                }
            ]
        },
        "differentiation_overview": {
            "below_level": {
                "focus": "Building foundational skills",
                "key_scaffolds": ["Visual aids", "Manipulatives"],
                "monitor_for": "Confusion with multiplication"
            },
            "approaching_level": {
                "focus": "Strengthening understanding",
                "key_scaffolds": ["Hints"],
                "monitor_for": "Procedural errors"
            },
            "at_level": {
                "focus": "Grade-level mastery",
                "key_scaffolds": ["Minimal"],
                "monitor_for": "Efficiency"
            },
            "above_level": {
                "focus": "Extension",
                "key_scaffolds": ["Open-ended challenges"],
                "monitor_for": "Complexity of thinking"
            }
        },
        "materials_list": ["Whiteboard", "Markers", "Handouts"],
        "common_misconceptions": [
            {
                "misconception": "Adding same number makes equivalent",
                "how_to_address": "Use visual models"
            }
        ],
        "udl_alignment": {
            "summary": "Lesson incorporates multiple means of engagement",
            "engagement": {
                "checkpoints_addressed": ["7.1", "8.2"],
                "how_addressed": "Student choice in examples"
            },
            "representation": {
                "checkpoints_addressed": ["1.2", "2.1"],
                "how_addressed": "Visual and verbal presentation"
            },
            "action_expression": {
                "checkpoints_addressed": ["4.1", "5.1"],
                "how_addressed": "Multiple response options"
            }
        }
    }


@pytest.fixture
def sample_student_handout_data():
    """Sample student handout data for testing."""
    return {
        "header": {
            "title": "Equivalent Ratios Practice",
            "student_objective": "Learn about equivalent ratios",
            "i_can_statement": "I can find equivalent ratios"
        },
        "vocabulary": [
            {
                "term": "ratio",
                "definition": "A comparison of two numbers",
                "example": "2:3"
            }
        ],
        "worked_example": {
            "problem": "Find two equivalent ratios for 2:3",
            "steps": [
                {
                    "step_number": 1,
                    "action": "Multiply both parts by 2",
                    "result": "4:6"
                }
            ],
            "solution": "4:6 and 6:9"
        },
        "guided_practice": [
            {
                "problem": "Find an equivalent ratio for 3:5",
                "scaffold": "Try multiplying by 2",
                "workspace": True
            }
        ],
        "independent_practice": [
            {
                "problem": "Find two equivalent ratios for 4:7",
                "workspace": True
            }
        ],
        "word_bank": ["ratio", "equivalent", "multiply"],
        "sentence_frames": [
            "The ratio of ___ to ___ is ___.",
            "An equivalent ratio is ___."
        ],
        "reflection": {
            "prompt": "What did you learn today?",
            "sentence_starter": "Today I learned..."
        }
    }


class TestTeacherGuide:
    """Tests for teacher guide PDF generation."""

    def test_generates_pdf_without_error(self, sample_teacher_guide_data):
        """Should generate teacher guide PDF without errors."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        result = create_teacher_guide(sample_teacher_guide_data, output_path, include_udl_docs=False)

        assert result == output_path
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0

        # Cleanup
        Path(output_path).unlink()

    def test_generates_pdf_with_udl_docs(self, sample_teacher_guide_data):
        """Should generate teacher guide with UDL documentation."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        result = create_teacher_guide(sample_teacher_guide_data, output_path, include_udl_docs=True)

        assert result == output_path
        assert Path(output_path).exists()

        # Cleanup
        Path(output_path).unlink()

    def test_handles_minimal_data(self):
        """Should handle minimal teacher guide data."""
        minimal_data = {
            "metadata": {"title": "Test"},
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        result = create_teacher_guide(minimal_data, output_path)
        assert Path(output_path).exists()

        # Cleanup
        Path(output_path).unlink()


class TestStudentHandout:
    """Tests for student handout PDF generation."""

    @pytest.mark.parametrize("level", [
        "below_level",
        "approaching_level",
        "at_level",
        "above_level"
    ])
    def test_generates_pdf_for_all_levels(self, sample_student_handout_data, level):
        """Should generate student handout for all readiness levels."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        result = create_student_handout(sample_student_handout_data, level, output_path)

        assert result == output_path
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0

        # Cleanup
        Path(output_path).unlink()

    def test_handles_minimal_data(self):
        """Should handle minimal student handout data."""
        minimal_data = {
            "header": {"title": "Test"}
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        result = create_student_handout(minimal_data, "at_level", output_path)
        assert Path(output_path).exists()

        # Cleanup
        Path(output_path).unlink()


class TestHelperComponents:
    """Tests for PDF helper components."""

    def test_create_workspace_box(self):
        """Should create workspace box without error."""
        box = create_workspace_box(lines=4)
        assert box is not None

    def test_create_workspace_box_custom_lines(self):
        """Should create workspace box with custom line count."""
        box = create_workspace_box(lines=6, accent_color=COLORS["gold_600"])
        assert box is not None

    def test_create_quick_reference_box(self):
        """Should create quick reference box from metadata."""
        meta = {
            "duration_minutes": 15,
            "grouping": "small_group",
            "pedagogical_approach": {"name": "5E Lesson"},
            "standards_addressed": ["6.RP.A.1"]
        }
        box = create_quick_reference_box(meta, {})
        assert box is not None

    def test_create_differentiation_at_a_glance(self):
        """Should create differentiation summary table."""
        diff = {
            "below_level": {"focus": "Foundation"},
            "approaching_level": {"focus": "Building"},
            "at_level": {"focus": "Mastery"},
            "above_level": {"focus": "Extension"},
        }
        table = create_differentiation_at_a_glance(diff)
        assert table is not None


class TestGenerateAllPdfs:
    """Tests for batch PDF generation."""

    @pytest.fixture
    def sample_curriculum(self, sample_teacher_guide_data, sample_student_handout_data):
        """Complete curriculum data for testing."""
        return {
            "teacher_guide": sample_teacher_guide_data,
            "student_materials": {
                "below_level": sample_student_handout_data,
                "approaching_level": sample_student_handout_data,
                "at_level": sample_student_handout_data,
                "above_level": sample_student_handout_data,
            }
        }

    def test_generates_all_pdfs(self, sample_curriculum):
        """Should generate all 5 PDFs (1 teacher + 4 student)."""
        with tempfile.TemporaryDirectory() as output_dir:
            files = generate_all_pdfs(
                sample_curriculum,
                session_id="test123",
                output_dir=output_dir,
                include_udl_docs=False
            )

            # Should return 5 file info dicts
            assert len(files) == 5

            # Each file should exist
            for file_info in files:
                filepath = Path(output_dir) / file_info["filename"]
                assert filepath.exists(), f"File not found: {filepath}"

    def test_generates_with_udl_docs(self, sample_curriculum):
        """Should generate PDFs with UDL documentation enabled."""
        with tempfile.TemporaryDirectory() as output_dir:
            files = generate_all_pdfs(
                sample_curriculum,
                session_id="test456",
                output_dir=output_dir,
                include_udl_docs=True
            )

            assert len(files) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
