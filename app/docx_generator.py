"""
DOCX Generator - Create editable Word documents from curriculum JSON.
Produces a single combined document with Teacher Guide and all Student Materials.
"""
from pathlib import Path
from typing import Any, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT


# Level display names
LEVEL_NAMES = {
    "below_level": "Below Level",
    "approaching_level": "Approaching Level",
    "at_level": "At Level",
    "above_level": "Above Level",
}


def _add_styled_heading(doc: Document, text: str, level: int = 1) -> None:
    """Add a styled heading to the document."""
    heading = doc.add_heading(text, level=level)
    if level == 1:
        heading.runs[0].font.size = Pt(24)
        heading.runs[0].font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)
    elif level == 2:
        heading.runs[0].font.size = Pt(18)
        heading.runs[0].font.color.rgb = RGBColor(0x34, 0x49, 0x5E)


def _add_section_header(doc: Document, title: str) -> None:
    """Add a section header with some styling."""
    para = doc.add_paragraph()
    run = para.add_run(title.upper())
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)
    para.space_before = Pt(12)
    para.space_after = Pt(6)


def _add_key_value(doc: Document, key: str, value: str) -> None:
    """Add a key-value pair."""
    para = doc.add_paragraph()
    key_run = para.add_run(f"{key}: ")
    key_run.bold = True
    para.add_run(str(value))


def _add_bullet_list(doc: Document, items: list) -> None:
    """Add a bullet list."""
    for item in items:
        para = doc.add_paragraph(str(item), style='List Bullet')


def _add_numbered_list(doc: Document, items: list) -> None:
    """Add a numbered list."""
    for item in items:
        para = doc.add_paragraph(str(item), style='List Number')


def _add_table(doc: Document, headers: list, rows: list) -> None:
    """Add a table with headers and rows."""
    if not rows:
        return
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'

    # Header row
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
        header_cells[i].paragraphs[0].runs[0].bold = True

    # Data rows
    for row_idx, row_data in enumerate(rows):
        row_cells = table.rows[row_idx + 1].cells
        for col_idx, cell_data in enumerate(row_data):
            row_cells[col_idx].text = str(cell_data) if cell_data else ""


def _add_info_box(doc: Document, title: str, content: str) -> None:
    """Add an info box (as a simple table with background)."""
    table = doc.add_table(rows=1, cols=1)
    table.style = 'Table Grid'
    cell = table.rows[0].cells[0]
    para = cell.paragraphs[0]
    run = para.add_run(f"{title}: ")
    run.bold = True
    para.add_run(content)


def generate_teacher_guide_section(doc: Document, teacher_guide: dict, day_num: Optional[int] = None) -> None:
    """Generate teacher guide section in the document."""
    meta = teacher_guide.get("metadata", {})

    # Title
    title = meta.get("title", "Lesson Plan")
    if day_num:
        title = f"Day {day_num}: {title}"
    _add_styled_heading(doc, title, level=1)

    # Metadata box
    _add_section_header(doc, "Lesson Overview")
    _add_key_value(doc, "Grade", meta.get("grade", ""))
    _add_key_value(doc, "Subject", meta.get("subject", ""))
    _add_key_value(doc, "Topic", meta.get("topic", ""))
    _add_key_value(doc, "Duration", f"{meta.get('duration_minutes', '')} minutes")

    standards = meta.get("standards_addressed", [])
    if standards:
        _add_key_value(doc, "Standards", ", ".join(standards))

    approach = meta.get("pedagogical_approach", {})
    if isinstance(approach, dict):
        _add_key_value(doc, "Approach", approach.get("name", ""))
        if approach.get("rationale"):
            doc.add_paragraph(f"Rationale: {approach['rationale']}")

    doc.add_paragraph()

    # Learning Objectives
    objectives = teacher_guide.get("learning_objectives", [])
    if objectives:
        _add_section_header(doc, "Learning Objectives")
        for obj in objectives:
            if isinstance(obj, dict):
                para = doc.add_paragraph()
                para.add_run(obj.get("objective", "")).bold = True
                if obj.get("success_criteria"):
                    doc.add_paragraph(f"Success Criteria: {obj['success_criteria']}", style='List Bullet')
            else:
                doc.add_paragraph(str(obj), style='List Bullet')
        doc.add_paragraph()

    # Session Structure / Phases
    session = teacher_guide.get("session_structure", {})
    phases = session.get("phases", [])
    if phases:
        _add_section_header(doc, "Session Structure")
        for i, phase in enumerate(phases, 1):
            # Phase header
            para = doc.add_paragraph()
            phase_name = phase.get("name", f"Phase {i}")
            duration = phase.get("duration_minutes", "")
            run = para.add_run(f"{phase_name}")
            run.bold = True
            run.font.size = Pt(12)
            if duration:
                para.add_run(f" ({duration} min)")

            # Phase details
            if phase.get("description"):
                doc.add_paragraph(phase["description"])
            if phase.get("teacher_actions"):
                doc.add_paragraph(f"Teacher Actions: {phase['teacher_actions']}")
            if phase.get("student_actions"):
                doc.add_paragraph(f"Student Actions: {phase['student_actions']}")
            if phase.get("key_points"):
                doc.add_paragraph("Key Points:")
                _add_bullet_list(doc, phase["key_points"])
            if phase.get("differentiation_notes"):
                doc.add_paragraph(f"Differentiation: {phase['differentiation_notes']}")
            doc.add_paragraph()

    # Exit Assessment
    exit_assess = session.get("exit_assessment", {})
    if exit_assess:
        _add_section_header(doc, "Exit Assessment")
        if exit_assess.get("type"):
            _add_key_value(doc, "Type", exit_assess["type"])
        if exit_assess.get("description"):
            doc.add_paragraph(exit_assess["description"])
        doc.add_paragraph()

    # Differentiation Overview
    diff = teacher_guide.get("differentiation_overview", {})
    if diff:
        _add_section_header(doc, "Differentiation Overview")
        for level_key, level_data in diff.items():
            if isinstance(level_data, dict):
                level_name = LEVEL_NAMES.get(level_key, level_key.replace("_", " ").title())
                para = doc.add_paragraph()
                para.add_run(level_name).bold = True
                if level_data.get("focus"):
                    doc.add_paragraph(f"Focus: {level_data['focus']}")
                if level_data.get("key_scaffolds"):
                    doc.add_paragraph("Scaffolds:")
                    _add_bullet_list(doc, level_data["key_scaffolds"])
                if level_data.get("monitor_for"):
                    doc.add_paragraph(f"Monitor for: {level_data['monitor_for']}")
        doc.add_paragraph()

    # EL Support Summary
    el_support = teacher_guide.get("el_support_summary", {})
    if el_support:
        _add_section_header(doc, "English Learner Support")
        for el_level, support_data in el_support.items():
            if isinstance(support_data, dict):
                para = doc.add_paragraph()
                para.add_run(el_level.title()).bold = True
                if support_data.get("key_vocabulary_to_preteach"):
                    doc.add_paragraph("Pre-teach Vocabulary:")
                    _add_bullet_list(doc, support_data["key_vocabulary_to_preteach"])
                if support_data.get("visual_supports_needed"):
                    doc.add_paragraph("Visual Supports:")
                    _add_bullet_list(doc, support_data["visual_supports_needed"])
                if support_data.get("partner_recommendations"):
                    doc.add_paragraph(f"Partner Recommendations: {support_data['partner_recommendations']}")
        doc.add_paragraph()

    # Materials List
    materials = teacher_guide.get("materials_list", [])
    if materials:
        _add_section_header(doc, "Materials Needed")
        _add_bullet_list(doc, materials)
        doc.add_paragraph()

    # Common Misconceptions
    misconceptions = teacher_guide.get("common_misconceptions", [])
    if misconceptions:
        _add_section_header(doc, "Common Misconceptions")
        for misc in misconceptions:
            if isinstance(misc, dict):
                para = doc.add_paragraph()
                para.add_run(f"Misconception: ").bold = True
                para.add_run(misc.get("misconception", ""))
                doc.add_paragraph(f"How to Address: {misc.get('how_to_address', '')}")
            else:
                doc.add_paragraph(str(misc), style='List Bullet')
        doc.add_paragraph()

    # Discussion Prompts
    prompts = teacher_guide.get("discussion_prompts", [])
    if prompts:
        _add_section_header(doc, "Discussion Prompts")
        _add_numbered_list(doc, prompts)
        doc.add_paragraph()

    # Formative Assessment Ideas
    assessments = teacher_guide.get("formative_assessment_ideas", [])
    if assessments:
        _add_section_header(doc, "Formative Assessment Ideas")
        _add_bullet_list(doc, assessments)
        doc.add_paragraph()


def generate_student_material_section(
    doc: Document,
    level_key: str,
    level_data: dict,
    day_num: Optional[int] = None
) -> None:
    """Generate a student material section for one level."""
    level_name = LEVEL_NAMES.get(level_key, level_key.replace("_", " ").title())

    # Check for multi-day structure
    if "days" in level_data:
        # Multi-day format
        for day_data in level_data["days"]:
            day = day_data.get("day", 1)
            title = day_data.get("title", f"Day {day}")
            _add_styled_heading(doc, f"{level_name} - {title}", level=2)
            _generate_student_day_content(doc, day_data)
            doc.add_page_break()
    else:
        # Single-day format
        title = level_name
        if day_num:
            title = f"Day {day_num} - {level_name}"
        _add_styled_heading(doc, title, level=2)
        _generate_student_day_content(doc, level_data)


def _generate_student_day_content(doc: Document, data: dict) -> None:
    """Generate content for a single day of student materials."""
    # Header
    header = data.get("header", {})
    if header:
        if header.get("title"):
            doc.add_paragraph(header["title"]).alignment = WD_ALIGN_PARAGRAPH.CENTER
        if header.get("student_objective"):
            _add_key_value(doc, "Learning Goal", header["student_objective"])
        if header.get("i_can_statement"):
            para = doc.add_paragraph()
            run = para.add_run(header["i_can_statement"])
            run.italic = True
        doc.add_paragraph()

    # Vocabulary
    vocab = data.get("vocabulary", [])
    if vocab:
        _add_section_header(doc, "Vocabulary")
        for word in vocab:
            if isinstance(word, dict):
                para = doc.add_paragraph()
                para.add_run(word.get("term", "")).bold = True
                para.add_run(f": {word.get('definition', '')}")
                if word.get("example"):
                    doc.add_paragraph(f"Example: {word['example']}", style='List Bullet')
            else:
                doc.add_paragraph(str(word), style='List Bullet')
        doc.add_paragraph()

    # Worked Example
    worked = data.get("worked_example", {})
    if worked:
        _add_section_header(doc, "Worked Example")
        if worked.get("problem"):
            para = doc.add_paragraph()
            para.add_run("Problem: ").bold = True
            para.add_run(worked["problem"])

        steps = worked.get("steps", [])
        if steps:
            doc.add_paragraph("Steps:")
            for step in steps:
                if isinstance(step, dict):
                    step_num = step.get("step_number", "")
                    action = step.get("action", "")
                    result = step.get("result", "")
                    doc.add_paragraph(f"Step {step_num}: {action}", style='List Number')
                    if result:
                        doc.add_paragraph(f"Result: {result}")
                else:
                    doc.add_paragraph(str(step), style='List Number')

        # Handle solution_summary (used by at_level instead of detailed steps)
        if worked.get("solution_summary"):
            para = doc.add_paragraph()
            para.add_run("Solution: ").bold = True
            para.add_run(worked["solution_summary"])

        # Handle final solution if present
        if worked.get("solution"):
            para = doc.add_paragraph()
            para.add_run("Answer: ").bold = True
            para.add_run(worked["solution"])

        doc.add_paragraph()

    # Guided Practice
    guided = data.get("guided_practice", [])
    if guided:
        _add_section_header(doc, "Guided Practice")
        for i, item in enumerate(guided, 1):
            if isinstance(item, dict):
                problem = item.get("problem", item.get("prompt", ""))
                doc.add_paragraph(f"{i}. {problem}")
                # Support both 'scaffold' (below level) and 'hint' (approaching level)
                hint = item.get("scaffold") or item.get("hint")
                if hint:
                    doc.add_paragraph(f"Hint: {hint}")
                if item.get("workspace"):
                    doc.add_paragraph("[Work Space]")
                    doc.add_paragraph()
            else:
                doc.add_paragraph(f"{i}. {item}")
        doc.add_paragraph()

    # Independent Practice
    independent = data.get("independent_practice", [])
    if independent:
        _add_section_header(doc, "Independent Practice")
        for i, item in enumerate(independent, 1):
            if isinstance(item, dict):
                problem = item.get("problem", item.get("prompt", ""))
                doc.add_paragraph(f"{i}. {problem}")
                if item.get("workspace"):
                    doc.add_paragraph("[Work Space]")
                    doc.add_paragraph()
            else:
                doc.add_paragraph(f"{i}. {item}")
        doc.add_paragraph()

    # Practice Problems (alternative structure)
    practice = data.get("practice_problems", [])
    if practice:
        _add_section_header(doc, "Practice Problems")
        for i, item in enumerate(practice, 1):
            if isinstance(item, dict):
                problem = item.get("problem", "")
                doc.add_paragraph(f"{i}. {problem}")
                if item.get("workspace"):
                    doc.add_paragraph("[Work Space]")
                    doc.add_paragraph()
            else:
                doc.add_paragraph(f"{i}. {item}")
        doc.add_paragraph()

    # Graphic Organizer
    organizer = data.get("graphic_organizer", {})
    if organizer:
        _add_section_header(doc, "Graphic Organizer")
        if organizer.get("title"):
            doc.add_paragraph(organizer["title"])
        if organizer.get("type"):
            _add_key_value(doc, "Type", organizer["type"])
        # Could render table structure in the future
        doc.add_paragraph()

    # Sentence Frames
    frames = data.get("sentence_frames", [])
    if frames:
        _add_section_header(doc, "Sentence Frames")
        _add_bullet_list(doc, frames)
        doc.add_paragraph()

    # Word Bank
    word_bank = data.get("word_bank", [])
    if word_bank:
        _add_section_header(doc, "Word Bank")
        doc.add_paragraph(", ".join(word_bank))
        doc.add_paragraph()

    # Application Problem (at_level)
    app_problem = data.get("application_problem", {})
    if app_problem:
        _add_section_header(doc, "Application Problem")
        if app_problem.get("context"):
            doc.add_paragraph(app_problem["context"])
        if app_problem.get("question"):
            para = doc.add_paragraph()
            para.add_run("Question: ").bold = True
            para.add_run(app_problem["question"])
        if app_problem.get("workspace"):
            doc.add_paragraph("[Work Space]")
            doc.add_paragraph()
        doc.add_paragraph()

    # Extension Challenge
    extension = data.get("extension_challenge", {})
    if extension:
        _add_section_header(doc, "Extension Challenge")
        if extension.get("title"):
            para = doc.add_paragraph()
            para.add_run(extension["title"]).bold = True
        if extension.get("description"):
            doc.add_paragraph(extension["description"])
        if extension.get("guiding_questions"):
            doc.add_paragraph("Guiding Questions:")
            _add_bullet_list(doc, extension["guiding_questions"])
        doc.add_paragraph()

    # Reflection
    reflection = data.get("reflection", {})
    if reflection:
        _add_section_header(doc, "Reflection")
        if reflection.get("prompt"):
            doc.add_paragraph(reflection["prompt"])
        doc.add_paragraph("[Your Response]")
        doc.add_paragraph()
        doc.add_paragraph()


def generate_combined_document(curriculum: dict, include_udl: bool = False) -> Document:
    """Generate a single combined DOCX with all curriculum content.

    Structure:
    1. Teacher Guide (all days if multi-day)
    2. Student Materials - Below Level (all days)
    3. Student Materials - Approaching Level (all days)
    4. Student Materials - At Level (all days)
    5. Student Materials - Above Level (all days)
    """
    doc = Document()

    teacher_guide = curriculum.get("teacher_guide", {})
    student_materials = curriculum.get("student_materials", {})

    # Check if multi-day format (teacher guide has "days" array)
    is_multi_day = "days" in teacher_guide

    # ===== TEACHER GUIDE SECTION =====
    _add_styled_heading(doc, "Teacher Guide", level=1)

    if is_multi_day:
        # Multi-day teacher guide
        meta = teacher_guide.get("metadata", {})
        unit_overview = teacher_guide.get("unit_overview", {})

        # Unit title and overview
        doc.add_paragraph(meta.get("title", "Lesson Plan"))
        if unit_overview.get("learning_arc"):
            _add_key_value(doc, "Learning Arc", unit_overview["learning_arc"])
        if unit_overview.get("essential_questions"):
            doc.add_paragraph("Essential Questions:")
            _add_bullet_list(doc, unit_overview["essential_questions"])
        doc.add_paragraph()

        # Each day - merge top-level metadata with day-specific data
        top_meta = teacher_guide.get("metadata", {})
        for day_data in teacher_guide.get("days", []):
            day_num = day_data.get("day", 1)
            # Create merged data: day-specific metadata takes precedence, but inherit from top-level
            day_meta = day_data.get("metadata", {})
            merged_meta = {
                "title": day_data.get("title", day_meta.get("title", f"Day {day_num}")),
                "grade": day_meta.get("grade", top_meta.get("grade")),
                "subject": day_meta.get("subject", top_meta.get("subject")),
                "topic": day_meta.get("topic", top_meta.get("topic")),
                "duration_minutes": day_meta.get("duration_minutes", top_meta.get("duration_minutes_per_day", top_meta.get("duration_minutes"))),
                "standards_addressed": day_meta.get("standards_addressed", top_meta.get("standards_addressed", [])),
                "pedagogical_approach": day_meta.get("pedagogical_approach", top_meta.get("pedagogical_approach")),
            }
            # Create merged day data with proper metadata
            merged_day = {**day_data, "metadata": merged_meta}
            generate_teacher_guide_section(doc, merged_day, day_num=day_num)
            doc.add_page_break()

        # Shared sections (differentiation, EL support, etc.)
        diff = teacher_guide.get("differentiation_overview", {})
        if diff:
            _add_section_header(doc, "Differentiation Overview (All Days)")
            for level_key, level_data in diff.items():
                if isinstance(level_data, dict):
                    level_name = LEVEL_NAMES.get(level_key, level_key.replace("_", " ").title())
                    para = doc.add_paragraph()
                    para.add_run(level_name).bold = True
                    if level_data.get("focus"):
                        doc.add_paragraph(f"Focus: {level_data['focus']}")
                    if level_data.get("key_scaffolds"):
                        _add_bullet_list(doc, level_data["key_scaffolds"])
            doc.add_page_break()
    else:
        # Single-day teacher guide
        generate_teacher_guide_section(doc, teacher_guide)
        doc.add_page_break()

    # ===== STUDENT MATERIALS SECTIONS =====
    _add_styled_heading(doc, "Student Materials", level=1)
    doc.add_paragraph("The following pages contain differentiated student handouts for all readiness levels.")
    doc.add_page_break()

    # Generate each level
    levels_order = ["below_level", "approaching_level", "at_level", "above_level"]
    for level_key in levels_order:
        level_data = student_materials.get(level_key, {})
        if level_data:
            generate_student_material_section(doc, level_key, level_data)
            doc.add_page_break()

    return doc


def save_combined_document(curriculum: dict, output_path: str, include_udl: bool = False) -> str:
    """Generate and save a combined DOCX document.

    Args:
        curriculum: The curriculum dictionary from LLM
        output_path: Directory to save the file
        include_udl: Whether to include UDL documentation (future)

    Returns:
        Path to the saved file
    """
    doc = generate_combined_document(curriculum, include_udl)

    # Generate filename
    teacher_guide = curriculum.get("teacher_guide", {})
    meta = teacher_guide.get("metadata", {})

    title = meta.get("title", "Lesson")
    # Clean title for filename
    clean_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    clean_title = clean_title.replace(" ", "_")[:50]

    filename = f"{clean_title}_lesson_plan.docx"
    filepath = Path(output_path) / filename

    doc.save(str(filepath))
    return filename
