"""
Shared PDF styling constants and utilities.

This module centralizes all PDF styling to ensure consistency across:
- pdf_generator.py (teacher guides, student handouts)
- json_to_pdf.py (standards PDFs)
- generate_research_pdf.py (pedagogical approaches)
- generate_comparison_report.py (model comparison)
"""
from functools import lru_cache
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, HRFlowable


# ============================================================================
# CENTRALIZED COLOR PALETTE - "Scholarly Modern" Design System
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

    # Model comparison colors
    "claude": colors.HexColor("#d97706"),  # Anthropic orange
    "gemini": colors.HexColor("#4285f4"),  # Google blue

    # Utility
    "white": colors.white,
    "success": colors.HexColor("#059669"),
    "success_light": colors.HexColor("#d1fae5"),
    "error": colors.HexColor("#dc2626"),
    "error_light": colors.HexColor("#fee2e2"),

    # Legacy aliases for compatibility
    "red_500": colors.HexColor("#dc2626"),
    "orange_500": colors.HexColor("#ea580c"),
    "green_500": colors.HexColor("#16a34a"),
    "green_600": colors.HexColor("#16a34a"),
    "purple_500": colors.HexColor("#7c3aed"),
    "purple_600": colors.HexColor("#7c3aed"),
    "teal_500": colors.HexColor("#0d9488"),
    "teal_600": colors.HexColor("#0d9488"),
    "teal_100": colors.HexColor("#f0fdfa"),
    "purple_100": colors.HexColor("#f5f3ff"),
    "green_100": colors.HexColor("#f0fdf4"),
}

# Level color mapping for student handouts
LEVEL_COLORS = {
    "below_level": ("below", "below_light"),
    "approaching_level": ("approaching", "approaching_light"),
    "at_level": ("at", "at_light"),
    "above_level": ("above", "above_light"),
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def hex_color(key: str) -> str:
    """Get hex string (without #) for use in Paragraph HTML markup.

    Example: f"<font color='#{hex_color('navy_700')}'>Text</font>"
    """
    return COLORS[key].hexval()[2:]


def get_color(key: str) -> colors.Color:
    """Get a color from the palette by key."""
    return COLORS[key]


# ============================================================================
# BASE STYLES
# ============================================================================
@lru_cache(maxsize=8)
def get_base_styles(level_key: str = None):
    """Create custom paragraph styles with optional level-specific colors.

    Args:
        level_key: Optional readiness level ('below_level', 'approaching_level', etc.)
                   to customize accent colors.

    Returns:
        tuple: (styles dict, accent color, accent_light color)
    """
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
# REUSABLE COMPONENTS
# ============================================================================
# Import Paragraph here to avoid circular imports while keeping it available for components
from reportlab.platypus import Paragraph as _Paragraph


def create_section_header(title: str, accent_color) -> Table:
    """Create a styled section header with colored left border."""
    header_table = Table(
        [[_Paragraph(f"<b>{title}</b>", ParagraphStyle(
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


def create_info_box(content: str, styles, bg_color, border_color) -> Table:
    """Create an info/highlight box."""
    box = Table(
        [[_Paragraph(content, styles["BodyText"])]],
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


def create_divider() -> HRFlowable:
    """Create a subtle horizontal divider."""
    return HRFlowable(
        width="100%",
        thickness=1,
        color=COLORS["ink_200"],
        spaceBefore=8,
        spaceAfter=8,
    )


def apply_standard_padding(table_style: list) -> list:
    """Add standard padding to a TableStyle command list."""
    return table_style + [
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]


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
        elements.append(_Paragraph(f"<font color='#{bullet_color.hexval()[2:]}'>\u2022</font>  {item}", bullet_style))
