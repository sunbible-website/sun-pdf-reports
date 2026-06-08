from configs import report_styles


class ReportFooter:
    """Handles drawing the footer on each PDF page."""

    def __init__(self, layout_config, language_text):
        self.layout_config = layout_config
        self.language_text = language_text
        self.styles = report_styles.get_report_styles()
        self.style = self.styles["footer"]

    def __call__(self, canvas, doc):
        """
        Callback to draw footer on every page.
        Saves the current state of the canvas and restores it
        when it has finished generating the footer.
        """
        canvas.saveState()
        self._draw_footer(canvas)
        canvas.restoreState()

    def _draw_footer(self, canvas):
        """Draws the page number and footer text at the bottom."""
        font_name = self.style.fontName
        font_size = self.style.fontSize

        canvas.setFont(font_name, font_size)
        canvas.setFillColor(self.style.textColor)

        page_num = canvas.getPageNumber()
        text = f"- Reader's Dictionary - {self.language_text} - {page_num} -"
        width = canvas.stringWidth(text, font_name, font_size)

        x_pos = (self.layout_config.PAGE_SIZE[0] - width) / 2
        y_pos = self.layout_config.FOOTER_Y_POS
        canvas.drawString(x_pos, y_pos, text)
