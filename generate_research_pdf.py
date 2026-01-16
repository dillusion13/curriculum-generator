"""
Generate Pedagogical Approaches Research PDF
Uses the project's existing ReportLab styling for consistency.
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    ListFlowable,
    ListItem,
)

# Color palette matching project design
COLORS = {
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
    "paper": colors.HexColor("#fdfcfa"),
    "navy_700": colors.HexColor("#1e3a5f"),
    "navy_600": colors.HexColor("#2c4a6e"),
    "navy_500": colors.HexColor("#3d5a80"),
    "navy_100": colors.HexColor("#e8eef4"),
    "gold_600": colors.HexColor("#b8860b"),
    "gold_500": colors.HexColor("#d4a574"),
    "gold_100": colors.HexColor("#fdf6eb"),
    "teal_600": colors.HexColor("#0d9488"),
    "teal_100": colors.HexColor("#f0fdfa"),
    "purple_600": colors.HexColor("#7c3aed"),
    "purple_100": colors.HexColor("#f5f3ff"),
    "green_600": colors.HexColor("#16a34a"),
    "green_100": colors.HexColor("#f0fdf4"),
    "white": colors.white,
}

# Comprehensive pedagogical approaches data
APPROACHES = [
    {
        "name": "Project-Based Learning (PBL)",
        "definition": "A teaching method in which students learn by actively engaging in real-world and personally meaningful projects over an extended period (one week to a full semester). Students work to solve authentic problems and create public products or presentations for a real audience.",
        "key_elements": [
            "Real-world problems and authentic contexts",
            "Extended inquiry and investigation",
            "Student voice and choice in project direction",
            "Collaboration and teamwork",
            "Public presentation of final products",
            "Reflection on learning process"
        ],
        "benefits": [
            "Develops critical thinking, collaboration, creativity, and communication skills",
            "Improves academic achievement compared to traditional instruction",
            "Increases student engagement and motivation",
            "Prepares students for real-world problem-solving"
        ],
        "implementation": "Design projects around driving questions that connect to standards. Plan for 2-3 weeks minimum. Include checkpoints and scaffolding. End with public presentation.",
        "sources": ["PBLWorks (pblworks.org)", "Edutopia", "Springer Open Research"]
    },
    {
        "name": "Place-Based Learning",
        "definition": "A pedagogical approach that emphasizes the connection between learning and the physical place where teachers and students are located. Uses local heritage, cultures, landscapes, and experiences as foundations for studying core subjects.",
        "key_elements": [
            "Learning IN place (outdoor/community settings)",
            "Studying OF the place (local environment/history)",
            "Learning FROM the place (unique educational value)",
            "Learning FOR the place (championing positive change)",
            "Community partnerships and involvement"
        ],
        "benefits": [
            "Fosters sense of belonging and connection",
            "Increases student learning and persistence",
            "Narrows equity gaps",
            "Develops social skills and responsibility",
            "Makes learning relevant and meaningful"
        ],
        "implementation": "Partner with local organizations. Use local history, ecology, and culture as curriculum foundation. Include service-learning components. Take learning outside school walls.",
        "sources": ["Promise of Place", "National Geographic Education", "University of Nebraska"]
    },
    {
        "name": "Passion-Based Learning",
        "definition": "An approach that focuses on engaging students by allowing them to explore and learn about topics they are genuinely passionate about. Shifts from standardized curriculum to personalized, student-centered experiences where learners have significant control over their learning journey.",
        "key_elements": [
            "Student identification of personal interests",
            "Teacher as facilitator, not lecturer",
            "Passion Projects aligned with student interests",
            "Student autonomy and independence",
            "Connection of passions to curriculum standards"
        ],
        "benefits": [
            "Increases intrinsic motivation and engagement",
            "Promotes deeper understanding through personal investment",
            "Cultivates lifelong love of learning",
            "Develops sense of purpose",
            "Encourages creative problem-solving"
        ],
        "implementation": "Survey students about interests. Create time for passion exploration. Help students connect passions to learning objectives. Provide resources and mentorship.",
        "sources": ["Learnlife", "TeachThought", "Edutopia"]
    },
    {
        "name": "5E Lesson Model",
        "definition": "A research-based instructional model with five phases: Engage, Explore, Explain, Elaborate, and Evaluate. Provides a carefully planned sequence of instruction that places students at the center of learning, with teachers serving as facilitators.",
        "key_elements": [
            "ENGAGE: Assess prior knowledge, create curiosity",
            "EXPLORE: Hands-on investigation in teams",
            "EXPLAIN: Make sense of data, develop vocabulary",
            "ELABORATE: Apply understanding to new contexts",
            "EVALUATE: Assess learning throughout"
        ],
        "benefits": [
            "Significantly better acquisition of scientific concepts",
            "Student-centered learning approach",
            "Builds on prior knowledge systematically",
            "Promotes conceptual understanding over memorization",
            "Flexible for various subjects and grade levels"
        ],
        "implementation": "Plan 2-3 week units with each phase as distinct lessons. Never skip phases or change order. Can loop phases as needed. Best for STEM subjects but adaptable.",
        "sources": ["San Diego County Office of Education", "Houghton Mifflin Harcourt", "Lesley University"]
    },
    {
        "name": "3 Act Math Tasks",
        "definition": "A problem-solving structure developed by Dan Meyer that uses storytelling to engage students in mathematics. Presents problems in three acts: conflict introduction, information gathering, and resolution reveal. Low floor, high ceiling tasks accessible to all learners.",
        "key_elements": [
            "ACT 1: Visual/visceral hook with minimal words",
            "ACT 2: Students request and gather information",
            "ACT 3: Real-world answer revealed via multimedia",
            "Withholding information to build curiosity",
            "Estimation before calculation",
            "Optional sequel for extension"
        ],
        "benefits": [
            "Develops estimation and number sense",
            "Builds mathematical reasoning skills",
            "Increases engagement through storytelling",
            "Accessible entry point for all students",
            "Connects math to real-world contexts"
        ],
        "implementation": "Find or create compelling visual hooks. Remove typical problem information. Let students ask for what they need. Reveal actual answer at end. Extend with sequel problems.",
        "sources": ["Dan Meyer (blog.mrmeyer.com)", "Tap Into Teen Minds", "When Math Happens"]
    },
    {
        "name": "Design-Based Thinking Lessons",
        "definition": "A five-step creative problem-solving process adapted from design schools: Empathize, Define, Ideate, Prototype, and Test. Cultivates 21st century skills and enables student-centered, constructivist learning focused on real problems.",
        "key_elements": [
            "EMPATHIZE: Understand user needs through research",
            "DEFINE: Clearly articulate the problem",
            "IDEATE: Brainstorm multiple solutions",
            "PROTOTYPE: Create quick, testable models",
            "TEST: Get feedback and iterate"
        ],
        "benefits": [
            "Develops creative confidence",
            "Builds collaboration and communication skills",
            "Teaches iteration and resilience",
            "Applicable across all disciplines",
            "Prepares students for innovation economy"
        ],
        "implementation": "Use the LAUNCH Cycle for K-12 adaptation. Start with empathy maps. Provide prototyping materials. Allow for failure and iteration. Can use literature characters as starting points.",
        "sources": ["Stanford d.school", "Common Sense Education", "Getting Smart"]
    },
    {
        "name": "Peer Teaching",
        "definition": "An instructional strategy where students teach and learn from each other. Based on research showing that the brain boost from teaching arises from both the expectation and act of teaching. Includes strategies like Jigsaw, Think-Pair-Share, and peer discussion.",
        "key_elements": [
            "Students explaining concepts to peers",
            "Jigsaw Groups: Each student becomes an expert",
            "Think-Pair-Share: Brief collaborative processing",
            "Three Before Me: Ask peers before teacher",
            "Process gains from group interaction"
        ],
        "benefits": [
            "Improves conceptual understanding",
            "Reduces student attrition in difficult courses",
            "Decreases failure rates",
            "Boosts retention through teaching",
            "Develops communication skills"
        ],
        "implementation": "Structure opportunities for peer explanation. Train students in effective peer teaching. Use during concept review or problem-solving. Combine with individual accountability.",
        "sources": ["Edutopia", "Harvard Instructional Moves", "NIH/PMC Research"]
    },
    {
        "name": "Cross-Age Peer Teaching",
        "definition": "A tutoring approach that pairs students of different ages, with older students (typically 2-3 years older) assuming the role of tutor for younger students. Benefits both tutors and tutees through social constructivist learning.",
        "key_elements": [
            "Older students tutoring younger students",
            "Optimal age gap of 2-3 years",
            "Training for tutors before implementation",
            "Structured tutoring protocols",
            "Regular sessions with consistent pairings"
        ],
        "benefits": [
            "Positive academic outcomes for both tutors and tutees",
            "Tutors gain through self-explanation (making learning explicit)",
            "Tutees more comfortable asking questions",
            "Develops social skills and relationships",
            "Builds leadership and responsibility in tutors"
        ],
        "implementation": "Match students by ability levels. Train tutors on content and teaching strategies. Schedule regular sessions. Monitor and provide feedback. Address scheduling conflicts proactively.",
        "sources": ["Education Northwest", "Springer Meta-Analysis", "Reading Rockets"]
    },
    {
        "name": "Inquiry-Based Learning Models",
        "definition": "Active learning that starts by posing questions, problems, or scenarios rather than presenting facts. Grounded in constructivism, with students directing their own learning through investigation. Includes confirmation, structured, guided, and open inquiry types.",
        "key_elements": [
            "CONFIRMATION: Known results, practice investigation",
            "STRUCTURED: Instructor provides problem and procedure",
            "GUIDED: Instructor provides problem, students choose method",
            "OPEN: Students choose both problem and method",
            "Teacher as facilitator and guide"
        ],
        "benefits": [
            "Improves critical thinking and problem-solving",
            "Increases creativity and self-efficacy",
            "Students more willing to take risks",
            "Higher conflict resolution rates",
            "Develops independent learning skills"
        ],
        "implementation": "Start with structured inquiry for novices. Gradually release responsibility. Provide resources and support. Allow for productive struggle. Celebrate multiple solution paths.",
        "sources": ["Wikipedia", "SplashLearn", "Queens University CTL"]
    },
    {
        "name": "Flipped Learning Lessons",
        "definition": "A pedagogical approach where direct instruction moves from group space to individual space (typically via pre-recorded videos), freeing class time for active learning, problem-solving, and deeper discussion. Students encounter content before class.",
        "key_elements": [
            "Pre-class content delivery (videos, readings)",
            "Class time for active learning and application",
            "Teacher as facilitator during class",
            "Higher-order thinking activities in person",
            "Student responsibility for initial learning"
        ],
        "benefits": [
            "67% of instructors report improved test scores",
            "Students learn more deeply",
            "Active participation replaces passive reception",
            "More time for personalized support",
            "Students can pace their initial learning"
        ],
        "implementation": "Create or curate short video content (10-15 min). Include accountability checks for pre-class work. Design active learning activities for class. Provide support for students who struggle with format.",
        "sources": ["Harvard Bok Center", "Stanford Teaching Commons", "Flipped Learning Network"]
    },
    {
        "name": "Genius Hour",
        "definition": "A movement allowing students to explore their own passions and creativity during a dedicated portion of school time. Based on Google's '20% time' policy. Students pursue passion projects of their choosing, developing ownership of their learning.",
        "key_elements": [
            "Dedicated time for passion projects (typically 20%)",
            "Student choice in project topics",
            "Project proposals with goals and objectives",
            "Regular check-ins and reflection",
            "Final presentation to class or community"
        ],
        "benefits": [
            "Fosters intrinsic motivation",
            "Gives students voice and choice",
            "Develops self-directed learning skills",
            "Creates electric, engaged classroom environment",
            "Produces authentic, meaningful work"
        ],
        "implementation": "Set aside regular time (one hour weekly or similar). Guide students through topic selection. Create proposal template. Schedule check-ins. Plan culminating sharing event.",
        "sources": ["Kesler Science", "Edutopia", "NY State Education Dept"]
    },
    {
        "name": "Makerspace",
        "definition": "Collaborative spaces where students create, tinker, invent, and learn by making. Based on constructionism philosophy that learning is a highly personal endeavor requiring students to build something tangible. Can range from low-tech to high-tech materials.",
        "key_elements": [
            "Hands-on creation and experimentation",
            "Wide range of materials (paper to 3D printers)",
            "Student-driven projects and exploration",
            "Failure as part of learning process",
            "Cross-curricular connections"
        ],
        "benefits": [
            "Fosters innovation through experimentation",
            "Develops critical thinking and problem-solving",
            "Promotes educational equity",
            "Builds 21st century skills",
            "Engages diverse learners"
        ],
        "implementation": "Start with available materials (craft supplies, cardboard). Designate flexible space. Introduce design challenges. Allow open exploration time. Connect making to curriculum standards.",
        "sources": ["Makerspaces.com", "Let's Talk Science", "CREATE Education"]
    },
    {
        "name": "Gamification-Based Learning",
        "definition": "The application of game elements (points, badges, leaderboards, challenges) to non-game educational contexts. Focuses on adding game mechanics to existing learning activities rather than creating full games. Harnesses principles that make games engaging.",
        "key_elements": [
            "Points, badges, and rewards systems",
            "Leaderboards and competition",
            "Levels and progression tracking",
            "Challenges, quests, and missions",
            "Immediate feedback loops"
        ],
        "benefits": [
            "12-19% improvement in student performance",
            "Increased engagement and motivation",
            "Natural collaboration through team challenges",
            "Aids cognitive and physical development",
            "Makes learning feel like play"
        ],
        "implementation": "Start small with one gamified element. Use tools like Kahoot!, ClassDojo, Quizizz. Match elements to student interests. Align with learning outcomes. Balance competition with collaboration.",
        "sources": ["University of Waterloo", "Discovery Education", "Kodable"]
    },
    {
        "name": "Action Civics",
        "definition": "An approach where students learn civics by doing civics. Students identify personally relevant community issues, collect and analyze information, and plan and take collective action. Encompasses community service, electoral engagement, and public advocacy.",
        "key_elements": [
            "Student identification of community issues",
            "Research and data collection",
            "Action planning and implementation",
            "Engagement with public officials",
            "Reflection on civic participation"
        ],
        "benefits": [
            "Increases future political participation",
            "Improves college graduation odds",
            "Addresses civic engagement equity gaps",
            "Develops deeper understanding of democracy",
            "Builds empowerment and agency"
        ],
        "implementation": "Guide issue identification process. Teach research skills. Connect with community organizations. Support student-led action. Reflect on impact and process.",
        "sources": ["USC Rossier School of Education", "Teaching for Democracy Alliance", "Generation Citizen"]
    },
    {
        "name": "Role Play Scenarios/Lessons",
        "definition": "An experiential learning strategy where students assume different characters and act out scenarios, typically without scripts. Allows students to take on unfamiliar roles, use creativity and critical thinking, and practice real-world situations in a safe environment.",
        "key_elements": [
            "Character assumption and persona development",
            "Scenario creation (historical, contemporary, fictional)",
            "Improvisation without scripts",
            "Debriefing and reflection",
            "Safe space for experimentation"
        ],
        "benefits": [
            "Higher satisfaction and retention than lectures",
            "Develops empathy and perspective-taking",
            "Improves communication and speaking skills",
            "Builds critical thinking through immersion",
            "Makes abstract concepts concrete"
        ],
        "implementation": "Create scenarios matching learning objectives. Set clear parameters and expectations. Model first if needed. Allow for student creativity. Include structured debriefing.",
        "sources": ["Northern Illinois University CITL", "Teachfloor", "University of San Diego"]
    },
    {
        "name": "Socratic Seminar",
        "definition": "A formal discussion based on a text, in which a facilitator asks open-ended questions to stimulate critical thinking and illuminate ideas. Named after Socrates' questioning method. Students lead discussion while teacher facilitates.",
        "key_elements": [
            "Anchor text (primary source, article, etc.)",
            "Open-ended questions without single correct answers",
            "Inner/outer circle or fishbowl structure",
            "Student-led discussion with teacher facilitation",
            "Active listening and thoughtful response"
        ],
        "benefits": [
            "Develops critical thinking and analysis skills",
            "Builds civic skills: empathy, tolerance, perspective-taking",
            "Gives students ownership of learning",
            "Promotes deeper text understanding",
            "Develops public speaking and listening skills"
        ],
        "implementation": "Select ambiguous, compelling texts. Prepare opening, follow-up, and closing questions. Teach discussion norms. Use fishbowl for observation. Debrief on content and process.",
        "sources": ["Facing History & Ourselves", "ReadWriteThink", "Colorado State University"]
    },
    {
        "name": "4C Lessons",
        "definition": "A framework for 21st century learning focusing on four essential skills: Critical Thinking, Creativity, Collaboration, and Communication. Originated from the Partnership for 21st Century Learning (P21) as foundational skills for innovation and success.",
        "key_elements": [
            "CRITICAL THINKING: Analyze, evaluate, synthesize information",
            "CREATIVITY: Think uniquely, solve problems innovatively",
            "COLLABORATION: Work together toward common goals",
            "COMMUNICATION: Efficiently convey ideas",
            "Integration across all subjects"
        ],
        "benefits": [
            "Prepares students for workforce demands",
            "Improves academic success",
            "Develops transferable life skills",
            "Creates discerning, capable problem-solvers",
            "Enables profound community impact"
        ],
        "implementation": "Explicitly teach and assess each skill. Integrate across curriculum. Use technology to support skill development. Design activities requiring multiple Cs. Model skills in teaching.",
        "sources": ["Partnership for 21st Century Learning", "Nearpod", "iCEV Online"]
    },
    {
        "name": "Readers Theatre",
        "definition": "An interpretive performance of dramatic text, typically done without costumes, props, or memorization. Students read aloud from scripts, focusing on oral expression and fluency rather than theatrical production. Combines drama with reading instruction.",
        "key_elements": [
            "Script reading without memorization",
            "Focus on expression and prosody",
            "No costumes or elaborate staging",
            "Repeated reading for fluency development",
            "Performance as authentic purpose for practice"
        ],
        "benefits": [
            "Large effect size on reading skills (meta-analysis)",
            "Improves fluency: accuracy, automaticity, prosody",
            "Engages reluctant readers",
            "Builds confidence in public speaking",
            "Teaches drama elements and vocabulary"
        ],
        "implementation": "Select or adapt scripts matching reading levels. Model expressive reading. Schedule rehearsal time. Plan culminating performance. Can create scripts from existing texts.",
        "sources": ["Reading Rockets", "Iowa Reading Research Center", "ReadWriteThink"]
    },
    {
        "name": "Culturally and Historically Responsive Literacy",
        "definition": "A four-part equity framework developed by Dr. Gholdy Muhammad focusing on Identity, Skills, Intellect, and Criticality. Derived from studying 19th century Black literary societies. Designed to teach the whole child and advance educational achievement for all students, particularly students of color.",
        "key_elements": [
            "IDENTITY: Help students make sense of self and others",
            "SKILLS: Develop proficiencies across disciplines",
            "INTELLECT: Gain knowledge and become smarter",
            "CRITICALITY: Understand power, equity, anti-oppression",
            "Culturally affirming texts and practices"
        ],
        "benefits": [
            "Advances achievement for underserved students",
            "Validates and affirms student identities",
            "Develops sociopolitical consciousness",
            "Empowers students as agents of change",
            "Creates student-centered learning environments"
        ],
        "implementation": "Select culturally and historically responsive texts. Plan for all four pursuits in each unit. Center student identities. Include critical analysis of power. Connect to community knowledge.",
        "sources": ["Cult of Pedagogy", "Dr. Gholdy Muhammad - Cultivating Genius", "NCTE"]
    },
    {
        "name": "Unboxing Video",
        "definition": "An educational activity where students create videos revealing items that represent concepts, stories, or problem-solving processes. Leverages students' familiarity with popular YouTube unboxing format to make learning engaging and multimedia-based.",
        "key_elements": [
            "Video creation by students or teachers",
            "Items representing learning concepts",
            "Reveal and explanation process",
            "Connection to books, lessons, or units",
            "Authentic multimedia production"
        ],
        "benefits": [
            "Highly engaging format familiar to students",
            "Develops multimedia literacy skills",
            "Encourages creative representation of knowledge",
            "Can serve as previews or summaries",
            "Motivates deep thinking about content"
        ],
        "implementation": "Introduce format with examples. Allow student choice of items. Connect to learning objectives. Can be book trailers, lesson previews, or math problem reveals. Simple recording setup works fine.",
        "sources": ["Ditch That Textbook", "Create Dream Explore"]
    }
]


def get_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=COLORS["navy_700"],
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=28
    ))

    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica",
        fontSize=12,
        textColor=COLORS["ink_600"],
        alignment=TA_CENTER,
        spaceAfter=24
    ))

    styles.add(ParagraphStyle(
        name="ApproachTitle",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=COLORS["navy_700"],
        spaceBefore=0,
        spaceAfter=8,
        leading=18
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=COLORS["gold_600"],
        spaceBefore=10,
        spaceAfter=4
    ))

    # Override existing BodyText style
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].textColor = COLORS["ink_700"]
    styles["BodyText"].alignment = TA_JUSTIFY
    styles["BodyText"].spaceAfter = 6
    styles["BodyText"].leading = 14

    styles.add(ParagraphStyle(
        name="BulletItem",
        fontName="Helvetica",
        fontSize=9,
        textColor=COLORS["ink_700"],
        leftIndent=16,
        firstLineIndent=-12,
        spaceBefore=2,
        spaceAfter=2,
        leading=12
    ))

    styles.add(ParagraphStyle(
        name="SourceText",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=COLORS["ink_500"],
        spaceBefore=6,
        spaceAfter=0
    ))

    styles.add(ParagraphStyle(
        name="TOCItem",
        fontName="Helvetica",
        fontSize=10,
        textColor=COLORS["ink_700"],
        leftIndent=0,
        spaceBefore=4,
        spaceAfter=4
    ))

    return styles


def create_approach_section(approach: dict, number: int, styles) -> list:
    """Create elements for a single approach section."""
    elements = []

    # Approach header with number
    header_table = Table([[
        Paragraph(f"<font color='#{COLORS['gold_600'].hexval()[2:]}' size='18'>{number}</font>",
                  ParagraphStyle(name="num", fontSize=18, alignment=TA_CENTER)),
        Paragraph(approach["name"], styles["ApproachTitle"])
    ]], colWidths=[0.5*inch, 7*inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["navy_100"]),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (0, 0), (0, -1), 4, COLORS["navy_700"]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # Definition
    elements.append(Paragraph("<b>Definition</b>", styles["SectionHeader"]))
    elements.append(Paragraph(approach["definition"], styles["BodyText"]))

    # Key Elements
    elements.append(Paragraph("<b>Key Elements</b>", styles["SectionHeader"]))
    for item in approach["key_elements"]:
        elements.append(Paragraph(f"<font color='#{COLORS['navy_600'].hexval()[2:]}'>\u2022</font>  {item}", styles["BulletItem"]))

    # Benefits
    elements.append(Paragraph("<b>Benefits for Students</b>", styles["SectionHeader"]))
    for item in approach["benefits"]:
        elements.append(Paragraph(f"<font color='#{COLORS['green_600'].hexval()[2:]}'>\u2713</font>  {item}", styles["BulletItem"]))

    # Implementation
    elements.append(Paragraph("<b>Implementation Strategies</b>", styles["SectionHeader"]))
    impl_box = Table([[
        Paragraph(approach["implementation"], styles["BodyText"])
    ]], colWidths=[7.5*inch])
    impl_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["gold_100"]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, COLORS["gold_600"]),
    ]))
    elements.append(impl_box)

    # Sources
    sources_text = " | ".join(approach["sources"])
    elements.append(Paragraph(f"<b>Sources:</b> {sources_text}", styles["SourceText"]))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLORS["ink_200"], spaceBefore=0, spaceAfter=16))

    return elements


def create_pdf(output_path: str):
    """Generate the complete research PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.6*inch,
        bottomMargin=0.5*inch,
    )

    styles = get_styles()
    elements = []

    # ===== TITLE PAGE =====
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Pedagogical Approaches", styles["DocTitle"]))
    elements.append(Paragraph("for K-12 Curriculum Development", styles["DocTitle"]))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(HRFlowable(width="60%", thickness=3, color=COLORS["gold_600"], spaceBefore=0, spaceAfter=16))
    elements.append(Paragraph("A Comprehensive Research Summary of 20 Teaching Methodologies", styles["DocSubtitle"]))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Prepared for Curriculum Generator Integration", styles["DocSubtitle"]))
    elements.append(Paragraph("January 2026", styles["DocSubtitle"]))
    elements.append(PageBreak())

    # ===== TABLE OF CONTENTS =====
    elements.append(Paragraph("Table of Contents", styles["DocTitle"]))
    elements.append(Spacer(1, 0.3*inch))

    for i, approach in enumerate(APPROACHES, 1):
        toc_entry = Table([[
            Paragraph(f"<b>{i}.</b>", ParagraphStyle(name="tocnum", fontSize=10, textColor=COLORS["gold_600"])),
            Paragraph(approach["name"], styles["TOCItem"])
        ]], colWidths=[0.4*inch, 7.1*inch])
        toc_entry.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(toc_entry)

    elements.append(PageBreak())

    # ===== INTRODUCTION =====
    elements.append(Paragraph("Introduction", styles["ApproachTitle"]))
    elements.append(Spacer(1, 8))
    intro_text = """This document presents a comprehensive overview of 20 pedagogical approaches for K-12 education. Each methodology has been researched to include its definition, key elements, benefits for students, implementation strategies, and authoritative sources. These approaches represent a spectrum of student-centered, inquiry-based, and experiential learning methods that can be integrated into curriculum design and lesson planning."""
    elements.append(Paragraph(intro_text, styles["BodyText"]))
    elements.append(Spacer(1, 8))

    categories_text = """The approaches are organized to cover diverse teaching needs including project-based and inquiry learning, peer instruction models, technology-enhanced learning, civic and culturally responsive education, and creative expression methods. Each can be adapted for various grade levels, subjects, and student populations."""
    elements.append(Paragraph(categories_text, styles["BodyText"]))

    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLORS["navy_700"], spaceBefore=0, spaceAfter=24))

    # ===== APPROACH SECTIONS =====
    for i, approach in enumerate(APPROACHES, 1):
        # Page break every 2 approaches for readability
        if i > 1 and (i - 1) % 2 == 0:
            elements.append(PageBreak())

        elements.extend(create_approach_section(approach, i, styles))

    # Build PDF
    doc.build(elements)
    print(f"PDF created: {output_path}")
    return output_path


if __name__ == "__main__":
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "pedagogical_approaches_research.pdf"
    create_pdf(str(output_file))
