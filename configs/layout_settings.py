from dataclasses import dataclass, field
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from configs.report_config import BASE_FONT


@dataclass
class LayoutConfig:
    """Base configuration for report layout."""

    # Page Layout
    PAGE_SIZE: tuple = letter
    MARGIN_LEFT: int = 72
    MARGIN_RIGHT: int = 72
    MARGIN_TOP: int = 72
    MARGIN_BOTTOM: int = 72

    # Section Header
    HEADER_HEIGHT: float = 1 * inch
    HEADER_BORDER_WIDTH: int = 2
    HEADER_CONTENT_GAP: int = 20
    HEADER_FONT_NAME: str = BASE_FONT
    HEADER_FONT_SIZE_LARGE: int = 20
    HEADER_FONT_SIZE_MEDIUM: int = 16
    HEADER_FONT_SIZE_SMALL: int = 12

    # Spacing
    SECTION_SPACER_HEIGHT: float = 0.15 * inch
    TABLE_SPACER_HEIGHT: float = 0.2 * inch

    # Footer
    FOOTER_LINE_Y_OFFSET: int = 12
    FOOTER_Y_POS: float = 0.4 * inch

    # Table Config (Defaults for 3-column)
    TABLE_COLUMNS: int = 3
    TABLE_COL_WIDTH: float = 2.35 * inch
    INNER_TABLE_COL_WIDTHS: List[float] = field(
        default_factory=lambda: [0.8 * inch, 1.3 * inch]
    )
    SVG_ICON_SIZE: float = 0.65 * inch


@dataclass
class ThreeColumnLayout(LayoutConfig):
    """Default 3-column layout."""

    pass


@dataclass
class SingleColumnLayout(LayoutConfig):
    """Single column layout with larger text and icons."""

    TABLE_COLUMNS: int = 1
    TABLE_COL_WIDTH: float = 7.0 * inch
    INNER_TABLE_COL_WIDTHS: List[float] = field(
        default_factory=lambda: [3.5 * inch, 3.5 * inch]
    )
    SVG_ICON_SIZE: float = 1.2 * inch
