import math

from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
)

from configs import report_config as config
from configs import report_styles
from utils import clean_text, load_and_scale_svg


class WordTable:
    """
    Constructs a formatted Table flowable.
    Layout: 3 columns. Each cell contains [Symbol | Text Details].
    """

    def __init__(self, group_data, detail_style, meta_style):
        self.group_data = group_data
        self.detail_style = detail_style
        self.meta_style = meta_style
        self.table_styles = report_styles.get_table_styles()

    def _get_symbol(self, record):
        """Loads and scales the SVG symbol for the record."""
        svg_name = f"{clean_text(record['unicode_id_id'])}.svg"
        return load_and_scale_svg(svg_name, config.SVG_ICON_SIZE, config.SVG_ICON_SIZE)

    def _get_text_content(self, record):
        """Builds the list of text paragraphs for the record."""
        # Main Word
        content = [Paragraph(f"<b>{clean_text(record['word'])}</b>", self.detail_style)]

        # Construction / Etymology
        parts = [
            clean_text(record["made_from_word_1"]),
            clean_text(record["made_from_word_2"]),
            clean_text(record["made_from_word_3"]),
        ]
        parts = [p for p in parts if p]
        if parts:
            made_from_str = ", ".join(parts)
            content.append(Paragraph(f"({made_from_str})", self.meta_style))

        # Related Meaning
        related = clean_text(record["related_meaning"])
        if related:
            content.append(Paragraph(f"{related}", self.meta_style))

        return content

    def _layout_cell(self, drawing, text_content):
        """Combines symbol and text into the inner cell layout."""
        # Ensure there's a placeholder if drawing is missing to maintain alignment
        symbol_element = drawing if drawing else Spacer(1, config.SVG_ICON_SIZE)

        cell_sub_table = Table(
            [[symbol_element, text_content]],
            colWidths=config.INNER_TABLE_COL_WIDTHS,
        )
        cell_sub_table.setStyle(self.table_styles["inner_cell"])
        return cell_sub_table

    def _create_cell(self, record):
        """Orchestrates the creation of a single table cell."""
        drawing = self._get_symbol(record)
        text_content = self._get_text_content(record)
        return self._layout_cell(drawing, text_content)

    def build(self):
        """Builds the main grid Table."""
        if self.group_data.empty:
            return None

        columns = config.TABLE_COLUMNS
        rows_count = math.ceil(len(self.group_data) / columns)

        table_data = []

        for r in range(rows_count):
            row_cells = []
            for c in range(columns):
                idx = c * rows_count + r
                if idx < len(self.group_data):
                    record = self.group_data.iloc[idx]
                    row_cells.append(self._create_cell(record))
                else:
                    row_cells.append("")
            table_data.append(row_cells)

        # Main Grid Style
        col_width = config.TABLE_COL_WIDTH
        table = Table(table_data, colWidths=[col_width] * columns)
        table.setStyle(self.table_styles["main_grid"])

        return table
