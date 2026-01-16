# PDF Generator - Claude Code Prompt

## Task

You are generating print-ready PDF documents from a structured curriculum JSON. Create **5 separate PDF files**:

1. `teacher_guide.pdf`
2. `student_below_level.pdf`
3. `student_approaching_level.pdf`
4. `student_at_level.pdf`
5. `student_above_level.pdf`

## Input

You will receive a JSON object with two main sections:
- `teacher_guide`: Contains all information for the teacher PDF
- `student_materials`: Contains `below_level`, `approaching_level`, `at_level`, `above_level` objects

```json
{{CURRICULUM_JSON}}
```

## Technical Requirements

- Use Python with `reportlab` library for PDF generation
- Output all PDFs to `/mnt/user-data/outputs/`
- Page size: Letter (8.5" x 11")
- Fonts: Helvetica family (built into reportlab)
- Include page numbers on multi-page documents

## Design System

### Color Palette
```python
COLORS = {
    "primary": "#2563EB",        # Blue - headers, accents
    "primary_light": "#DBEAFE",  # Light blue - backgrounds
    "secondary": "#059669",      # Green - success, answers
    "warning": "#D97706",        # Orange - important notes
    "text_dark": "#1F2937",      # Near black - body text
    "text_medium": "#6B7280",    # Gray - secondary text
    "text_light": "#9CA3AF",     # Light gray - hints
    "border": "#E5E7EB",         # Light gray - borders
    "background": "#F9FAFB",     # Off-white - section backgrounds
    "white": "#FFFFFF"
}
```

### Typography Scale
```python
FONTS = {
    "title": ("Helvetica-Bold", 24),
    "h1": ("Helvetica-Bold", 18),
    "h2": ("Helvetica-Bold", 14),
    "h3": ("Helvetica-Bold", 12),
    "body": ("Helvetica", 11),
    "body_small": ("Helvetica", 10),
    "caption": ("Helvetica", 9),
    "label": ("Helvetica-Bold", 10),
    "icon": ("MaterialSymbols", 16)  # For section icons
}
```

### Icon System (Google Fonts - Material Symbols)

Download and register the Material Symbols font for use in PDFs:

```python
import urllib.request
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Download Material Symbols Rounded font
FONT_URL = "https://github.com/google/material-design-icons/raw/master/variablefont/MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf"
FONT_PATH = "/tmp/MaterialSymbolsRounded.ttf"

urllib.request.urlretrieve(FONT_URL, FONT_PATH)
pdfmetrics.registerFont(TTFont("MaterialSymbols", FONT_PATH))
```

### Icon Mapping (Unicode Codepoints)

Use these Material Symbols icons for section headers:

```python
ICONS = {
    # Student handout sections
    "goal": "\uE8B8",           # track_changes (target-like)
    "vocabulary": "\uE865",     # menu_book
    "example": "\uE3C9",        # edit
    "guided_practice": "\uE7EF", # groups
    "independent": "\uE7FD",    # person
    "word_bank": "\uE8EF",      # format_list_bulleted
    "sentence_frames": "\uE0B7", # chat
    "reflection": "\uE90F",     # psychology
    "hint": "\uE90F",           # lightbulb (tips_and_updates)
    "apply": "\uE80B",          # public (globe)
    "extension": "\uE148",      # trending_up
    
    # Teacher guide sections
    "standards": "\uE8D7",      # rule (checklist)
    "objectives": "\uE8B5",     # flag
    "materials": "\uE8F1",      # inventory_2
    "hook": "\uE838",           # lightbulb
    "instruction": "\uE80C",    # school
    "practice": "\uE3AE",       # draw
    "closure": "\uE876",        # check_circle
    "differentiation": "\uE8D5", # tune
    "el_support": "\uE8E2",     # translate
    "misconception": "\uE002",  # warning
    "discussion": "\uE0BF",     # forum
    "time": "\uE8B5",           # schedule
}
```

### Helper Function for Icon + Label Headers

```python
def draw_section_header(canvas, x, y, icon_key, label, width):
    """Draw a section header with icon and label."""
    icon = ICONS.get(icon_key, "")
    
    # Draw icon
    canvas.setFont("MaterialSymbols", 16)
    canvas.setFillColor(COLORS["primary"])
    canvas.drawString(x, y, icon)
    
    # Draw label
    canvas.setFont("Helvetica-Bold", 12)
    canvas.setFillColor(COLORS["text_dark"])
    canvas.drawString(x + 22, y, label)
    
    # Draw underline
    canvas.setStrokeColor(COLORS["border"])
    canvas.line(x, y - 4, x + width, y - 4)
```

### Spacing
```python
SPACING = {
    "margin": 0.5 * inch,        # Page margins
    "section_gap": 0.3 * inch,   # Between sections
    "item_gap": 0.15 * inch,     # Between items in a list
    "padding": 0.15 * inch       # Inside boxes/containers
}
```

---

## Teacher Guide PDF Specification

### Page 1: Overview

```
+-------------------------------------------------------------+
|  [PRIMARY COLOR BAR]                                         |
|  LESSON TITLE                                          Grade X|
|  Subject - Topic - Duration                                  |
+-------------------------------------------------------------+
|                                                              |
|  [rule icon] STANDARDS             CLASS COMPOSITION         |
|  +---------------------+           +---------------------+   |
|  | - 6.RP.A.1          |           | Below:      8       |   |
|  | - 6.RP.A.2          |           | Approaching: 10     |   |
|  | - 6.RP.A.3          |           | At Level:   7       |   |
|  +---------------------+           | Above:      3       |   |
|                                    +---------------------+   |
|                                    | EL Emerging:  3     |   |
|                                    | EL Expanding: 5     |   |
|                                    | EL Bridging:  2     |   |
|                                    +---------------------+   |
|                                                              |
|  [flag icon] LEARNING OBJECTIVES                             |
|  +-----------------------------------------------------+    |
|  | Objective: Students will...                          |    |
|  | Success Criteria: Students can...                    |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [inventory icon] MATERIALS NEEDED                           |
|  - Item 1        - Item 2        - Item 3                    |
|  - Item 4        - Item 5        - Item 6                    |
|                                                              |
+-------------------------------------------------------------+
```

### Page 2: Session Structure

```
+-------------------------------------------------------------+
|  SESSION STRUCTURE                                           |
+-------------------------------------------------------------+
|                                                              |
|  [lightbulb icon] HOOK (X min)                               |
|  +-----------------------------------------------------+    |
|  | Description text...                                  |    |
|  |                                                      |    |
|  | Teacher: ...                                         |    |
|  | Students: ...                                        |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [school icon] INSTRUCTION (X min)                           |
|  +-----------------------------------------------------+    |
|  | Description text...                                  |    |
|  |                                                      |    |
|  | Teacher: ...                                         |    |
|  | Students: ...                                        |    |
|  |                                                      |    |
|  | Key Points:                                          |    |
|  | - Point 1                                            |    |
|  | - Point 2                                            |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [draw icon] PRACTICE (X min)                                |
|  +-----------------------------------------------------+    |
|  | Description text...                                  |    |
|  | Grouping: ...                                        |    |
|  | Differentiation: ...                                 |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [check_circle icon] CLOSURE (X min)                         |
|  +-----------------------------------------------------+    |
|  | Description text...                                  |    |
|  | Exit Ticket: ...                                     |    |
|  +-----------------------------------------------------+    |
|                                                              |
+-------------------------------------------------------------+
```

### Page 3: Differentiation Guide

```
+-------------------------------------------------------------+
|  [tune icon] DIFFERENTIATION GUIDE                           |
+-------------------------------------------------------------+
|                                                              |
|  +----------------------+  +----------------------+          |
|  | BELOW LEVEL          |  | APPROACHING LEVEL    |          |
|  | [Light blue bg]      |  | [Light blue bg]      |          |
|  |                      |  |                      |          |
|  | Focus:               |  | Focus:               |          |
|  | ...                  |  | ...                  |          |
|  |                      |  |                      |          |
|  | Key Scaffolds:       |  | Key Scaffolds:       |          |
|  | - ...                |  | - ...                |          |
|  | - ...                |  | - ...                |          |
|  |                      |  |                      |          |
|  | Monitor for:         |  | Monitor for:         |          |
|  | ...                  |  | ...                  |          |
|  +----------------------+  +----------------------+          |
|                                                              |
|  +----------------------+  +----------------------+          |
|  | AT LEVEL             |  | ABOVE LEVEL          |          |
|  | [Light blue bg]      |  | [Light blue bg]      |          |
|  |                      |  |                      |          |
|  | Focus:               |  | Focus:               |          |
|  | ...                  |  | ...                  |          |
|  |                      |  |                      |          |
|  | Key Scaffolds:       |  | Key Scaffolds:       |          |
|  | - ...                |  | - ...                |          |
|  |                      |  |                      |          |
|  | Monitor for:         |  | Monitor for:         |          |
|  | ...                  |  | ...                  |          |
|  +----------------------+  +----------------------+          |
|                                                              |
+-------------------------------------------------------------+
```

### Page 4: EL Support & Teacher Notes

```
+-------------------------------------------------------------+
|  [translate icon] ENGLISH LEARNER SUPPORTS                   |
+-------------------------------------------------------------+
|                                                              |
|  EMERGING                                                    |
|  +-----------------------------------------------------+    |
|  | Pre-teach vocabulary: word1, word2, word3            |    |
|  | Visual supports: ...                                 |    |
|  | Partner with: ...                                    |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  EXPANDING                                                   |
|  +-----------------------------------------------------+    |
|  | Pre-teach vocabulary: ...                            |    |
|  | Visual supports: ...                                 |    |
|  | Partner with: ...                                    |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  BRIDGING                                                    |
|  +-----------------------------------------------------+    |
|  | Academic vocabulary: ...                             |    |
|  | Supports: ...                                        |    |
|  +-----------------------------------------------------+    |
|                                                              |
+-------------------------------------------------------------+
|  [warning icon] COMMON MISCONCEPTIONS                        |
|  +-----------------------------------------------------+    |
|  | [warning icon] Misconception: ...                    |    |
|  |   Address by: ...                                    |    |
|  |                                                      |    |
|  | [warning icon] Misconception: ...                    |    |
|  |   Address by: ...                                    |    |
|  +-----------------------------------------------------+    |
|                                                              |
+-------------------------------------------------------------+
|  [forum icon] DISCUSSION PROMPTS                             |
|  - Prompt 1                                                  |
|  - Prompt 2                                                  |
|                                                              |
|  [trending_up icon] EXTENSION IF TIME                        |
|  - Extension 1                                               |
|  - Extension 2                                               |
+-------------------------------------------------------------+
```

---

## Student Handout PDF Specifications

### Design Principles for Student Materials
1. **Clean and uncluttered** - ample white space, clear visual hierarchy
2. **Consistent layout** - students know where to look
3. **Readable fonts** - minimum 11pt for body text
4. **Clear workspace areas** - defined boxes for student work
5. **Visual cues** - icons and color to guide attention
6. **Scaffold visibility** - hints and supports clearly marked but not distracting

### Below Level Handout Structure

```
+-------------------------------------------------------------+
|  [PRIMARY COLOR BAR]                                         |
|  TITLE                                            Name: ___  |
|  -----------------------------------------------------------+
|  [target icon] GOAL: I can [i_can_statement]                 |
+-------------------------------------------------------------+
|                                                              |
|  [book icon] VOCABULARY                                      |
|  +-------------+-------------+-------------+-------------+   |
|  | [visual]    | [visual]    | [visual]    | [visual]    |   |
|  | term        | term        | term        | term        |   |
|  | definition  | definition  | definition  | definition  |   |
|  | ex: ...     | ex: ...     | ex: ...     | ex: ...     |   |
|  +-------------+-------------+-------------+-------------+   |
|                                                              |
|  [edit icon] EXAMPLE - Watch and follow along                |
|  +-----------------------------------------------------+    |
|  | Problem: ...                                         |    |
|  |                                                      |    |
|  | Step 1: [action]           ->  [result]              |    |
|  | Step 2: [action]           ->  [result]              |    |
|  | Step 3: [action]           ->  [result]              |    |
|  |                                                      |    |
|  | Answer: [solution in box]                            |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [groups icon] GUIDED PRACTICE - Try with help               |
|  +-----------------------------------------------------+    |
|  | 1. Problem...                                        |    |
|  |    [lightbulb icon] Hint: [scaffold]                 |    |
|  |    +-----------------------------------------------+ |    |
|  |    |                                               | |    |
|  |    |              [WORKSPACE]                      | |    |
|  |    |                                               | |    |
|  |    +-----------------------------------------------+ |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [person icon] YOUR TURN - Try on your own                   |
|  +-----------------------------------------------------+    |
|  | 1. Problem...                                        |    |
|  |    +-----------------------------------------------+ |    |
|  |    |                                               | |    |
|  |    |              [WORKSPACE]                      | |    |
|  |    |                                               | |    |
|  |    +-----------------------------------------------+ |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [list icon] WORD BANK                                       |
|  +-----------------------------------------------------+    |
|  |  word1  |  word2  |  word3  |  word4  |  word5      |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [chat icon] SENTENCE FRAMES                                 |
|  - The ratio of ___ to ___ is ___.                           |
|  - I found the answer by ___.                                |
|                                                              |
|  [psychology icon] REFLECTION                                |
|  Today I learned ________________________________________    |
|  _______________________________________________________    |
|                                                              |
+-------------------------------------------------------------+
```

### Approaching Level Handout Structure

```
+-------------------------------------------------------------+
|  [PRIMARY COLOR BAR]                                         |
|  TITLE                                            Name: ___  |
|  -----------------------------------------------------------+
|  [target icon] GOAL: I can [i_can_statement]                 |
+-------------------------------------------------------------+
|                                                              |
|  [book icon] KEY VOCABULARY                                  |
|  term - definition    |    term - definition                 |
|  term - definition    |    term - definition                 |
|                                                              |
|  [edit icon] EXAMPLE                                         |
|  +-----------------------------------------------------+    |
|  | Problem: ...                                         |    |
|  |                                                      |    |
|  | Step 1: ...                                          |    |
|  | Step 2: ...                                          |    |
|  | Step 3: ...                                          |    |
|  |                                                      |    |
|  | Answer: [solution]                                   |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [groups icon] GUIDED PRACTICE                               |
|  +-----------------------------------------------------+    |
|  | 1. Problem...                                        |    |
|  |    [lightbulb icon] Hint: [lighter scaffold]         |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  |                                                      |    |
|  | 2. Problem...                                        |    |
|  |    [lightbulb icon] Hint: ...                        |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [person icon] INDEPENDENT PRACTICE                          |
|  +-----------------------------------------------------+    |
|  | 1. Problem...              2. Problem...             |    |
|  | +------------------+       +------------------+      |    |
|  | |                  |       |                  |      |    |
|  | |   [WORKSPACE]    |       |   [WORKSPACE]    |      |    |
|  | |                  |       |                  |      |    |
|  | +------------------+       +------------------+      |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [chat icon] SENTENCE STARTERS                               |
|  - I solved this by...                                       |
|  - The answer is ___ because...                              |
|                                                              |
|  [psychology icon] REFLECTION                                |
|  What strategy worked best for you today?                    |
|  _______________________________________________________    |
|                                                              |
+-------------------------------------------------------------+
```

### At Level Handout Structure

```
+-------------------------------------------------------------+
|  [PRIMARY COLOR BAR]                                         |
|  TITLE                                            Name: ___  |
|  -----------------------------------------------------------+
|  [target icon] GOAL: I can [i_can_statement]                 |
+-------------------------------------------------------------+
|                                                              |
|  [book icon] VOCABULARY: term - definition | term - def      |
|                                                              |
|  [edit icon] EXAMPLE                                         |
|  +-----------------------------------------------------+    |
|  | Problem: ...                                         |    |
|  | Solution: [summary approach, not step-by-step]       |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [person icon] PRACTICE                                      |
|  +-----------------------------------------------------+    |
|  | 1. Problem...                                        |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  |                                                      |    |
|  | 2. Problem...                                        |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  |                                                      |    |
|  | 3. Problem...                                        |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [globe icon] APPLY IT - Real World Problem                  |
|  +-----------------------------------------------------+    |
|  | [Context/scenario]                                   |    |
|  |                                                      |    |
|  | Question: ...                                        |    |
|  |                                                      |    |
|  | +-------------------------------------------------+ |    |
|  | |                                                 | |    |
|  | |              [LARGE WORKSPACE]                  | |    |
|  | |                                                 | |    |
|  | +-------------------------------------------------+ |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [psychology icon] REFLECTION                                |
|  Explain your thinking on problem #___:                      |
|  _______________________________________________________    |
|  _______________________________________________________    |
|                                                              |
+-------------------------------------------------------------+
```

### Above Level Handout Structure

```
+-------------------------------------------------------------+
|  [PRIMARY COLOR BAR]                                         |
|  TITLE                                            Name: ___  |
|  -----------------------------------------------------------+
|  [target icon] GOAL: I can [i_can_statement - w/ extension]  |
+-------------------------------------------------------------+
|                                                              |
|  [book icon] VOCABULARY: term - definition | term - def      |
|              (may include advanced terms)                    |
|                                                              |
|  [person icon] PRACTICE                                      |
|  +-----------------------------------------------------+    |
|  | 1. [Complex, multi-step problem]                     |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  |                                                      |    |
|  | 2. [Complex problem]                                 |    |
|  |    +---------------------------------------------+   |    |
|  |    |           [WORKSPACE]                       |   |    |
|  |    +---------------------------------------------+   |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [trending_up icon] EXTENSION CHALLENGE                      |
|  +-----------------------------------------------------+    |
|  | [TITLE]                                              |    |
|  |                                                      |    |
|  | [Open-ended challenge description]                   |    |
|  |                                                      |    |
|  | Guiding Questions:                                   |    |
|  | - Question 1                                         |    |
|  | - Question 2                                         |    |
|  | - Question 3                                         |    |
|  |                                                      |    |
|  | +-------------------------------------------------+ |    |
|  | |                                                 | |    |
|  | |                                                 | |    |
|  | |              [LARGE WORKSPACE]                  | |    |
|  | |                                                 | |    |
|  | |                                                 | |    |
|  | +-------------------------------------------------+ |    |
|  +-----------------------------------------------------+    |
|                                                              |
|  [psychology icon] REFLECTION                                |
|  [Metacognitive or connection-making prompt]                 |
|  _______________________________________________________    |
|  _______________________________________________________    |
|  _______________________________________________________    |
|                                                              |
+-------------------------------------------------------------+
```

---

## Graphic Organizer Rendering

When `graphic_organizer` is present in the JSON, render based on `type`:

### ratio_table
```
+-----------------------------------------+
|           RATIO TABLE                   |
+----------+----------+----------+--------+
| Column1  | Column2  | Column1  | Column2|
+----------+----------+----------+--------+
| (prefill)| (prefill)|          |        |
+----------+----------+----------+--------+
|          |          |          |        |
+----------+----------+----------+--------+
|          |          |          |        |
+----------+----------+----------+--------+
```

### story_map
```
+-----------------------------------------+
|              STORY MAP                  |
+-----------------------------------------+
|  CHARACTERS    |    SETTING             |
|  ___________   |    ___________         |
|  ___________   |    ___________         |
+-----------------------------------------+
|  PROBLEM                                |
|  _____________________________________  |
+-----------------------------------------+
|  EVENTS                                 |
|  1. _________________________________   |
|  2. _________________________________   |
|  3. _________________________________   |
+-----------------------------------------+
|  SOLUTION                               |
|  _____________________________________  |
+-----------------------------------------+
```

### vocabulary_four_square
```
+------------------+----------------------+
|  WORD            |  DEFINITION          |
|  ____________    |  __________________  |
|                  |  __________________  |
+------------------+----------------------+
|  PICTURE         |  SENTENCE            |
|                  |  __________________  |
|  [drawing space] |  __________________  |
|                  |  __________________  |
+------------------+----------------------+
```

### cause_effect
```
+-----------------------------------------+
|          CAUSE AND EFFECT               |
+------------------+----------------------+
|      CAUSE       |       EFFECT         |
|  +------------+  |   +------------+     |
|  |            |--+-->|            |     |
|  +------------+  |   +------------+     |
|  +------------+  |   +------------+     |
|  |            |--+-->|            |     |
|  +------------+  |   +------------+     |
|  +------------+  |   +------------+     |
|  |            |--+-->|            |     |
|  +------------+  |   +------------+     |
+------------------+----------------------+
```

---

## Python Code Structure

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import json

# Parse input JSON
curriculum = json.loads('''{{CURRICULUM_JSON}}''')

# Define colors
COLORS = {
    "primary": HexColor("#2563EB"),
    "primary_light": HexColor("#DBEAFE"),
    "secondary": HexColor("#059669"),
    "warning": HexColor("#D97706"),
    "text_dark": HexColor("#1F2937"),
    "text_medium": HexColor("#6B7280"),
    "border": HexColor("#E5E7EB"),
    "background": HexColor("#F9FAFB"),
    "white": HexColor("#FFFFFF")
}

def create_teacher_guide(data, output_path):
    # Implementation for teacher guide PDF
    pass

def create_student_handout(data, level, output_path):
    # Implementation for student handout PDF
    # level = "below_level" | "approaching_level" | "at_level" | "above_level"
    pass

# Generate all PDFs
create_teacher_guide(
    curriculum["teacher_guide"], 
    "/mnt/user-data/outputs/teacher_guide.pdf"
)

for level in ["below_level", "approaching_level", "at_level", "above_level"]:
    create_student_handout(
        curriculum["student_materials"][level],
        level,
        f"/mnt/user-data/outputs/student_{level}.pdf"
    )

print("Generated 5 PDFs successfully.")
```

---

## Final Checklist

Before completing, verify:

- [ ] All 5 PDFs generated in `/mnt/user-data/outputs/`
- [ ] Teacher guide is 3-4 pages with all sections
- [ ] Each student handout fits on 1-2 pages (prefer 1 for shorter sessions)
- [ ] Workspace boxes are large enough to write in
- [ ] Font sizes are readable (minimum 10pt)
- [ ] Color contrast meets accessibility standards
- [ ] Page margins are consistent
- [ ] Headers clearly identify the document
- [ ] "Name: ___" line on all student handouts

Output the file paths when complete.
