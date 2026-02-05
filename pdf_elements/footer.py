from pandas.core.arrays.datetimes import datetime
from reportlab.lib import colors

from configs import report_config as config
from configs import report_styles


class ReportFooter:
    """Handles drawing the footer on each PDF page."""

    def __init__(self):
        self.styles = report_styles.get_report_styles()
        self.style = self.styles["footer"]

    def __call__(self, canvas, doc):
        """
        Callback to draw footer on every page.
        Saves the current state of the canvas and restores it
        when it has finished generating the footer.
        """
        canvas.saveState()

        font_name = self.style.fontName
        font_size = self.style.fontSize
        canvas.setFont(font_name, font_size)
        canvas.setFillColor(self.style.textColor)

        page_num = canvas.getPageNumber()
        text = f"Reader's Dictionary - {datetime.now().strftime('%Y-%m-%d')}  |  Page {page_num}"
        width = canvas.stringWidth(text, font_name, font_size)

        x_pos = (config.PAGE_SIZE[0] - width) / 2
        y_pos = config.FOOTER_Y_POS
        canvas.drawString(x_pos, y_pos, text)

        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(
            config.MARGIN_LEFT,
            y_pos + config.FOOTER_LINE_Y_OFFSET,
            config.PAGE_SIZE[0] - config.MARGIN_RIGHT,
            y_pos + config.FOOTER_LINE_Y_OFFSET,
        )
        canvas.restoreState()
