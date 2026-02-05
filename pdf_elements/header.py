from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph,
)
from reportlab.platypus.flowables import Flowable

from configs import report_config as config
from configs import report_styles
from utils import load_and_scale_svg


class SectionHeader(Flowable):
    """Flowable to display an SVG symbol and section title side-by-side, centered in a box."""

    def __init__(self, svg_filename, text, width=None, height=config.HEADER_HEIGHT):
        super().__init__()
        self.text = text
        self.height = height
        self.width = (
            width
            if width
            else config.PAGE_SIZE[0] - (config.MARGIN_LEFT + config.MARGIN_RIGHT)
        )

        # Load SVG
        self.drawing = load_and_scale_svg(svg_filename, height * 2, height * 0.8)

    def wrap(self, aW, aH):
        """
        Specifies the size of this flowable.
        It claims the full available width (aW) and its fixed height.
        """
        self.width = aW
        return aW, self.height

    def _draw_border(self):
        """Draws a rectangle around the header."""
        self.canv.setStrokeColor(colors.black)
        self.canv.setLineWidth(config.HEADER_BORDER_WIDTH)
        self.canv.rect(0, 0, self.width, self.height)

    def _get_drawing_width(self):
        return self.drawing.width if self.drawing else 0

    def _get_font_size(self):
        """Adjusts font size based on text length."""
        font_size = config.HEADER_FONT_SIZE_LARGE
        if len(self.text) > 20:
            font_size = config.HEADER_FONT_SIZE_MEDIUM
        if len(self.text) > 40:
            font_size = config.HEADER_FONT_SIZE_SMALL
        return font_size

    def _prepare_text_layout(self, font_size, avail_width):
        """
        Determines if text needs to be wrapped or drawn directly.

        Logic:
        1. Measures text width at the given font size.
        2. If it fits, returns metadata for simple string drawing.
        3. If it overflows, creates a Paragraph object to handle line wrapping.

        Returns: (paragraph_obj_or_none, width, height)
        """
        font_name = config.HEADER_FONT_NAME
        text_width = self.canv.stringWidth(self.text.upper(), font_name, font_size)

        if text_width > avail_width:
            # Create Paragraph to handle wrapping
            header_text_style = report_styles.get_header_internal_style(
                font_name, font_size
            )
            p = Paragraph(self.text.upper(), header_text_style)
            p_width, p_height = p.wrap(avail_width, self.height - 10)
            return p, p_width, p_height
        else:
            return None, text_width, font_size

    def _draw_symbol(self, x, y_center):
        if self.drawing:
            d_height = self.drawing.height
            sym_y = y_center - (d_height / 2)
            renderPDF.draw(self.drawing, self.canv, x, sym_y)

    def _draw_text_element(self, x, y_center, text_obj, height, font_size):
        if text_obj:
            # Draw Paragraph
            text_y = y_center - (height / 2)
            text_obj.drawOn(self.canv, x, text_y)
        else:
            # Draw String directly
            font_name = config.HEADER_FONT_NAME
            self.canv.setFont(font_name, font_size)
            text_y = y_center - (font_size * 0.35)
            self.canv.drawString(x, text_y, self.text.upper())

    def draw(self):
        self._draw_border()

        d_width = self._get_drawing_width()
        gap = config.HEADER_CONTENT_GAP
        content_max_width = self.width - 20
        text_avail_width = content_max_width - d_width - gap

        font_size = self._get_font_size()
        text_obj, text_width, text_height = self._prepare_text_layout(
            font_size, text_avail_width
        )

        total_content_width = d_width + gap + text_width
        start_x = (self.width - total_content_width) / 2
        center_y = self.height / 2

        self._draw_symbol(start_x, center_y)
        self._draw_text_element(
            start_x + d_width + gap, center_y, text_obj, text_height, font_size
        )
