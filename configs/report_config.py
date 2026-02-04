import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Paths
SVG_FOLDER = os.path.join("svg-symbols", "svg-symbols")

# Font
BASE_FONT = "Arial"

# Page Layout
PAGE_SIZE = letter
MARGIN_LEFT = 72
MARGIN_RIGHT = 72
MARGIN_TOP = 72
MARGIN_BOTTOM = 72

# Section Header
HEADER_HEIGHT = 1 * inch
HEADER_BORDER_WIDTH = 2
HEADER_CONTENT_GAP = 20
HEADER_FONT_NAME = "Arial"
HEADER_FONT_SIZE_LARGE = 20
HEADER_FONT_SIZE_MEDIUM = 16
HEADER_FONT_SIZE_SMALL = 12

# Table Config
TABLE_COLUMNS = 3
TABLE_COL_WIDTH = 2.35 * inch
INNER_TABLE_COL_WIDTHS = [0.8 * inch, 1.3 * inch]
SVG_ICON_SIZE = 0.65 * inch

# Spacing
SECTION_SPACER_HEIGHT = 0.15 * inch
TABLE_SPACER_HEIGHT = 0.2 * inch

# Footer
FOOTER_LINE_Y_OFFSET = 12
FOOTER_Y_POS = 0.4 * inch
