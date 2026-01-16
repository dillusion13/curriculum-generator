"""
JSON to PDF Converter - Creates readable PDFs from standards JSON files.
"""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Color palette matching the app design
COLORS = {
    "ink_900": colors.HexColor("#1a1a2e"),
    "ink_700": colors.HexColor("#2d2d44"),
    "ink_500": colors.HexColor("#4a4a68"),
    "ink_300": colors.HexColor("#8e8ea0"),
    "ink_100": colors.HexColor("#f4f4f6"),
    "navy_700": colors.HexColor("#1e3a5f"),
    "navy_500": colors.HexColor("#2c5282"),
    "navy_100": colors.HexColor("#e8f0f8"),
    "gold_600": colors.HexColor("#b8860b"),
    "gold_100": colors.HexColor("#fdf6eb"),
    "white": colors.white,
    "red_500": colors.HexColor("#dc2626"),
    "orange_500": colors.HexColor("#ea580c"),
    "green_500": colors.HexColor("#16a34a"),
    "purple_500": colors.HexColor("#7c3aed"),
    "teal_500": colors.HexColor("#0d9488"),
}


def create_styles():
    """Create paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=COLORS["navy_700"],
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=COLORS["navy_700"],
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        borderColor=COLORS["gold_600"],
        borderWidth=2,
        borderPadding=5,
        leftIndent=0,
    ))

    styles.add(ParagraphStyle(
        name='SubsectionTitle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=COLORS["ink_700"],
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='ItemTitle',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=COLORS["navy_500"],
        spaceBefore=10,
        spaceAfter=5,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='ContentText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLORS["ink_700"],
        spaceBefore=3,
        spaceAfter=3,
        leading=14,
        fontName='Helvetica'
    ))

    styles.add(ParagraphStyle(
        name='BulletText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLORS["ink_500"],
        leftIndent=15,
        spaceBefore=2,
        spaceAfter=2,
        fontName='Helvetica'
    ))

    styles.add(ParagraphStyle(
        name='CodeKey',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLORS["gold_600"],
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=3
    ))

    styles.add(ParagraphStyle(
        name='MetaText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLORS["ink_300"],
        spaceBefore=2,
        spaceAfter=2,
        fontName='Helvetica-Oblique'
    ))

    return styles


def render_value(value, styles, depth=0, parent_key=""):
    """Recursively render JSON values as flowables."""
    elements = []
    indent = depth * 15

    if isinstance(value, dict):
        for key, val in value.items():
            # Skip metadata at root level - handled separately
            if depth == 0 and key == "metadata":
                continue

            # Format the key nicely
            display_key = key.replace("_", " ").title()

            # Determine style based on depth
            if depth == 0:
                elements.append(Spacer(1, 15))
                elements.append(Paragraph(
                    f"<font color='#b8860b'>&#9632;</font> {display_key}",
                    styles['SectionTitle']
                ))
            elif depth == 1:
                elements.append(Paragraph(display_key, styles['SubsectionTitle']))
            elif depth == 2:
                elements.append(Paragraph(display_key, styles['ItemTitle']))
            else:
                elements.append(Paragraph(
                    f"<b>{display_key}:</b>",
                    styles['ContentText']
                ))

            # Render the value
            elements.extend(render_value(val, styles, depth + 1, key))

    elif isinstance(value, list):
        if len(value) > 0:
            # Check if it's a list of simple strings
            if all(isinstance(item, str) for item in value):
                for item in value:
                    elements.append(Paragraph(
                        f"<bullet>&bull;</bullet> {item}",
                        styles['BulletText']
                    ))
            # List of dicts
            elif all(isinstance(item, dict) for item in value):
                for i, item in enumerate(value):
                    elements.extend(render_value(item, styles, depth, parent_key))
                    if i < len(value) - 1:
                        elements.append(Spacer(1, 5))
            else:
                # Mixed list
                for item in value:
                    if isinstance(item, str):
                        elements.append(Paragraph(
                            f"<bullet>&bull;</bullet> {item}",
                            styles['BulletText']
                        ))
                    else:
                        elements.extend(render_value(item, styles, depth, parent_key))
    else:
        # Simple value
        text = str(value) if value is not None else ""
        if text:
            elements.append(Paragraph(text, styles['ContentText']))

    return elements


def render_metadata(metadata, styles):
    """Render metadata section at the top of the document."""
    elements = []

    if "title" in metadata:
        elements.append(Paragraph(metadata["title"], styles['DocTitle']))

    # Create a summary table for metadata
    meta_items = []
    for key, val in metadata.items():
        if key == "title":
            continue
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        elif isinstance(val, dict):
            val = ", ".join(f"{k}: {v}" for k, v in val.items())

        display_key = key.replace("_", " ").title()
        meta_items.append([display_key, str(val)])

    if meta_items:
        table = Table(meta_items, colWidths=[1.5*inch, 5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), COLORS["ink_500"]),
            ('TEXTCOLOR', (1, 0), (-1, -1), COLORS["ink_700"]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    # Add a divider line
    elements.append(Table(
        [[""]],
        colWidths=[6.5*inch],
        rowHeights=[2]
    ))
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS["gold_600"]),
    ])
    elements[-1].setStyle(table_style)
    elements.append(Spacer(1, 10))

    return elements


def json_to_pdf(json_path: Path, output_path: Path):
    """Convert a JSON file to a formatted PDF."""
    print(f"Converting {json_path.name} to PDF...")

    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Create PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    elements = []

    # Add title based on filename
    title = json_path.stem.replace("_", " ").title()
    elements.append(Paragraph(title, styles['DocTitle']))
    elements.append(Spacer(1, 10))

    # Render metadata if present
    if "metadata" in data:
        elements.extend(render_metadata(data["metadata"], styles))

    # Render the rest of the content
    elements.extend(render_value(data, styles, depth=0))

    # Build PDF
    doc.build(elements)
    print(f"  Created: {output_path.name}")


def main():
    """Convert all standards JSON files to PDFs."""
    files_dir = Path(__file__).parent.parent / "files"
    outputs_dir = Path(__file__).parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    json_files = [
        "ca_k12_standards_enhanced.json",
        "ca_k12_standards_readiness.json",
        "topic_standards_mapping_6_8.json",
    ]

    print("\n" + "="*50)
    print("Converting Standards JSON files to PDF")
    print("="*50 + "\n")

    for filename in json_files:
        json_path = files_dir / filename
        if json_path.exists():
            output_name = filename.replace(".json", ".pdf")
            output_path = outputs_dir / output_name
            json_to_pdf(json_path, output_path)
        else:
            print(f"  Warning: {filename} not found")

    print("\n" + "="*50)
    print("Conversion complete!")
    print(f"PDFs saved to: {outputs_dir}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
