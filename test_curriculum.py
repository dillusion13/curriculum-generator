"""
Test script for curriculum generation with pedagogical approaches.
"""
import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.curriculum_agent import generate_curriculum
from app.pdf_generator import generate_all_pdfs

def test_3_act_math():
    """Test curriculum generation with 3 Act Math approach."""

    teacher_input = {
        "grade": 6,
        "subject": "Math",
        "topic": "equivalent ratios",
        "readiness_levels": {
            "below": 5,
            "approaching": 8,
            "at": 10,
            "above": 4
        },
        "session_length_minutes": 20,
        "learning_goal_type": "introduce",
        "english_learners": {
            "emerging": 2,
            "expanding": 4,
            "bridging": 1
        },
        "group_format": "whole_class",
        "pedagogical_approach": "3_act_math"
    }

    print("=" * 60)
    print("Testing 3 Act Math Curriculum Generation")
    print("=" * 60)
    print(f"\nInput:\n{json.dumps(teacher_input, indent=2)}")
    print("\nGenerating curriculum... (this may take a minute)")

    try:
        curriculum = generate_curriculum(teacher_input)

        print("\n" + "=" * 60)
        print("GENERATED CURRICULUM")
        print("=" * 60)

        # Print metadata
        metadata = curriculum.get("teacher_guide", {}).get("metadata", {})
        print(f"\nTitle: {metadata.get('title', 'N/A')}")
        print(f"Pedagogical Approach: {metadata.get('pedagogical_approach', {})}")

        # Print session structure phases
        session = curriculum.get("teacher_guide", {}).get("session_structure", {})
        phases = session.get("phases", [])

        print(f"\nSession Phases ({len(phases)} phases):")
        for i, phase in enumerate(phases, 1):
            print(f"  {i}. {phase.get('name', 'Unnamed')} - {phase.get('duration_minutes', '?')} min")
            print(f"     {phase.get('description', '')[:80]}...")

        # Print UDL alignment
        udl = curriculum.get("teacher_guide", {}).get("udl_alignment", {})
        if udl:
            print(f"\nUDL Alignment:")
            print(f"  Summary: {udl.get('summary', 'N/A')[:100]}...")
            for principle in ["engagement", "representation", "action_expression"]:
                p_data = udl.get(principle, {})
                if p_data:
                    checkpoints = p_data.get("checkpoints_addressed", [])
                    print(f"  {principle.upper()}: {checkpoints}")
        else:
            print("\nWARNING: No UDL alignment found in output!")

        # Save full curriculum to file for inspection
        output_path = Path(__file__).parent / "outputs" / "test_3_act_curriculum.json"
        with open(output_path, "w") as f:
            json.dump(curriculum, f, indent=2)
        print(f"\nFull curriculum saved to: {output_path}")

        # Generate PDFs
        print("\nGenerating PDFs...")
        pdf_files = generate_all_pdfs(curriculum, "test_3act", str(Path(__file__).parent / "outputs"))
        print(f"Generated {len(pdf_files)} PDFs:")
        for pdf in pdf_files:
            print(f"  - {pdf['name']}: {pdf['filename']}")

        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return curriculum

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_5e_science():
    """Test curriculum generation with 5E Lesson approach."""

    teacher_input = {
        "grade": 7,
        "subject": "Science",
        "topic": "cell division",
        "readiness_levels": {
            "below": 4,
            "approaching": 7,
            "at": 12,
            "above": 5
        },
        "session_length_minutes": 20,
        "learning_goal_type": "introduce",
        "english_learners": {
            "emerging": 1,
            "expanding": 3,
            "bridging": 2
        },
        "group_format": "small_group",
        "pedagogical_approach": "5e_lessons"
    }

    print("\n" + "=" * 60)
    print("Testing 5E Lesson Curriculum Generation")
    print("=" * 60)
    print(f"\nInput:\n{json.dumps(teacher_input, indent=2)}")
    print("\nGenerating curriculum... (this may take a minute)")

    try:
        curriculum = generate_curriculum(teacher_input)

        print("\n" + "=" * 60)
        print("GENERATED CURRICULUM")
        print("=" * 60)

        # Print metadata
        metadata = curriculum.get("teacher_guide", {}).get("metadata", {})
        print(f"\nTitle: {metadata.get('title', 'N/A')}")
        print(f"Pedagogical Approach: {metadata.get('pedagogical_approach', {})}")

        # Print session structure phases
        session = curriculum.get("teacher_guide", {}).get("session_structure", {})
        phases = session.get("phases", [])

        print(f"\nSession Phases ({len(phases)} phases):")
        for i, phase in enumerate(phases, 1):
            print(f"  {i}. {phase.get('name', 'Unnamed')} - {phase.get('duration_minutes', '?')} min")
            print(f"     {phase.get('description', '')[:80]}...")

        # Save full curriculum to file for inspection
        output_path = Path(__file__).parent / "outputs" / "test_5e_curriculum.json"
        with open(output_path, "w") as f:
            json.dump(curriculum, f, indent=2)
        print(f"\nFull curriculum saved to: {output_path}")

        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return curriculum

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_model_comparison():
    """Test curriculum generation with both Claude and Gemini models."""

    teacher_input = {
        "grade": 6,
        "subject": "Math",
        "topic": "equivalent ratios",
        "session_length_minutes": 15,
        "learning_goal_type": "practice",
        "group_format": "small_group",
    }

    models = ["claude-sonnet-4.5", "gemini-3-pro"]
    results = {}

    for model in models:
        print("\n" + "=" * 60)
        print(f"Testing with {model.upper()}")
        print("=" * 60)
        print(f"\nInput:\n{json.dumps(teacher_input, indent=2)}")
        print("\nGenerating curriculum... (this may take a minute)")

        try:
            curriculum = generate_curriculum(teacher_input, model_key=model)
            results[model] = curriculum

            # Print key info
            metadata = curriculum.get("teacher_guide", {}).get("metadata", {})
            print(f"\nTitle: {metadata.get('title', 'N/A')}")

            # Print session structure phases
            session = curriculum.get("teacher_guide", {}).get("session_structure", {})
            phases = session.get("phases", [])
            print(f"\nSession Phases ({len(phases)} phases):")
            for i, phase in enumerate(phases, 1):
                print(f"  {i}. {phase.get('name', 'Unnamed')} - {phase.get('duration_minutes', '?')} min")

            # Print UDL alignment
            udl = curriculum.get("teacher_guide", {}).get("udl_alignment", {})
            if udl:
                print(f"\nUDL Checkpoints:")
                for principle in ["engagement", "representation", "action_expression"]:
                    p_data = udl.get(principle, {})
                    if p_data:
                        checkpoints = p_data.get("checkpoints_addressed", [])
                        print(f"  {principle}: {checkpoints}")

            # Save to file
            output_path = Path(__file__).parent / "outputs" / f"test_{model.replace('.', '_')}_curriculum.json"
            with open(output_path, "w") as f:
                json.dump(curriculum, f, indent=2)
            print(f"\nSaved to: {output_path}")

            # Generate PDF
            pdf_files = generate_all_pdfs(curriculum, f"test_{model.replace('.', '_')}", str(Path(__file__).parent / "outputs"))
            print(f"Generated PDF: {pdf_files[0]['filename']}")

        except Exception as e:
            print(f"\nERROR with {model}: {e}")
            import traceback
            traceback.print_exc()
            results[model] = None

    # Comparison summary
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    for model, curriculum in results.items():
        if curriculum:
            metadata = curriculum.get("teacher_guide", {}).get("metadata", {})
            phases = curriculum.get("teacher_guide", {}).get("session_structure", {}).get("phases", [])
            print(f"\n{model}:")
            print(f"  Title: {metadata.get('title', 'N/A')[:50]}...")
            print(f"  Phases: {len(phases)}")
            print(f"  Phase names: {[p.get('name', '?') for p in phases]}")
        else:
            print(f"\n{model}: FAILED")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test curriculum generation")
    parser.add_argument("--approach", choices=["3_act_math", "5e_lessons", "both"],
                        default="3_act_math", help="Which approach to test")
    parser.add_argument("--compare-models", action="store_true", help="Compare Claude vs Gemini")

    args = parser.parse_args()

    if args.compare_models:
        test_model_comparison()
    elif args.approach == "3_act_math":
        test_3_act_math()
    elif args.approach == "5e_lessons":
        test_5e_science()
    else:
        test_3_act_math()
        test_5e_science()
