"""
PDF Generator - Create polished, print-ready PDFs from curriculum JSON.
Matches the "Scholarly Modern" frontend design aesthetic.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

# Import shared styles
from .pdf_styles import (
    COLORS,
    LEVEL_COLORS,
    get_base_styles as get_styles,
    create_section_header,
    create_info_box,
    create_divider,
    add_bullet_list,
    hex_color,
)


def create_workspace_box(lines: int = 4, accent_color=None) -> Table:
    """Create a styled workspace box for student work with dotted writing lines."""
    if accent_color is None:
        accent_color = COLORS["ink_300"]

    # Create rows for each line - each row is a writing area
    rows = [[""] for _ in range(lines)]
    row_height = 0.28 * inch

    workspace = Table(
        rows,
        colWidths=[7.5 * inch],
        rowHeights=[row_height] * lines
    )

    # Build style with dotted lines between rows
    style_commands = [
        ("BOX", (0, 0), (-1, -1), 1.5, COLORS["ink_200"]),
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["white"]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent_color),
    ]

    # Add dotted lines between rows (writing guides)
    for i in range(lines - 1):
        style_commands.append(
            ("LINEBELOW", (0, i), (-1, i), 0.5, COLORS["ink_200"], 1, None, None, 2, 2)
        )

    workspace.setStyle(TableStyle(style_commands))
    return workspace


def create_quick_reference_box(meta: dict, data: dict) -> Table:
    """Create a compact quick reference box with key lesson info.

    ┌─────────────────────────────────────────────────┐
    │ QUICK REFERENCE                                 │
    │ Duration: 20 min │ Format: Small Group          │
    │ Approach: 5E Lesson │ Goal: Introduce           │
    │ Key Standard: 6.RP.A.3a                         │
    └─────────────────────────────────────────────────┘
    """
    # Gather info
    duration = meta.get("duration_minutes", "")
    approach_data = meta.get("pedagogical_approach", "")
    if isinstance(approach_data, dict):
        approach = approach_data.get("name", approach_data.get("id", ""))
    else:
        approach = approach_data
    grouping = meta.get("grouping", "")
    standards = meta.get("standards_addressed", [])
    key_standard = standards[0] if standards else ""

    # Build info items
    info_items = []
    if duration:
        info_items.append(f"<b>Duration:</b> {duration} min")
    if grouping:
        info_items.append(f"<b>Format:</b> {grouping}")
    if approach:
        info_items.append(f"<b>Approach:</b> {approach}")
    if key_standard:
        info_items.append(f"<b>Standard:</b> {key_standard}")

    # Create two-column layout
    row1_items = info_items[:2]
    row2_items = info_items[2:4]

    row1_text = "  │  ".join(row1_items) if row1_items else ""
    row2_text = "  │  ".join(row2_items) if row2_items else ""

    rows = [[Paragraph("<b>QUICK REFERENCE</b>", ParagraphStyle(
        name="qrheader", fontSize=9, textColor=COLORS["navy_700"]
    ))]]

    if row1_text:
        rows.append([Paragraph(row1_text, ParagraphStyle(
            name="qrrow1", fontSize=9, textColor=COLORS["ink_600"]
        ))])
    if row2_text:
        rows.append([Paragraph(row2_text, ParagraphStyle(
            name="qrrow2", fontSize=9, textColor=COLORS["ink_600"]
        ))])

    box = Table(rows, colWidths=[7.5 * inch])
    box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, COLORS["navy_700"]),
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["navy_100"]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, COLORS["navy_500"]),
    ]))
    return box


def create_differentiation_at_a_glance(diff: dict) -> Table:
    """Create a compact differentiation summary view."""
    level_info = [
        ("below_level", "Below", COLORS["below"], COLORS["below_light"]),
        ("approaching_level", "Approaching", COLORS["approaching"], COLORS["approaching_light"]),
        ("at_level", "At Level", COLORS["at"], COLORS["at_light"]),
        ("above_level", "Above", COLORS["above"], COLORS["above_light"]),
    ]

    # Header row
    headers = [Paragraph(f"<b>{name}</b>", ParagraphStyle(
        name=f"dh_{key}", fontSize=8, textColor=color, alignment=TA_CENTER
    )) for key, name, color, _ in level_info]

    # Focus row - extract key focus for each level
    focus_cells = []
    for key, _, color, bg_color in level_info:
        level_data = diff.get(key, {})
        focus = level_data.get("focus", "")
        # Truncate if too long
        if len(focus) > 60:
            focus = focus[:57] + "..."
        focus_cells.append(Paragraph(focus, ParagraphStyle(
            name=f"df_{key}", fontSize=8, textColor=COLORS["ink_700"], leading=10
        )))

    table = Table([headers, focus_cells], colWidths=[1.875 * inch] * 4)
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), COLORS["below_light"]),
        ("BACKGROUND", (1, 0), (1, -1), COLORS["approaching_light"]),
        ("BACKGROUND", (2, 0), (2, -1), COLORS["at_light"]),
        ("BACKGROUND", (3, 0), (3, -1), COLORS["above_light"]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLORS["ink_200"]),
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, COLORS["ink_200"]),
        ("LINEBEFORE", (2, 0), (2, -1), 0.5, COLORS["ink_200"]),
        ("LINEBEFORE", (3, 0), (3, -1), 0.5, COLORS["ink_200"]),
    ]))
    return table


def render_graphic_organizer(go_data: dict, accent_color, styles) -> list:
    """Render a graphic organizer based on type.

    Returns a list of flowable elements to add to the document.
    """
    elements = []
    go_type = go_data.get("type", "").lower()
    title = go_data.get("title", "Graphic Organizer")

    # Header
    elements.append(Paragraph(f"<b>■ {title.upper()}</b>", ParagraphStyle(
        name="goheader", fontSize=10, textColor=accent_color, spaceAfter=6
    )))

    if go_type in ("ratio_table", "table"):
        # Ratio table / generic table
        headers = go_data.get("headers", go_data.get("columns", []))
        rows_data = go_data.get("rows", [])

        if headers:
            # Header row
            header_cells = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
                name="goth", fontSize=9, textColor=COLORS["ink_700"], alignment=TA_CENTER
            )) for h in headers]

            all_rows = [header_cells]

            # Data rows (or empty rows for student fill-in)
            num_rows = len(rows_data) if rows_data else go_data.get("num_rows", 4)
            for i in range(num_rows):
                if rows_data and i < len(rows_data):
                    row = rows_data[i]
                    cells = [Paragraph(str(cell), styles["SmallText"]) for cell in row]
                else:
                    cells = ["" for _ in headers]
                all_rows.append(cells)

            col_width = 7.5 * inch / len(headers)
            table = Table(all_rows, colWidths=[col_width] * len(headers))
            table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLORS["ink_200"]),
                ("BACKGROUND", (0, 0), (-1, 0), accent_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLORS["white"]),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)

    elif go_type in ("vocabulary_four_square", "four_square"):
        # Four-square vocabulary organizer
        word = go_data.get("word", go_data.get("term", ""))
        quadrants = go_data.get("quadrants", ["Definition", "Example", "Non-Example", "Picture/Drawing"])

        # Center word
        center_text = Paragraph(f"<b>{word}</b>", ParagraphStyle(
            name="gocenter", fontSize=12, textColor=accent_color, alignment=TA_CENTER
        ))

        # Four quadrants - ensure exactly 4 cells
        quad_cells = [
            Paragraph(f"<b>{q}</b>", ParagraphStyle(
                name="goquad", fontSize=9, textColor=COLORS["ink_600"]
            )) for q in quadrants[:4]
        ]
        while len(quad_cells) < 4:
            quad_cells.append("")

        four_square = Table([
            [quad_cells[0], quad_cells[1]],
            [center_text, center_text],
            [quad_cells[2], quad_cells[3]],
        ], colWidths=[3.75 * inch, 3.75 * inch], rowHeights=[0.8 * inch, 0.4 * inch, 0.8 * inch])
        four_square.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.5, accent_color),
            ("INNERGRID", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
            ("SPAN", (0, 1), (1, 1)),
            ("BACKGROUND", (0, 1), (1, 1), accent_color),
            ("TEXTCOLOR", (0, 1), (1, 1), COLORS["white"]),
            ("ALIGN", (0, 1), (1, 1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(four_square)

    elif go_type in ("t_chart", "comparison"):
        # T-Chart for comparisons
        left_header = go_data.get("left_header", "Side A")
        right_header = go_data.get("right_header", "Side B")
        num_rows = go_data.get("num_rows", 4)

        header_row = [
            Paragraph(f"<b>{left_header}</b>", ParagraphStyle(
                name="gothl", fontSize=10, textColor=COLORS["white"], alignment=TA_CENTER
            )),
            Paragraph(f"<b>{right_header}</b>", ParagraphStyle(
                name="gothr", fontSize=10, textColor=COLORS["white"], alignment=TA_CENTER
            )),
        ]

        rows = [header_row]
        for _ in range(num_rows):
            rows.append(["", ""])

        t_chart = Table(rows, colWidths=[3.75 * inch, 3.75 * inch], rowHeights=[0.35 * inch] + [0.5 * inch] * num_rows)
        t_chart.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.5, accent_color),
            ("LINEBEFORE", (1, 0), (1, -1), 1.5, accent_color),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, accent_color),
            ("BACKGROUND", (0, 0), (-1, 0), accent_color),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_chart)

    else:
        # Generic fallback - simple labeled box
        description = go_data.get("description", go_data.get("instructions", ""))
        if description:
            elements.append(Paragraph(description, styles["SmallText"]))
            elements.append(Spacer(1, 6))

        # Add an empty workspace
        elements.append(create_workspace_box(4, accent_color))

    elements.append(Spacer(1, 12))
    return elements


# ============================================================================
# TEACHER GUIDE PDF
# ============================================================================
def create_teacher_guide(data: dict[str, Any], output_path: str, include_udl_docs: bool = False) -> str:
    """Generate a polished teacher guide PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.5 * inch,
    )

    styles, accent, accent_light = get_styles()
    elements = []
    meta = data.get("metadata", {})

    # ===== HEADER =====
    # Title with navy accent square
    title_text = meta.get("title", "Lesson Plan")
    elements.append(Paragraph(f"<font color='#{COLORS['navy_700'].hexval()[2:]}'>&#9632;</font>  {title_text}", styles["Title"]))

    # Metadata line
    meta_parts = []
    if meta.get("grade"):
        meta_parts.append(f"Grade {meta['grade']}")
    if meta.get("subject"):
        meta_parts.append(meta["subject"])
    if meta.get("topic"):
        meta_parts.append(meta["topic"])
    if meta.get("duration_minutes"):
        meta_parts.append(f"{meta['duration_minutes']} min")

    elements.append(Paragraph(" \u2022 ".join(meta_parts), styles["Subtitle"]))
    elements.append(Spacer(1, 8))

    # Standards badges
    standards = meta.get("standards_addressed", [])
    if standards:
        standards_text = "  ".join([f"<font color='#{COLORS['gold_600'].hexval()[2:]}' size='9'><b>[{s}]</b></font>" for s in standards])
        elements.append(Paragraph(standards_text, styles["BodyText"]))

    elements.append(Spacer(1, 8))

    # ===== QUICK REFERENCE BOX =====
    elements.append(create_quick_reference_box(meta, data))
    elements.append(Spacer(1, 12))

    # ===== MATERIALS (moved up for teacher prep) =====
    materials = data.get("materials_list", [])
    if materials:
        elements.append(create_section_header("MATERIALS NEEDED", COLORS["gold_600"]))
        elements.append(Spacer(1, 6))
        add_bullet_list(elements, materials, styles["BodyText"], COLORS["gold_600"])
        elements.append(Spacer(1, 12))

    # ===== LEARNING OBJECTIVES =====
    objectives = data.get("learning_objectives", [])
    if objectives:
        elements.append(create_section_header("LEARNING OBJECTIVES", COLORS["gold_600"]))
        elements.append(Spacer(1, 8))

        for obj in objectives:
            obj_box = Table([[
                Paragraph(f"<b>Objective:</b> {obj.get('objective', '')}", styles["BodyText"]),
            ], [
                Paragraph(f"<b>Success Criteria:</b> {obj.get('success_criteria', '')}", styles["SmallText"]),
            ]], colWidths=[7.5 * inch])
            obj_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["gold_100"]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("LINEBEFORE", (0, 0), (0, -1), 3, COLORS["gold_600"]),
            ]))
            elements.append(obj_box)
        elements.append(Spacer(1, 12))

    # ===== DIFFERENTIATION AT-A-GLANCE =====
    diff = data.get("differentiation_overview", {})
    if diff:
        elements.append(Paragraph("<b>DIFFERENTIATION AT-A-GLANCE</b>", ParagraphStyle(
            name="diffglance", fontSize=10, textColor=COLORS["ink_700"], spaceAfter=6
        )))
        elements.append(create_differentiation_at_a_glance(diff))
        elements.append(Spacer(1, 12))

    # ===== SESSION STRUCTURE =====
    structure = data.get("session_structure", {})
    if structure:
        elements.append(create_section_header("SESSION STRUCTURE", COLORS["navy_700"]))
        elements.append(Spacer(1, 8))

        # Check for pedagogical approach phases (new format) first
        phases = structure.get("phases", [])
        if phases:
            # Use the phases array from pedagogical approaches
            phase_color_cycle = [COLORS["gold_600"], COLORS["navy_600"], COLORS["at"], COLORS["above"], COLORS["emerging"]]
            for idx, phase in enumerate(phases):
                phase_name = phase.get("name", phase.get("phase", f"Phase {idx + 1}"))
                duration = phase.get("duration_minutes", phase.get("duration", ""))
                color = phase_color_cycle[idx % len(phase_color_cycle)]

                # Phase header row
                phase_header = Table([[
                    Paragraph(f"<font color='#{color.hexval()[2:]}'>■</font> <b>{phase_name.upper()}</b>",
                             ParagraphStyle(name="ph", fontSize=10, textColor=color)),
                    Paragraph(f"<b>{duration} min</b>" if duration else "",
                             ParagraphStyle(name="dur", fontSize=10, textColor=COLORS["ink_500"], alignment=2)),
                ]], colWidths=[6 * inch, 1.5 * inch])
                phase_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]))
                elements.append(phase_header)

                # Phase content - handle various field names
                description = phase.get("description", phase.get("activities", ""))
                if description:
                    elements.append(Paragraph(description, styles["BodyText"]))

                if phase.get("teacher_actions"):
                    elements.append(Paragraph(f"<b>Teacher:</b> {phase['teacher_actions']}", styles["SmallText"]))
                if phase.get("student_actions"):
                    elements.append(Paragraph(f"<b>Students:</b> {phase['student_actions']}", styles["SmallText"]))
                if phase.get("key_points"):
                    elements.append(Paragraph("<b>Key Points:</b>", styles["SmallText"]))
                    add_bullet_list(elements, phase["key_points"], styles["SmallText"], color)
                if phase.get("key_questions"):
                    elements.append(Paragraph("<b>Key Questions:</b>", styles["SmallText"]))
                    add_bullet_list(elements, phase["key_questions"], styles["SmallText"], color)

                elements.append(Spacer(1, 10))
        else:
            # Legacy fallback: hook/instruction/practice/closure
            section_labels = {"hook": "HOOK", "instruction": "INSTRUCTION", "practice": "PRACTICE", "closure": "CLOSURE"}
            section_colors = {
                "hook": COLORS["gold_600"],
                "instruction": COLORS["navy_600"],
                "practice": COLORS["at"],
                "closure": COLORS["above"],
            }

            for section_name in ["hook", "instruction", "practice", "closure"]:
                section = structure.get(section_name, {})
                if section:
                    duration = section.get("duration_minutes", "")
                    label = section_labels.get(section_name, section_name.upper())
                    color = section_colors.get(section_name, COLORS["ink_600"])

                    # Section header row
                    section_header = Table([[
                        Paragraph(f"<font color='#{color.hexval()[2:]}'>■</font> <b>{label}</b>",
                                 ParagraphStyle(name="sh", fontSize=10, textColor=color)),
                        Paragraph(f"<b>{duration} min</b>",
                                 ParagraphStyle(name="dur", fontSize=10, textColor=COLORS["ink_500"], alignment=2)),
                    ]], colWidths=[6 * inch, 1.5 * inch])
                    section_header.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(section_header)

                    # Section content
                    elements.append(Paragraph(section.get("description", ""), styles["BodyText"]))

                    if section.get("teacher_actions"):
                        elements.append(Paragraph(f"<b>Teacher:</b> {section['teacher_actions']}", styles["SmallText"]))
                    if section.get("student_actions"):
                        elements.append(Paragraph(f"<b>Students:</b> {section['student_actions']}", styles["SmallText"]))
                    if section.get("key_points"):
                        elements.append(Paragraph("<b>Key Points:</b>", styles["SmallText"]))
                        add_bullet_list(elements, section["key_points"], styles["SmallText"], color)

                    elements.append(Spacer(1, 10))

    # ===== COMMON MISCONCEPTIONS (moved up - teachers need this before teaching) =====
    misconceptions = data.get("common_misconceptions", [])
    if misconceptions:
        elements.append(create_section_header("COMMON MISCONCEPTIONS", COLORS["below"]))
        elements.append(Spacer(1, 6))

        for m in misconceptions:
            misc_box = Table([[
                Paragraph(f"<b>■ Misconception:</b> {m.get('misconception', '')}", styles["BodyText"]),
            ], [
                Paragraph(f"<b>→ Address by:</b> {m.get('how_to_address', '')}", styles["SmallText"]),
            ]], colWidths=[7.5 * inch])
            misc_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["below_light"]),
                ("BACKGROUND", (0, 1), (-1, 1), COLORS["at_light"]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
            ]))
            elements.append(misc_box)
            elements.append(Spacer(1, 6))
        elements.append(Spacer(1, 6))

    # ===== DETAILED DIFFERENTIATION GUIDE (Page 2) =====
    # Note: diff was already loaded earlier for At-A-Glance section
    if diff:
        elements.append(PageBreak())
        elements.append(create_section_header("DIFFERENTIATION GUIDE", COLORS["navy_700"]))
        elements.append(Spacer(1, 8))

        level_info = [
            ("below_level", "Below Level", COLORS["below"], COLORS["below_light"]),
            ("approaching_level", "Approaching Level", COLORS["approaching"], COLORS["approaching_light"]),
            ("at_level", "At Level", COLORS["at"], COLORS["at_light"]),
            ("above_level", "Above Level", COLORS["above"], COLORS["above_light"]),
        ]

        for level_key, level_name, color, bg_color in level_info:
            level_data = diff.get(level_key, {})
            if level_data:
                # Level header - uses border for print-friendliness, text label is primary
                level_header = Table([[
                    Paragraph(f"<b>■ {level_name}</b>", ParagraphStyle(name="lh", fontSize=11, textColor=color)),
                ]], colWidths=[7.5 * inch])
                level_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLORS["white"]),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, color),
                    ("BOX", (0, 0), (-1, -1), 1, color),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ]))
                elements.append(level_header)

                elements.append(Paragraph(f"<b>Focus:</b> {level_data.get('focus', '')}", styles["BodyText"]))

                scaffolds = level_data.get("key_scaffolds", [])
                if scaffolds:
                    elements.append(Paragraph("<b>Key Scaffolds:</b>", styles["SmallText"]))
                    add_bullet_list(elements, scaffolds, styles["SmallText"], color)

                elements.append(Paragraph(f"<b>Monitor for:</b> {level_data.get('monitor_for', '')}", styles["SmallText"]))
                elements.append(Spacer(1, 10))

    # ===== UDL ALIGNMENT =====
    udl = data.get("udl_alignment", {})
    if udl and include_udl_docs:
        elements.append(create_section_header("UDL ALIGNMENT", COLORS["udl_engagement"]))
        elements.append(Spacer(1, 8))

        # Summary
        summary = udl.get("summary", "")
        if summary:
            summary_box = Table([[
                Paragraph(summary, styles["BodyText"])
            ]], colWidths=[7.5 * inch])
            summary_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]))
            elements.append(summary_box)
            elements.append(Spacer(1, 10))

        # UDL Principles
        udl_principles = [
            ("engagement", "Engagement", "The Why of Learning", COLORS["udl_engagement"], COLORS["udl_engagement_light"]),
            ("representation", "Representation", "The What of Learning", COLORS["udl_representation"], COLORS["udl_representation_light"]),
            ("action_expression", "Action & Expression", "The How of Learning", COLORS["udl_action"], COLORS["udl_action_light"]),
        ]

        for key, name, subtitle, color, bg_color in udl_principles:
            principle_data = udl.get(key, {})
            if principle_data:
                checkpoints = principle_data.get("checkpoints_addressed", [])
                how = principle_data.get("how_addressed", "")

                # Principle header
                principle_header = Table([[
                    Paragraph(f"<b>{name}</b> <font size='8' color='#{COLORS['ink_500'].hexval()[2:]}'>{subtitle}</font>",
                             ParagraphStyle(name="udlh", fontSize=10, textColor=color)),
                    Paragraph(" ".join([f"<font size='8' color='#{color.hexval()[2:]}'>[{cp}]</font>" for cp in checkpoints]),
                             ParagraphStyle(name="udlcp", fontSize=8, textColor=color, alignment=2)),
                ]], colWidths=[4.5 * inch, 3 * inch])
                principle_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                elements.append(principle_header)

                if how:
                    elements.append(Paragraph(how, styles["SmallText"]))
                elements.append(Spacer(1, 8))

        elements.append(Spacer(1, 4))

    doc.build(elements)
    return output_path


# ============================================================================
# STUDENT HANDOUT PDF
# ============================================================================
def create_student_handout(data: dict[str, Any], level: str, output_path: str) -> str:
    """Generate a polished, level-specific student handout PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles, accent, accent_light = get_styles(level)
    elements = []
    header = data.get("header", {})

    # ===== HEADER WITH NAME LINE =====
    title_text = header.get("title", "Lesson")

    # Create header table with title and name field
    header_table = Table([
        [
            Paragraph(f"<b>{title_text}</b>", styles["StudentTitle"]),
            Paragraph("Name: ____________________", ParagraphStyle(
                name="namefield", fontSize=10, textColor=COLORS["ink_600"], alignment=2
            ))
        ],
        [
            Paragraph("Date: __________", ParagraphStyle(
                name="datefield", fontSize=9, textColor=COLORS["ink_400"]
            )),
            ""
        ]
    ], colWidths=[5.5 * inch, 2 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)

    # Colored accent bar
    accent_bar = Table([[""]],  colWidths=[7.5 * inch], rowHeights=[4])
    accent_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), accent),
    ]))
    elements.append(accent_bar)
    elements.append(Spacer(1, 12))

    # ===== I CAN STATEMENT (Goal Box) =====
    i_can = header.get("i_can_statement", header.get("student_objective", ""))
    if i_can:
        goal_box = Table([[
            Paragraph(f"<font color='#{accent.hexval()[2:]}'>&#9632;</font> <b>TODAY'S GOAL:</b>  {i_can}", ParagraphStyle(
                name="goaltext", fontSize=11, textColor=accent, leading=14
            ))
        ]], colWidths=[7.5 * inch])
        goal_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent_light),
            ("BOX", (0, 0), (-1, -1), 2, accent),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(goal_box)
        elements.append(Spacer(1, 12))

    # ===== WORD BANK (moved up - students need while working) =====
    word_bank = data.get("word_bank", [])
    if word_bank:
        words_text = "   •   ".join(word_bank)
        word_box = Table([[
            Paragraph(f"<b>■ WORD BANK:</b>  {words_text}", ParagraphStyle(
                name="wordbank", fontSize=10, textColor=accent
            ))
        ]], colWidths=[7.5 * inch])
        word_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.5, accent),
            ("BACKGROUND", (0, 0), (-1, -1), accent_light),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(word_box)
        elements.append(Spacer(1, 10))

    # ===== SENTENCE FRAMES (moved up - students need while working) =====
    frames = data.get("sentence_frames", [])
    if frames:
        frames_content = []
        frames_content.append([Paragraph("<b>■ SENTENCE FRAMES</b>", ParagraphStyle(
            name="sfheader", fontSize=10, textColor=COLORS["ink_700"]
        ))])
        for frame in frames:
            frames_content.append([Paragraph(f"• {frame}", ParagraphStyle(
                name="sfitem", fontSize=9, textColor=COLORS["ink_600"], leftIndent=8
            ))])

        frames_table = Table(frames_content, colWidths=[7.5 * inch])
        frames_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
            ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(frames_table)
        elements.append(Spacer(1, 12))

    # ===== VOCABULARY =====
    vocab = data.get("vocabulary", [])
    if vocab:
        elements.append(Paragraph(f"<font color='#{COLORS['navy_700'].hexval()[2:]}'>&#9632;</font> <b>VOCABULARY</b>", ParagraphStyle(
            name="vocabheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=8
        )))

        vocab_rows = []
        for v in vocab:
            term = v.get("term", "")
            definition = v.get("definition", "")
            example = v.get("example", "")

            term_text = f"<b>{term}</b>"
            def_text = definition
            if example:
                def_text += f"<br/><font size='8' color='#{COLORS['ink_500'].hexval()[2:]}'><i>Example: {example}</i></font>"

            vocab_rows.append([
                Paragraph(term_text, ParagraphStyle(name="vt", fontSize=10, textColor=accent)),
                Paragraph(def_text, styles["SmallText"]),
            ])

        vocab_table = Table(vocab_rows, colWidths=[1.8 * inch, 5.7 * inch])
        vocab_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (0, -1), 8),
            ("BACKGROUND", (0, 0), (0, -1), accent_light),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, COLORS["ink_200"]),
        ]))
        elements.append(vocab_table)
        elements.append(Spacer(1, 14))

    # ===== GRAPHIC ORGANIZER (if present) =====
    graphic_organizer = data.get("graphic_organizer", {})
    if graphic_organizer:
        go_elements = render_graphic_organizer(graphic_organizer, accent, styles)
        elements.extend(go_elements)

    # ===== WORKED EXAMPLE =====
    worked = data.get("worked_example", {})
    if worked:
        elements.append(Paragraph(f"<font color='#{COLORS['navy_700'].hexval()[2:]}'>&#9632;</font> <b>EXAMPLE</b>", ParagraphStyle(
            name="exheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=6
        )))

        # Problem box
        problem_box = Table([[
            Paragraph(f"<b>Problem:</b> {worked.get('problem', '')}", styles["BodyText"])
        ]], colWidths=[7.5 * inch])
        problem_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
            ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(problem_box)
        elements.append(Spacer(1, 6))

        # Steps
        steps = worked.get("steps", [])
        if steps:
            for step in steps:
                step_num = step.get("step_number", "")
                action = step.get("action", "")
                result = step.get("result", "")

                step_row = Table([[
                    Paragraph(f"<b>{step_num}</b>", ParagraphStyle(
                        name="stepnum", fontSize=12, textColor=accent, alignment=TA_CENTER
                    )),
                    Paragraph(f"{action}  \u2192  <b>{result}</b>", styles["BodyText"]),
                ]], colWidths=[0.4 * inch, 7.1 * inch])
                step_row.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (0, -1), accent_light),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(step_row)
                elements.append(Spacer(1, 2))

        # Solution
        solution = worked.get("solution", worked.get("solution_summary", ""))
        if solution:
            elements.append(Spacer(1, 4))
            answer_box = Table([[
                Paragraph(f"<font color='#{COLORS['at'].hexval()[2:]}'>\u2713</font> <b>Answer:</b> {solution}", ParagraphStyle(
                    name="answer", fontSize=10, textColor=COLORS["at"]
                ))
            ]], colWidths=[7.5 * inch])
            answer_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["at_light"]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            elements.append(answer_box)

        elements.append(Spacer(1, 14))

    # ===== GUIDED PRACTICE =====
    guided = data.get("guided_practice", [])
    if guided:
        elements.append(Paragraph(f"<font color='#{COLORS['navy_700'].hexval()[2:]}'>&#9632;</font> <b>GUIDED PRACTICE</b>", ParagraphStyle(
            name="gpheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=8
        )))

        for i, prob in enumerate(guided, 1):
            problem = prob.get("problem", "")
            hint = prob.get("scaffold", prob.get("hint", ""))

            elements.append(Paragraph(f"<b>{i}.</b>  {problem}", styles["BodyText"]))
            if hint:
                hint_box = Table([[
                    Paragraph(f"<font color='#{COLORS['gold_600'].hexval()[2:]}'>&#9632;</font> <i>Hint: {hint}</i>", styles["HintText"])
                ]], colWidths=[7.5 * inch])
                hint_box.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLORS["gold_100"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]))
                elements.append(hint_box)

            elements.append(Spacer(1, 4))
            elements.append(create_workspace_box(4, accent))
            elements.append(Spacer(1, 10))

    # ===== INDEPENDENT PRACTICE =====
    independent = data.get("independent_practice", data.get("practice_problems", []))
    if independent:
        elements.append(Paragraph(f"<font color='#{accent.hexval()[2:]}'>■</font> <b>YOUR TURN</b>", ParagraphStyle(
            name="ipheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=8
        )))

        for i, prob in enumerate(independent, 1):
            problem = prob.get("problem", "")
            elements.append(Paragraph(f"<b>{i}.</b>  {problem}", styles["BodyText"]))
            elements.append(Spacer(1, 4))
            elements.append(create_workspace_box(4, accent))
            elements.append(Spacer(1, 10))

    # ===== APPLICATION PROBLEM =====
    application = data.get("application_problem", {})
    if application:
        elements.append(Paragraph(f"<font color='#{COLORS['gold_600'].hexval()[2:]}'>■</font> <b>APPLY IT</b>", ParagraphStyle(
            name="apheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=6
        )))

        context = application.get("context", "")
        question = application.get("question", "")

        if context:
            elements.append(Paragraph(context, styles["BodyText"]))
        elements.append(Paragraph(f"<b>Question:</b> {question}", styles["BodyText"]))
        elements.append(Spacer(1, 6))
        elements.append(create_workspace_box(6, accent))
        elements.append(Spacer(1, 12))

    # ===== EXTENSION CHALLENGE =====
    extension = data.get("extension_challenge", {})
    if extension:
        ext_header = Table([[
            Paragraph(f"<font color='#{COLORS['above'].hexval()[2:]}'>■</font> <b>EXTENSION CHALLENGE: {extension.get('title', '')}</b>", ParagraphStyle(
                name="extheader", fontSize=11, textColor=COLORS["above"]
            ))
        ]], colWidths=[7.5 * inch])
        ext_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLORS["above_light"]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBEFORE", (0, 0), (0, -1), 4, COLORS["above"]),
        ]))
        elements.append(ext_header)
        elements.append(Spacer(1, 6))

        elements.append(Paragraph(extension.get("description", ""), styles["BodyText"]))

        guiding = extension.get("guiding_questions", [])
        if guiding:
            elements.append(Paragraph("<b>Guiding Questions:</b>", styles["SmallText"]))
            add_bullet_list(elements, guiding, styles["SmallText"], COLORS["above"])

        elements.append(Spacer(1, 6))
        elements.append(create_workspace_box(6, COLORS["above"]))
        elements.append(Spacer(1, 12))

    # ===== REFLECTION =====
    reflection = data.get("reflection", {})
    if reflection:
        elements.append(Paragraph(f"<font color='#{COLORS['navy_700'].hexval()[2:]}'>&#9632;</font> <b>REFLECTION</b>", ParagraphStyle(
            name="refheader", fontSize=11, textColor=COLORS["ink_800"], spaceAfter=6
        )))

        prompt = reflection.get("prompt", "")
        starter = reflection.get("sentence_starter", "")

        elements.append(Paragraph(prompt, styles["BodyText"]))

        if starter:
            elements.append(Paragraph(f"<i>{starter}</i> _______________________________________________", styles["BodyText"]))

        # Writing lines
        for _ in range(2):
            elements.append(Paragraph("_" * 85, ParagraphStyle(
                name="writeline", fontSize=10, textColor=COLORS["ink_300"], spaceBefore=8
            )))

    doc.build(elements)
    return output_path


# ============================================================================
# MAIN GENERATOR
# ============================================================================
def generate_all_pdfs(
    curriculum: dict[str, Any],
    session_id: str,
    output_dir: str,
    include_udl_docs: bool = False
) -> list[dict[str, str]]:
    """Generate all PDFs from curriculum data using parallel execution."""
    output_path = Path(output_dir)
    files = []

    # Prepare all PDF tasks
    teacher_data = curriculum.get("teacher_guide", {})
    teacher_filename = f"{session_id}_teacher_guide.pdf"
    teacher_path = str(output_path / teacher_filename)

    student_materials = curriculum.get("student_materials", {})
    level_names = {
        "below_level": "Below Level",
        "approaching_level": "Approaching Level",
        "at_level": "At Level",
        "above_level": "Above Level",
    }

    # Generate all PDFs in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}

        # Submit teacher guide task
        future = executor.submit(
            create_teacher_guide, teacher_data, teacher_path, include_udl_docs
        )
        futures[future] = {
            "name": "Teacher Guide",
            "filename": teacher_filename,
            "download_url": f"/download/{teacher_filename}",
            "order": 0
        }

        # Submit student handout tasks
        for i, (level_key, level_name) in enumerate(level_names.items(), 1):
            level_data = student_materials.get(level_key, {})
            if level_data:
                filename = f"{session_id}_student_{level_key}.pdf"
                filepath = str(output_path / filename)
                future = executor.submit(
                    create_student_handout, level_data, level_key, filepath
                )
                futures[future] = {
                    "name": f"Student Handout - {level_name}",
                    "filename": filename,
                    "download_url": f"/download/{filename}",
                    "order": i
                }

        # Collect results as they complete
        results = []
        for future in as_completed(futures):
            file_info = futures[future]
            future.result()  # Raise any exceptions
            results.append(file_info)

        # Sort by original order
        results.sort(key=lambda x: x["order"])
        files = [{k: v for k, v in r.items() if k != "order"} for r in results]

    return files
