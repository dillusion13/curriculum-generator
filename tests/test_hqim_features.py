"""
Tests for HQIM Feature Updates.

Tests session length validation, multi-day support, and DOCX generation.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError


class TestSessionLength:
    """Verify session length validation."""

    def test_valid_session_lengths(self):
        """All new session lengths should be accepted."""
        from app.main import CurriculumRequest

        valid_lengths = [10, 15, 20, 30, 45, 60, 90, 120]
        for minutes in valid_lengths:
            req = CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Fractions",
                session_length=minutes
            )
            assert req.session_length == minutes

    def test_session_length_below_minimum_rejected(self):
        """Session length below 5 min should fail."""
        from app.main import CurriculumRequest

        with pytest.raises(ValidationError):
            CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Test",
                session_length=4
            )

    def test_session_length_above_maximum_rejected(self):
        """Session length above 120 min should fail."""
        from app.main import CurriculumRequest

        with pytest.raises(ValidationError):
            CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Test",
                session_length=121
            )

    def test_default_session_length_is_45(self):
        """Default session length should be 45 minutes."""
        from app.main import CurriculumRequest

        req = CurriculumRequest(
            grade=5,
            subject="Math",
            topic="Fractions"
        )
        assert req.session_length == 45


class TestMultiDay:
    """Verify multi-day support."""

    def test_valid_num_days(self):
        """1-3 days should be accepted."""
        from app.main import CurriculumRequest

        for days in [1, 2, 3]:
            req = CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Fractions",
                num_days=days
            )
            assert req.num_days == days

    def test_num_days_above_maximum_rejected(self):
        """More than 3 days should fail."""
        from app.main import CurriculumRequest

        with pytest.raises(ValidationError):
            CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Test",
                num_days=4
            )

    def test_num_days_zero_rejected(self):
        """Zero days should fail."""
        from app.main import CurriculumRequest

        with pytest.raises(ValidationError):
            CurriculumRequest(
                grade=5,
                subject="Math",
                topic="Test",
                num_days=0
            )

    def test_default_num_days_is_1(self):
        """Default num_days should be 1."""
        from app.main import CurriculumRequest

        req = CurriculumRequest(
            grade=5,
            subject="Math",
            topic="Fractions"
        )
        assert req.num_days == 1


class TestMaxTokensCalculation:
    """Test dynamic max tokens calculation for multi-day."""

    def test_single_day_tokens(self):
        """Single day should use base tokens."""
        from app.curriculum_agent import _calculate_max_tokens

        assert _calculate_max_tokens(1) == 16000

    def test_two_day_tokens(self):
        """Two days should add 8000 tokens."""
        from app.curriculum_agent import _calculate_max_tokens

        assert _calculate_max_tokens(2) == 24000

    def test_three_day_tokens(self):
        """Three days should add 16000 tokens."""
        from app.curriculum_agent import _calculate_max_tokens

        assert _calculate_max_tokens(3) == 32000


class TestDocxGeneration:
    """Verify DOCX output generation."""

    @pytest.fixture
    def sample_curriculum(self):
        """Single-day curriculum fixture."""
        return {
            "teacher_guide": {
                "metadata": {
                    "title": "Test Lesson",
                    "grade": 5,
                    "subject": "Math",
                    "topic": "Fractions",
                    "duration_minutes": 45,
                    "standards_addressed": ["5.NF.A.1"]
                },
                "learning_objectives": [
                    {"objective": "Understand fractions", "success_criteria": "Can identify fractions"}
                ],
                "session_structure": {
                    "phases": [
                        {"name": "Intro", "duration_minutes": 10, "description": "Introduction"}
                    ],
                    "exit_assessment": {"type": "Quick check", "description": "Exit ticket"}
                },
                "materials_list": ["Whiteboard", "Markers"]
            },
            "student_materials": {
                "below_level": {
                    "header": {"title": "Below Level", "student_objective": "Learn fractions", "i_can_statement": "I can identify fractions"},
                    "vocabulary": [{"term": "Fraction", "definition": "A part of a whole"}]
                },
                "approaching_level": {
                    "header": {"title": "Approaching Level", "student_objective": "Learn fractions", "i_can_statement": "I can work with fractions"}
                },
                "at_level": {
                    "header": {"title": "At Level", "student_objective": "Master fractions", "i_can_statement": "I can add fractions"}
                },
                "above_level": {
                    "header": {"title": "Above Level", "student_objective": "Extend fractions", "i_can_statement": "I can multiply fractions"}
                }
            }
        }

    @pytest.fixture
    def sample_3day_curriculum(self):
        """3-day curriculum fixture."""
        return {
            "teacher_guide": {
                "metadata": {
                    "title": "Fraction Unit",
                    "grade": 5,
                    "subject": "Math",
                    "topic": "Fractions",
                    "total_days": 3,
                    "duration_minutes_per_day": 45
                },
                "unit_overview": {
                    "learning_arc": "Introduction to mastery",
                    "essential_questions": ["What are fractions?"]
                },
                "days": [
                    {
                        "day": 1,
                        "title": "Day 1 - Introduction",
                        "metadata": {"title": "Intro", "duration_minutes": 45},
                        "session_structure": {"phases": []}
                    },
                    {
                        "day": 2,
                        "title": "Day 2 - Practice",
                        "metadata": {"title": "Practice", "duration_minutes": 45},
                        "session_structure": {"phases": []}
                    },
                    {
                        "day": 3,
                        "title": "Day 3 - Assessment",
                        "metadata": {"title": "Assessment", "duration_minutes": 45},
                        "session_structure": {"phases": []}
                    }
                ]
            },
            "student_materials": {
                "below_level": {
                    "days": [
                        {"day": 1, "header": {"title": "Day 1"}},
                        {"day": 2, "header": {"title": "Day 2"}},
                        {"day": 3, "header": {"title": "Day 3"}}
                    ]
                },
                "approaching_level": {
                    "days": [{"day": 1}, {"day": 2}, {"day": 3}]
                },
                "at_level": {
                    "days": [{"day": 1}, {"day": 2}, {"day": 3}]
                },
                "above_level": {
                    "days": [{"day": 1}, {"day": 2}, {"day": 3}]
                }
            }
        }

    def test_docx_generates_without_error(self, sample_curriculum):
        """DOCX generation should not raise exceptions."""
        from app.docx_generator import generate_combined_document

        doc = generate_combined_document(sample_curriculum)
        assert doc is not None

    def test_docx_generates_for_multiday(self, sample_3day_curriculum):
        """Multi-day DOCX generation should not raise exceptions."""
        from app.docx_generator import generate_combined_document

        doc = generate_combined_document(sample_3day_curriculum)
        assert doc is not None

    def test_save_combined_document(self, sample_curriculum, tmp_path):
        """Saving combined document should create a file."""
        from app.docx_generator import save_combined_document

        filename = save_combined_document(sample_curriculum, str(tmp_path))
        assert filename.endswith(".docx")

        filepath = tmp_path / filename
        assert filepath.exists()
        assert filepath.stat().st_size > 0


class TestBuildTeacherInput:
    """Test _build_teacher_input function."""

    def test_includes_num_days(self):
        """Teacher input should include num_days."""
        from app.main import _build_teacher_input

        result = _build_teacher_input(
            grade=5,
            subject="Math",
            topic="Fractions",
            session_length=45,
            num_days=2,
            learning_goal_type="introduce",
            group_format="whole_class"
        )

        assert result["num_days"] == 2
        assert result["session_length_minutes"] == 45
