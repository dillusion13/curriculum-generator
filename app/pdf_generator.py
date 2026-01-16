"""
PDF Generator - Create polished, print-ready PDFs from curriculum JSON.
Matches the "Scholarly Modern" frontend design aesthetic.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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


# ============================================================================
# COLOR PALETTE - Matches "Scholarly Modern" frontend design
# ============================================================================
COLORS = {
    # Core ink palette (warm grays)
    "ink_900": colors.HexColor("#1a1a2e"),
    "ink_800": colors.HexColor("#2d2d44"),
    "ink_700": colors.HexColor("#404058"),
    "ink_600": colors.HexColor("#5c5c73"),
    "ink_500": colors.HexColor("#7a7a8c"),
    "ink_400": colors.HexColor("#9e9eab"),
    "ink_300": colors.HexColor("#c4c4cd"),
    "ink_200": colors.HexColor("#e0e0e6"),
    "ink_100": colors.HexColor("#f0f0f3"),
    "ink_50": colors.HexColor("#f8f8fa"),

    # Paper tones
    "paper": colors.HexColor("#fdfcfa"),
    "paper_warm": colors.HexColor("#faf8f5"),

    # Navy - Primary accent
    "navy_700": colors.HexColor("#1e3a5f"),
    "navy_600": colors.HexColor("#2c4a6e"),
    "navy_500": colors.HexColor("#3d5a80"),
    "navy_100": colors.HexColor("#e8eef4"),

    # Gold - Secondary accent
    "gold_600": colors.HexColor("#b8860b"),
    "gold_500": colors.HexColor("#d4a574"),
    "gold_400": colors.HexColor("#e4bb84"),
    "gold_300": colors.HexColor("#f0d4a8"),
    "gold_100": colors.HexColor("#fdf6eb"),

    # Readiness levels
    "below": colors.HexColor("#dc2626"),
    "below_muted": colors.HexColor("#991b1b"),
    "below_light": colors.HexColor("#fef2f2"),
    "below_border": colors.HexColor("#fecaca"),

    "approaching": colors.HexColor("#ea580c"),
    "approaching_muted": colors.HexColor("#c2410c"),
    "approaching_light": colors.HexColor("#fff7ed"),
    "approaching_border": colors.HexColor("#fed7aa"),

    "at": colors.HexColor("#16a34a"),
    "at_muted": colors.HexColor("#15803d"),
    "at_light": colors.HexColor("#f0fdf4"),
    "at_border": colors.HexColor("#bbf7d0"),

    "above": colors.HexColor("#7c3aed"),
    "above_muted": colors.HexColor("#6d28d9"),
    "above_light": colors.HexColor("#f5f3ff"),
    "above_border": colors.HexColor("#ddd6fe"),

    # EL levels - Teal spectrum
    "emerging": colors.HexColor("#0d9488"),
    "emerging_light": colors.HexColor("#f0fdfa"),
    "expanding": colors.HexColor("#0891b2"),
    "expanding_light": colors.HexColor("#ecfeff"),
    "bridging": colors.HexColor("#0369a1"),
    "bridging_light": colors.HexColor("#f0f9ff"),

    # UDL colors - Purple/Teal/Blue for the 3 principles
    "udl_engagement": colors.HexColor("#7c3aed"),
    "udl_engagement_light": colors.HexColor("#f5f3ff"),
    "udl_representation": colors.HexColor("#0891b2"),
    "udl_representation_light": colors.HexColor("#ecfeff"),
    "udl_action": colors.HexColor("#059669"),
    "udl_action_light": colors.HexColor("#d1fae5"),

    # Utility
    "white": colors.white,
    "success": colors.HexColor("#059669"),
    "success_light": colors.HexColor("#d1fae5"),
    "error": colors.HexColor("#dc2626"),
    "error_light": colors.HexColor("#fee2e2"),
}

# Level color mapping
LEVEL_COLORS = {
    "below_level": ("below", "below_light"),
    "approaching_level": ("approaching", "approaching_light"),
    "at_level": ("at", "at_light"),
    "above_level": ("above", "above_light"),
}


# ============================================================================
# STYLES
# ============================================================================
@lru_cache(maxsize=8)
def get_styles(level_key: str = None):
    """Create custom paragraph styles with optional level-specific colors."""
    styles = getSampleStyleSheet()

    # Determine accent color based on level
    if level_key and level_key in LEVEL_COLORS:
        accent = COLORS[LEVEL_COLORS[level_key][0]]
        accent_light = COLORS[LEVEL_COLORS[level_key][1]]
    else:
        accent = COLORS["navy_700"]
        accent_light = COLORS["navy_100"]

    # Document Title
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 22
    styles["Title"].textColor = COLORS["ink_900"]
    styles["Title"].spaceAfter = 4
    styles["Title"].leading = 26

    # Section Headers (H1)
    styles["Heading1"].fontName = "Helvetica-Bold"
    styles["Heading1"].fontSize = 13
    styles["Heading1"].textColor = COLORS["ink_800"]
    styles["Heading1"].spaceBefore = 16
    styles["Heading1"].spaceAfter = 8
    styles["Heading1"].leading = 16

    # Subsection Headers (H2)
    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].fontSize = 11
    styles["Heading2"].textColor = accent
    styles["Heading2"].spaceBefore = 12
    styles["Heading2"].spaceAfter = 6
    styles["Heading2"].leading = 14

    # Body Text
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].textColor = COLORS["ink_700"]
    styles["BodyText"].spaceAfter = 4
    styles["BodyText"].leading = 14

    # Add custom styles
    styles.add(ParagraphStyle(
        name="Subtitle",
        fontName="Helvetica",
        fontSize=10,
        textColor=COLORS["ink_500"],
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="SmallText",
        fontName="Helvetica",
        fontSize=9,
        textColor=COLORS["ink_600"],
        leading=12,
    ))

    styles.add(ParagraphStyle(
        name="SectionLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=COLORS["ink_600"],
        spaceBefore=0,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="StudentTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=COLORS["ink_900"],
        spaceAfter=2,
        leading=22,
    ))

    styles.add(ParagraphStyle(
        name="ICanStatement",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=accent,
        spaceBefore=4,
        spaceAfter=16,
        leading=14,
        backColor=accent_light,
        borderPadding=(8, 8, 8, 8),
    ))

    styles.add(ParagraphStyle(
        name="GoalBox",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=accent,
        alignment=TA_LEFT,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name="StepNumber",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=accent,
    ))

    styles.add(ParagraphStyle(
        name="HintText",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=COLORS["ink_600"],
        leftIndent=12,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="VocabTerm",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=COLORS["ink_800"],
    ))

    return styles, accent, accent_light


# ============================================================================
# HELPER COMPONENTS
# ============================================================================
def create_section_header(title: str, accent_color) -> Table:
    """Create a styled section header with colored left border."""
    header_table = Table(
        [[Paragraph(f"<b>{title}</b>", ParagraphStyle(
            name="SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=COLORS["ink_800"],
            leading=16,
        ))]],
        colWidths=[7.5 * inch],
        rowHeights=[0.35 * inch]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_50"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
        ("LINEBEFORE", (0, 0), (0, -1), 4, accent_color),
    ]))
    return header_table


def create_workspace_box(lines: int = 4, accent_color=None) -> Table:
    """Create a styled workspace box for student work."""
    if accent_color is None:
        accent_color = COLORS["ink_300"]

    # Create dotted lines for writing
    line_content = []
    for _ in range(lines):
        line_content.append("")

    workspace = Table(
        [["\n".join(line_content)]],
        colWidths=[7.5 * inch],
        rowHeights=[lines * 0.3 * inch]
    )
    workspace.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, COLORS["ink_200"]),
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["white"]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent_color),
    ]))
    return workspace


def create_info_box(content: str, styles, bg_color, border_color) -> Table:
    """Create an info/highlight box."""
    box = Table(
        [[Paragraph(content, styles["BodyText"])]],
        colWidths=[7.5 * inch]
    )
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return box


def add_bullet_list(elements: list, items: list, style, bullet_color=None) -> None:
    """Add a styled bulleted list to elements."""
    if bullet_color is None:
        bullet_color = COLORS["ink_400"]

    bullet_style = ParagraphStyle(
        name="BulletItem",
        parent=style,
        leftIndent=16,
        firstLineIndent=-12,
        spaceBefore=2,
        spaceAfter=2,
    )

    for item in items:
        elements.append(Paragraph(f"<font color='#{bullet_color.hexval()[2:]}'>\u2022</font>  {item}", bullet_style))


def create_divider() -> HRFlowable:
    """Create a subtle horizontal divider."""
    return HRFlowable(
        width="100%",
        thickness=1,
        color=COLORS["ink_200"],
        spaceBefore=8,
        spaceAfter=8,
    )


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

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLORS["navy_700"], spaceBefore=0, spaceAfter=16))

    # ===== CLASS COMPOSITION =====
    comp = meta.get("class_composition", {})
    if comp:
        elements.append(create_section_header("CLASS COMPOSITION", COLORS["ink_600"]))
        elements.append(Spacer(1, 8))

        # Readiness levels table with colors
        readiness_data = [
            [
                Paragraph("<b>Below Level</b>", ParagraphStyle(name="t1", fontSize=9, textColor=COLORS["below"])),
                Paragraph("<b>Approaching</b>", ParagraphStyle(name="t2", fontSize=9, textColor=COLORS["approaching"])),
                Paragraph("<b>At Level</b>", ParagraphStyle(name="t3", fontSize=9, textColor=COLORS["at"])),
                Paragraph("<b>Above Level</b>", ParagraphStyle(name="t4", fontSize=9, textColor=COLORS["above"])),
            ],
            [
                str(comp.get("below_level", 0)),
                str(comp.get("approaching_level", 0)),
                str(comp.get("at_level", 0)),
                str(comp.get("above_level", 0)),
            ]
        ]

        t1 = Table(readiness_data, colWidths=[1.75 * inch] * 4)
        t1.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, 1), 14),
            ("BACKGROUND", (0, 1), (0, 1), COLORS["below_light"]),
            ("BACKGROUND", (1, 1), (1, 1), COLORS["approaching_light"]),
            ("BACKGROUND", (2, 1), (2, 1), COLORS["at_light"]),
            ("BACKGROUND", (3, 1), (3, 1), COLORS["above_light"]),
            ("TEXTCOLOR", (0, 1), (0, 1), COLORS["below"]),
            ("TEXTCOLOR", (1, 1), (1, 1), COLORS["approaching"]),
            ("TEXTCOLOR", (2, 1), (2, 1), COLORS["at"]),
            ("TEXTCOLOR", (3, 1), (3, 1), COLORS["above"]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, COLORS["ink_200"]),
            ("LINEBELOW", (0, 0), (-1, 0), 1, COLORS["ink_200"]),
        ]))
        elements.append(t1)

        # EL levels if present
        el_total = comp.get("el_emerging", 0) + comp.get("el_expanding", 0) + comp.get("el_bridging", 0)
        if el_total > 0:
            elements.append(Spacer(1, 8))
            el_text = f"<b>English Learners:</b> Emerging ({comp.get('el_emerging', 0)}) \u2022 Expanding ({comp.get('el_expanding', 0)}) \u2022 Bridging ({comp.get('el_bridging', 0)})"
            elements.append(Paragraph(el_text, styles["SmallText"]))

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

    # ===== SESSION STRUCTURE =====
    structure = data.get("session_structure", {})
    if structure:
        elements.append(create_section_header("SESSION STRUCTURE", COLORS["navy_700"]))
        elements.append(Spacer(1, 8))

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
                    Paragraph(f"<font color='#{color.hexval()[2:]}'>&#9632;</font> <b>{label}</b>",
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

    # ===== DIFFERENTIATION GUIDE =====
    diff = data.get("differentiation_overview", {})
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
                # Level header
                level_header = Table([[
                    Paragraph(f"<b>{level_name}</b>", ParagraphStyle(name="lh", fontSize=11, textColor=color)),
                ]], colWidths=[7.5 * inch])
                level_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, color),
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

    # ===== MATERIALS =====
    materials = data.get("materials_list", [])
    if materials:
        elements.append(create_section_header("MATERIALS NEEDED", COLORS["ink_600"]))
        elements.append(Spacer(1, 6))
        add_bullet_list(elements, materials, styles["BodyText"], COLORS["gold_600"])
        elements.append(Spacer(1, 12))

    # ===== MISCONCEPTIONS =====
    misconceptions = data.get("common_misconceptions", [])
    if misconceptions:
        elements.append(create_section_header("COMMON MISCONCEPTIONS", COLORS["below"]))
        elements.append(Spacer(1, 6))

        for m in misconceptions:
            misc_box = Table([[
                Paragraph(f"<font color='#{COLORS['below'].hexval()[2:]}'>&#9632;&#9632;</font> <b>Misconception:</b> {m.get('misconception', '')}", styles["BodyText"]),
            ], [
                Paragraph(f"<font color='#{COLORS['at'].hexval()[2:]}'>\u2713</font> <b>Address by:</b> {m.get('how_to_address', '')}", styles["SmallText"]),
            ]], colWidths=[7.5 * inch])
            misc_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["below_light"]),
                ("BACKGROUND", (0, 1), (-1, 1), COLORS["at_light"]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            elements.append(misc_box)
            elements.append(Spacer(1, 6))

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
        elements.append(Spacer(1, 16))

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
        elements.append(Paragraph(f"<font color='#{accent.hexval()[2:]}'>&#9866;&#9632;</font> <b>YOUR TURN</b>", ParagraphStyle(
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
        elements.append(Paragraph(f"<font color='#{COLORS['gold_600'].hexval()[2:]}'>&#9733;</font> <b>APPLY IT</b>", ParagraphStyle(
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
            Paragraph(f"<font color='#{COLORS['above'].hexval()[2:]}'>&#9650;</font> <b>EXTENSION CHALLENGE: {extension.get('title', '')}</b>", ParagraphStyle(
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

    # ===== SENTENCE FRAMES =====
    frames = data.get("sentence_frames", [])
    if frames:
        frames_header = Table([[
            Paragraph(f"<font color='#{COLORS['ink_600'].hexval()[2:]}'>&#9632;</font> <b>SENTENCE FRAMES</b>", ParagraphStyle(
                name="sfheader", fontSize=10, textColor=COLORS["ink_700"]
            ))
        ]], colWidths=[7.5 * inch])
        frames_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLORS["ink_100"]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(frames_header)

        for frame in frames:
            elements.append(Paragraph(f"\u2022 {frame}", styles["SmallText"]))
        elements.append(Spacer(1, 12))

    # ===== WORD BANK =====
    word_bank = data.get("word_bank", [])
    if word_bank:
        words_text = "   \u2022   ".join(word_bank)
        word_box = Table([[
            Paragraph(f"<b>WORD BANK:</b>  {words_text}", ParagraphStyle(
                name="wordbank", fontSize=10, textColor=accent, alignment=TA_CENTER
            ))
        ]], colWidths=[7.5 * inch])
        word_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 2, accent),
            ("BACKGROUND", (0, 0), (-1, -1), accent_light),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(word_box)
        elements.append(Spacer(1, 14))

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
