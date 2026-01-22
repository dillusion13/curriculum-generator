"""
DOCX Styling Constants and Utilities.

Centralized styling for Word document generation, matching the design system
used in pdf_styles.py for visual consistency across output formats.
"""
from docx.shared import Pt, RGBColor, Inches, Twips
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ============================================================================
# COLOR PALETTE - "Scholarly Modern" Design System
# ============================================================================
# Hex values without '#' prefix for python-docx RGBColor conversion
COLORS = {
    # Core ink palette (warm grays)
    "ink_900": "1a1a2e",
    "ink_800": "2d2d44",
    "ink_700": "404058",
    "ink_600": "5c5c73",
    "ink_500": "7a7a8c",
    "ink_400": "9e9eab",
    "ink_300": "c4c4cd",
    "ink_200": "e0e0e6",
    "ink_100": "f0f0f3",
    "ink_50": "f8f8fa",

    # Navy - Primary accent
    "navy_700": "1e3a5f",
    "navy_600": "2c4a6e",
    "navy_500": "3d5a80",
    "navy_100": "e8eef4",

    # Gold - Secondary accent
    "gold_600": "b8860b",
    "gold_500": "d4a574",
    "gold_400": "e4bb84",
    "gold_100": "fdf6eb",

    # Readiness levels
    "below": "dc2626",
    "below_light": "fef2f2",
    "below_border": "fecaca",

    "approaching": "ea580c",
    "approaching_light": "fff7ed",
    "approaching_border": "fed7aa",

    "at": "16a34a",
    "at_light": "f0fdf4",
    "at_border": "bbf7d0",

    "above": "7c3aed",
    "above_light": "f5f3ff",
    "above_border": "ddd6fe",

    # EL levels - Teal spectrum
    "emerging": "0d9488",
    "emerging_light": "f0fdfa",
    "expanding": "0891b2",
    "expanding_light": "ecfeff",
    "bridging": "0369a1",
    "bridging_light": "f0f9ff",

    # Utility
    "white": "ffffff",
    "black": "000000",
    "success": "059669",
    "success_light": "d1fae5",
    "error": "dc2626",
    "error_light": "fee2e2",
}

# Level color mapping for student handouts
LEVEL_COLORS = {
    "below_level": {
        "accent": "below",
        "light": "below_light",
        "border": "below_border",
        "name": "Below Level",
    },
    "approaching_level": {
        "accent": "approaching",
        "light": "approaching_light",
        "border": "approaching_border",
        "name": "Approaching Level",
    },
    "at_level": {
        "accent": "at",
        "light": "at_light",
        "border": "at_border",
        "name": "At Level",
    },
    "above_level": {
        "accent": "above",
        "light": "above_light",
        "border": "above_border",
        "name": "Above Level",
    },
}


# ============================================================================
# TYPOGRAPHY SETTINGS
# ============================================================================
FONTS = {
    "heading": "Georgia",  # Serif for headers - scholarly feel
    "body": "Calibri",     # Sans-serif for body - modern, readable
}

FONT_SIZES = {
    "title": Pt(22),
    "heading1": Pt(14),
    "heading2": Pt(12),
    "body": Pt(10),
    "i_can": Pt(11),
    "hint": Pt(9),
    "small": Pt(9),
    "label": Pt(9),
}

SPACING = {
    "section_before": Pt(16),
    "section_after": Pt(8),
    "paragraph_after": Pt(6),
    "list_item_after": Pt(4),
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def hex_to_rgb(hex_code: str) -> RGBColor:
    """Convert hex string to RGBColor for python-docx."""
    hex_code = hex_code.lstrip('#')
    return RGBColor(
        int(hex_code[0:2], 16),
        int(hex_code[2:4], 16),
        int(hex_code[4:6], 16)
    )


def get_color(key: str) -> RGBColor:
    """Get RGBColor from palette by key."""
    return hex_to_rgb(COLORS[key])


def get_level_colors(level_key: str) -> dict:
    """Get color configuration for a readiness level.

    Returns dict with 'accent', 'light', 'border' RGBColors and 'name' string.
    """
    if level_key not in LEVEL_COLORS:
        # Default to navy for teacher guide or unknown levels
        return {
            "accent": get_color("navy_700"),
            "light": get_color("navy_100"),
            "border": get_color("ink_200"),
            "name": level_key.replace("_", " ").title(),
        }

    level_config = LEVEL_COLORS[level_key]
    return {
        "accent": get_color(COLORS[level_config["accent"]]) if level_config["accent"] in COLORS else hex_to_rgb(COLORS[level_config["accent"]]),
        "light": hex_to_rgb(COLORS[level_config["light"]]),
        "border": hex_to_rgb(COLORS[level_config["border"]]),
        "name": level_config["name"],
    }


def get_level_accent(level_key: str) -> RGBColor:
    """Get the primary accent color for a readiness level."""
    if level_key in LEVEL_COLORS:
        return hex_to_rgb(COLORS[LEVEL_COLORS[level_key]["accent"]])
    return get_color("navy_700")


def get_level_light(level_key: str) -> str:
    """Get the light background hex color for a readiness level (for XML)."""
    if level_key in LEVEL_COLORS:
        return COLORS[LEVEL_COLORS[level_key]["light"]]
    return COLORS["navy_100"]


def get_level_name(level_key: str) -> str:
    """Get display name for a readiness level."""
    if level_key in LEVEL_COLORS:
        return LEVEL_COLORS[level_key]["name"]
    return level_key.replace("_", " ").title()


# ============================================================================
# TABLE STYLING HELPERS
# ============================================================================
def set_cell_shading(cell, hex_color: str):
    """Set background shading for a table cell.

    Args:
        cell: A python-docx table cell
        hex_color: Hex color code without '#' prefix
    """
    shading_elm = parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    )
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_border(cell, side: str, color: str, width: int = 8, style: str = "single"):
    """Set border on a specific side of a cell.

    Args:
        cell: A python-docx table cell
        side: 'top', 'bottom', 'left', 'right'
        color: Hex color code without '#' prefix
        width: Border width in eighths of a point (8 = 1pt)
        style: Border style ('single', 'dotted', 'dashed', etc.)
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(parse_xml(f'<w:tcBorders {nsdecls("w")}/>').tag)
    if tcBorders is None:
        tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
        tcPr.append(tcBorders)

    border_elem = parse_xml(
        f'<w:{side} {nsdecls("w")} w:val="{style}" w:sz="{width}" w:color="{color}"/>'
    )
    # Remove existing border for this side if present
    existing = tcBorders.find(f'{{{tcBorders.nsmap["w"]}}}{side}')
    if existing is not None:
        tcBorders.remove(existing)
    tcBorders.append(border_elem)


def set_cell_borders(cell, color: str, width: int = 8, style: str = "single"):
    """Set all borders on a cell."""
    for side in ["top", "bottom", "left", "right"]:
        set_cell_border(cell, side, color, width, style)


def set_table_borders(table, color: str = None, width: int = 8):
    """Set borders on entire table.

    Args:
        table: A python-docx table
        color: Hex color for borders (default ink_200)
        width: Border width in eighths of a point
    """
    if color is None:
        color = COLORS["ink_200"]

    for row in table.rows:
        for cell in row.cells:
            set_cell_borders(cell, color, width)


def remove_cell_borders(cell):
    """Remove all borders from a cell."""
    for side in ["top", "bottom", "left", "right"]:
        set_cell_border(cell, side, "FFFFFF", 0, "nil")
