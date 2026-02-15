from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import TableStyle


styles = getSampleStyleSheet()

instruction_title_style = ParagraphStyle(
    "InstructionTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=16,
    alignment=1,  # center
    spaceAfter=18
)

instruction_body_style = ParagraphStyle(
    "InstructionBody",
    parent=styles["Normal"],
    fontSize=11,
    leading=14,
    spaceAfter=10
)

instruction_list_style = ParagraphStyle(
    "InstructionList",
    parent=styles["Normal"],
    fontSize=11,
    leftIndent=18,
    leading=14,
    spaceAfter=6
)
detail_style = ParagraphStyle(
    "Detail",
    parent=styles["Normal"],
    fontSize=9,
    spaceAfter=2
)

appendix_style = ParagraphStyle(
    "Detail",
    parent=styles["Normal"],
    fontSize=7,
    spaceAfter=2
)

def table_style(table, grid_color=colors.grey, bg_color=colors.lightgrey, x=(0,0), y=(-1,-1), padding=(4,4,2,1)):
    return table.setStyle(TableStyle([
                    ("GRID", x, y, 0.5, grid_color),
                    ("VALIGN", x, y, "MIDDLE"),
                    ("ALIGN", x, y, "CENTER"),
                    ("LEFTPADDING", x, y, padding[0]),
                    ("RIGHTPADDING", x, y, padding[1]),
                    ("TOPPADDING", x, y, padding[2]),
                    ("BOTTOMPADDING",x, y, padding[3]),
                    ("BACKGROUND", (0,0), (-1,0), bg_color),
                ]))
