"""PDF Generator script for LevelUp Master Instructions & Controls Guide."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def create_pdf(filename: str = "LevelUp_Master_Guide.pdf") -> str:
    """Generate a PDF document of the LevelUp Master Instructions Guide.

    Args:
        filename: Target PDF file name.

    Returns:
        Path string to created PDF file.
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []

    # Palette
    c_bg = colors.HexColor("#1A0B2E")
    c_cyan = colors.HexColor("#00E5FF")
    c_gold = colors.HexColor("#FFD700")
    c_green = colors.HexColor("#00FF9D")
    c_white = colors.HexColor("#FFFFFF")
    c_muted = colors.HexColor("#8C9BB4")
    c_dark_panel = colors.HexColor("#110620")
    c_blue = colors.HexColor("#0055FF")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_cyan,
        alignment=0,
    )

    sub_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_gold,
    )

    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=c_cyan,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=c_white,
    )

    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=c_gold,
    )

    cell_text = ParagraphStyle(
        "CellText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=c_white,
    )

    # Header Banner
    story.append(Paragraph("LEVELUP — SOLO LEVELING SYSTEM HUD", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("MASTER INSTRUCTIONS & CONTROLS MANUAL", sub_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=c_cyan, spaceAfter=12))

    # Section 1: How to Launch
    story.append(Paragraph("1. Launch & Platform Options", h2_style))
    launch_data = [
        [
            Paragraph("Platform", cell_bold),
            Paragraph("Launch Method", cell_bold),
        ],
        [
            Paragraph("Standalone Desktop App (.exe)", cell_text),
            Paragraph("Open <b>dist/LevelUp/</b> and double-click <b>LevelUp.exe</b>", cell_text),
        ],
        [
            Paragraph("Live Web App (Phone & PC)", cell_text),
            Paragraph("Open <b>https://zareen333.github.io/levelup-system-hud/</b>", cell_text),
        ],
        [
            Paragraph("Local Web File", cell_text),
            Paragraph("Double-click <b>web_app/index.html</b> in File Explorer", cell_text),
        ],
        [
            Paragraph("Python Terminal", cell_text),
            Paragraph("Run <b>python main.py</b> inside system_ar_glasses/", cell_text),
        ],
    ]
    t1 = Table(launch_data, colWidths=[160, 380])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_dark_panel),
                ("GRID", (0, 0), (-1, -1), 0.5, c_blue),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 10))

    # Section 2: Voice Commands
    story.append(Paragraph("2. Voice Commands (Microphone Input)", h2_style))
    voice_data = [
        [
            Paragraph("Action Intent", cell_bold),
            Paragraph("Phrases You Can Speak", cell_bold),
            Paragraph("System Action Result", cell_bold),
        ],
        [
            Paragraph("Add New Quest", cell_text),
            Paragraph('<b>"Add quest [Title]"</b><br/><i>"New quest Run 5KM"</i>', cell_text),
            Paragraph("Creates new quest with title & +50 XP", cell_text),
        ],
        [
            Paragraph("Complete by Number", cell_text),
            Paragraph('<b>"Complete quest 1"</b><br/><i>"Finish 2"</i>', cell_text),
            Paragraph("Completes quest #1, #2, etc., awards XP", cell_text),
        ],
        [
            Paragraph("Complete by Name", cell_text),
            Paragraph('<b>"Complete pushups"</b><br/><i>"Finish study"</i>', cell_text),
            Paragraph("Finds and completes matching title", cell_text),
        ],
        [
            Paragraph("Level Up", cell_text),
            Paragraph('<b>"System level up"</b><br/><i>"Upgrade level"</i>', cell_text),
            Paragraph("Triggers level up & grants +3 stat points", cell_text),
        ],
        [
            Paragraph("AR Camera Mode", cell_text),
            Paragraph('<b>"AR mode"</b><br/><i>"Camera"</i>', cell_text),
            Paragraph("Toggles live camera AR glasses overlay", cell_text),
        ],
        [
            Paragraph("Switch Viewport", cell_text),
            Paragraph('<b>"Switch view"</b><br/><i>"Mobile view"</i>', cell_text),
            Paragraph("Toggles Mobile (440px) & Desktop (1000px)", cell_text),
        ],
    ]
    t2 = Table(voice_data, colWidths=[120, 220, 200])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_dark_panel),
                ("GRID", (0, 0), (-1, -1), 0.5, c_blue),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 10))

    # Section 3: Text Console
    story.append(Paragraph("3. Text Console Commands", h2_style))
    console_data = [
        [
            Paragraph("Typed Command Syntax", cell_bold),
            Paragraph("Example Input", cell_bold),
            Paragraph("Function Result", cell_bold),
        ],
        [
            Paragraph("/complete &lt;num / title&gt;", cell_text),
            Paragraph("<b>/complete 1</b><br/><b>/complete pushups</b>", cell_text),
            Paragraph("Completes quest by 1-based index or keyword", cell_text),
        ],
        [
            Paragraph("/addquest &lt;title&gt; | &lt;xp&gt; | &lt;cat&gt;", cell_text),
            Paragraph("<b>/addquest Read 20 Pages | 80 | Intellect</b>", cell_text),
            Paragraph("Adds custom quest with XP & category", cell_text),
        ],
        [
            Paragraph("/levelup", cell_text),
            Paragraph("<b>/levelup</b>", cell_text),
            Paragraph("Grants required XP for level increase", cell_text),
        ],
        [
            Paragraph("/mode", cell_text),
            Paragraph("<b>/mode</b>", cell_text),
            Paragraph("Toggles Desktop & Mobile viewport layouts", cell_text),
        ],
        [
            Paragraph("/camera", cell_text),
            Paragraph("<b>/camera</b>", cell_text),
            Paragraph("Toggles WebRTC live camera background stream", cell_text),
        ],
    ]
    t3 = Table(console_data, colWidths=[150, 210, 180])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_dark_panel),
                ("GRID", (0, 0), (-1, -1), 0.5, c_blue),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 10))

    # Section 4: Touch & Shortcuts
    story.append(Paragraph("4. Touch Controls & Keyboard Shortcuts", h2_style))
    controls_data = [
        [
            Paragraph("Interaction", cell_bold),
            Paragraph("Control Target", cell_bold),
            Paragraph("Action", cell_bold),
        ],
        [
            Paragraph("Direct Tap / Click", cell_text),
            Paragraph("Quest Card", cell_text),
            Paragraph("Completes clicked quest card instantly", cell_text),
        ],
        [
            Paragraph("Direct Tap / Click", cell_text),
            Paragraph("<b>[ 👓 AR CAMERA ]</b>", cell_text),
            Paragraph("Toggles live video stream for smart glasses testing", cell_text),
        ],
        [
            Paragraph("Direct Tap / Click", cell_text),
            Paragraph("<b>[ 🔄 FLIP CAM ]</b>", cell_text),
            Paragraph("Flips between rear environment and front camera", cell_text),
        ],
        [
            Paragraph("Direct Tap / Click", cell_text),
            Paragraph("<b>[ + ADD QUEST ]</b>", cell_text),
            Paragraph("Opens interactive Quest Creation Form modal", cell_text),
        ],
        [
            Paragraph("Shortcut Keys", cell_text),
            Paragraph("<b>1 - 9</b>", cell_text),
            Paragraph("Completes Quest #1 through #9", cell_text),
        ],
        [
            Paragraph("Shortcut Keys", cell_text),
            Paragraph("<b>L / M / C</b>", cell_text),
            Paragraph("<b>L</b>: Level Up  |  <b>M</b>: View Mode  |  <b>C</b>: AR Camera", cell_text),
        ],
    ]
    t4 = Table(controls_data, colWidths=[120, 180, 240])
    t4.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), c_dark_panel),
                ("GRID", (0, 0), (-1, -1), 0.5, c_blue),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t4)
    story.append(Spacer(1, 14))

    # Page background color
    def draw_bg(canvas, doc_obj):
        canvas.saveState()
        canvas.setFillColor(c_bg)
        canvas.rect(0, 0, doc_obj.pagesize[0], doc_obj.pagesize[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)
    return os.path.abspath(filename)


if __name__ == "__main__":
    pdf_path = create_pdf()
    print("PDF generated successfully:", pdf_path)
