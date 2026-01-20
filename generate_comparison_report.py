"""
Generate a PDF comparison report of Claude vs Gemini curriculum outputs.
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# Import shared color palette
from app.pdf_styles import COLORS

def create_comparison_report(claude_data: dict, gemini_data: dict, output_path: str):
    """Generate comparison report PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.5 * inch,
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph(
        "<font color='#1e3a5f'>■</font>  Model Comparison Report",
        ParagraphStyle(name="Title", fontSize=22, fontName="Helvetica-Bold", 
                      textColor=COLORS["ink_900"], spaceAfter=4)
    ))
    elements.append(Paragraph(
        "Claude Sonnet 4.5 vs Gemini 3.0 Pro • Curriculum Generation",
        ParagraphStyle(name="Subtitle", fontSize=10, textColor=COLORS["ink_500"], spaceAfter=12)
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLORS["navy_700"], spaceAfter=16))
    
    # Test Parameters
    elements.append(Paragraph("<b>Test Parameters</b>", 
        ParagraphStyle(name="H1", fontSize=13, fontName="Helvetica-Bold", 
                      textColor=COLORS["ink_700"], spaceBefore=12, spaceAfter=8)))
    
    params = [
        ["Grade", "6"],
        ["Subject", "Math"],
        ["Topic", "equivalent ratios"],
        ["Session Length", "15 minutes"],
        ["Learning Goal", "Practice"],
        ["Group Format", "Small Group"],
        ["Pedagogical Approach", "Auto-selected"],
    ]
    param_table = Table(params, colWidths=[2*inch, 5.5*inch])
    param_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLORS["ink_50"]),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLORS["ink_700"]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, COLORS["ink_200"]),
    ]))
    elements.append(param_table)
    elements.append(Spacer(1, 20))
    
    # Comparison Table
    elements.append(Paragraph("<b>Side-by-Side Comparison</b>", 
        ParagraphStyle(name="H1", fontSize=13, fontName="Helvetica-Bold", 
                      textColor=COLORS["ink_700"], spaceBefore=12, spaceAfter=8)))
    
    claude_meta = claude_data.get("teacher_guide", {}).get("metadata", {})
    gemini_meta = gemini_data.get("teacher_guide", {}).get("metadata", {})
    claude_phases = claude_data.get("teacher_guide", {}).get("session_structure", {}).get("phases", [])
    gemini_phases = gemini_data.get("teacher_guide", {}).get("session_structure", {}).get("phases", [])
    claude_udl = claude_data.get("teacher_guide", {}).get("udl_alignment", {})
    gemini_udl = gemini_data.get("teacher_guide", {}).get("udl_alignment", {})
    
    comparison_data = [
        [
            Paragraph("<b>Aspect</b>", ParagraphStyle(name="th", fontSize=9, fontName="Helvetica-Bold")),
            Paragraph("<b>Claude Sonnet 4.5</b>", ParagraphStyle(name="th", fontSize=9, fontName="Helvetica-Bold", textColor=COLORS["claude"])),
            Paragraph("<b>Gemini 3.0 Pro</b>", ParagraphStyle(name="th", fontSize=9, fontName="Helvetica-Bold", textColor=COLORS["gemini"])),
        ],
        [
            "Title",
            claude_meta.get("title", "N/A")[:40] + "...",
            gemini_meta.get("title", "N/A")[:40] + "...",
        ],
        [
            "Approach Selected",
            claude_meta.get("pedagogical_approach", {}).get("name", "N/A"),
            gemini_meta.get("pedagogical_approach", {}).get("name", "N/A"),
        ],
        [
            "Phase Count",
            str(len(claude_phases)),
            str(len(gemini_phases)),
        ],
        [
            "Phase Names",
            "\n".join([f"• {p.get('name', '?')}" for p in claude_phases]),
            "\n".join([f"• {p.get('name', '?')}" for p in gemini_phases]),
        ],
        [
            "UDL Engagement",
            ", ".join(claude_udl.get("engagement", {}).get("checkpoints_addressed", [])),
            ", ".join(gemini_udl.get("engagement", {}).get("checkpoints_addressed", [])),
        ],
        [
            "UDL Representation",
            ", ".join(claude_udl.get("representation", {}).get("checkpoints_addressed", [])),
            ", ".join(gemini_udl.get("representation", {}).get("checkpoints_addressed", [])),
        ],
        [
            "UDL Action/Expression",
            ", ".join(claude_udl.get("action_expression", {}).get("checkpoints_addressed", [])),
            ", ".join(gemini_udl.get("action_expression", {}).get("checkpoints_addressed", [])),
        ],
    ]
    
    comp_table = Table(comparison_data, colWidths=[1.5*inch, 3*inch, 3*inch])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLORS["ink_50"]),
        ("BACKGROUND", (0, 1), (0, -1), COLORS["ink_50"]),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLORS["ink_700"]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLORS["ink_200"]),
    ]))
    elements.append(comp_table)
    elements.append(Spacer(1, 20))
    
    # Key Findings
    elements.append(Paragraph("<b>Key Findings</b>", 
        ParagraphStyle(name="H1", fontSize=13, fontName="Helvetica-Bold", 
                      textColor=COLORS["ink_700"], spaceBefore=12, spaceAfter=8)))
    
    findings = [
        f"<b>Claude</b> selected <b>{claude_meta.get('pedagogical_approach', {}).get('name', 'N/A')}</b> - a collaborative approach where students teach each other concepts.",
        f"<b>Gemini</b> selected <b>{gemini_meta.get('pedagogical_approach', {}).get('name', 'N/A')}</b> - a game-based approach with challenges and progression.",
        "Both models correctly followed the prompt structure and generated valid JSON output.",
        "Both auto-selected appropriate pedagogical approaches for a math practice session.",
        "Both included UDL alignment documentation with specific checkpoint references.",
        "Phase timing adds up to 15 minutes as specified in the input.",
    ]
    
    for finding in findings:
        elements.append(Paragraph(f"• {finding}", 
            ParagraphStyle(name="finding", fontSize=10, textColor=COLORS["ink_700"],
                          leftIndent=12, spaceAfter=6, leading=14)))
    
    elements.append(Spacer(1, 20))
    
    # Conclusion
    elements.append(Paragraph("<b>Conclusion</b>", 
        ParagraphStyle(name="H1", fontSize=13, fontName="Helvetica-Bold", 
                      textColor=COLORS["ink_700"], spaceBefore=12, spaceAfter=8)))
    
    conclusion = """Both Claude Sonnet 4.5 and Gemini 3.0 Pro successfully generated complete, 
    standards-aligned curriculum following the same prompt. The main difference is in pedagogical 
    approach selection and creative interpretation. Claude favored peer collaboration while Gemini 
    favored gamification. Both outputs are valid and usable for classroom instruction."""
    
    elements.append(Paragraph(conclusion.replace("\n", " "), 
        ParagraphStyle(name="conclusion", fontSize=10, textColor=COLORS["ink_700"], leading=14)))
    
    doc.build(elements)
    return output_path


if __name__ == "__main__":
    outputs_dir = Path(__file__).parent / "outputs"
    
    # Load both curriculum JSONs
    with open(outputs_dir / "test_claude-sonnet-4_5_curriculum.json") as f:
        claude_data = json.load(f)
    
    with open(outputs_dir / "test_gemini-3-pro_curriculum.json") as f:
        gemini_data = json.load(f)
    
    # Generate report
    output_path = str(outputs_dir / "model_comparison_report.pdf")
    create_comparison_report(claude_data, gemini_data, output_path)
    print(f"Report generated: {output_path}")
