from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import TableStyle

from configs import report_config as config


def get_report_styles():
    """Returns a dictionary of custom ReportLab styles using the base font."""
    styles = getSampleStyleSheet()
    font_name = config.BASE_FONT

    detail_style = ParagraphStyle(
        "Detail",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=12,
        spaceAfter=1,
        alignment=1,  # Center
    )

    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8,
        leading=9,
        textColor=colors.black,
        alignment=1,  # Center
    )

    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=14,
        alignment=1,  # Center
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8,
        textColor=colors.black,
    )

    return {
        "detail": detail_style,
        "meta": meta_style,
        "header": header_style,
        "footer": footer_style,
    }


def get_table_styles():
    """Returns dictionary of TableStyles."""

    # Inner Cell Table Style (Symbol | Text)
    inner_cell_style = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.black),
            ("LEFTPADDING", (1, 0), (1, -1), 8),
            ("LEFTPADDING", (0, 0), (0, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    # Main Grid Table Style
    main_grid_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )

    return {"inner_cell": inner_cell_style, "main_grid": main_grid_style}


def get_header_internal_style(font_name, font_size):
    """Creates a dynamic style for the section header text."""
    return ParagraphStyle(
        "HeaderInternal",
        fontName=font_name,
        fontSize=font_size,
        leading=font_size * 1.2,
        alignment=0,  # Left Align
    )
