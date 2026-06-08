import math

from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
)

from configs import report_styles
from pdf_elements.header import SectionHeader
from utils import clean_text, load_and_scale_svg


class CellHeader(SectionHeader):
    """Custom header for the table cell, reusing SectionHeader logic but without border."""

    def _draw_border(self):
        pass

    def _get_font_size(self):
        # Use a smaller font size for the table header
        return self.layout_config.HEADER_FONT_SIZE_SMALL


class WordTable:
    """
    Constructs a formatted Table flowable.
    Layout: Each cell contains [Symbol | Text Details].
    Layout details are passed in from layout config.
    """

    def __init__(
        self,
        group_data,
        detail_style,
        meta_style,
        layout_config,
        header_text,
        header_symbol_path,
    ):
        self.group_data = group_data
        self.detail_style = detail_style
        self.meta_style = meta_style
        self.layout_config = layout_config
        self.header_text = header_text
        self.header_symbol_path = header_symbol_path
        self.table_styles = report_styles.get_table_styles()

    def _get_symbol(self, record):
        """Loads and scales the SVG symbol for the record."""
        svg_name = f"{clean_text(record['unicode_id_id'])}.svg"
        return load_and_scale_svg(
            svg_name, self.layout_config.SVG_ICON_SIZE, self.layout_config.SVG_ICON_SIZE
        )

    def _get_text_content(self, record):
        """Builds the list of text paragraphs for the record."""
        # Main Word
        content = [Paragraph(f"<b>{clean_text(record['word'])}</b>", self.detail_style)]

        # Made from words
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
        symbol_element = (
            drawing if drawing else Spacer(1, self.layout_config.SVG_ICON_SIZE)
        )

        cell_sub_table = Table(
            [[symbol_element, text_content]],
            colWidths=self.layout_config.INNER_TABLE_COL_WIDTHS,
        )
        cell_sub_table.setStyle(self.table_styles["inner_cell"])
        return cell_sub_table

    def _create_cell(self, record):
        """Orchestrates the creation of a single table cell."""
        drawing = self._get_symbol(record)
        text_content = self._get_text_content(record)
        return self._layout_cell(drawing, text_content)

    def _create_header_cell(self):
        """Creates the header cell for the top of the column."""

        total_width = (
            self.layout_config.TABLE_COL_WIDTH * self.layout_config.TABLE_COLUMNS
        )

        return CellHeader(
            self.header_symbol_path,
            self.header_text,
            self.layout_config,
            width=total_width,
            height=self.layout_config.HEADER_HEIGHT * 0.8,
            gap=10,
        )

    def build(self):
        """
        Builds the main grid Table.

        It arranges items in 'Column-Major' order so the user reads down the first column,
        then down the second, etc.

        Example (10 items, 3 columns):
        - Column 1 contains items 0-3
        - Column 2 contains items 4-7
        - Column 3 contains items 8-9

        The code constructs rows to match this:
        - Row 1: [Item 0, Item 4, Item 8]
        - Row 2: [Item 1, Item 5, Item 9]
        - ...

        Returns:
            Table: The fully constructed ReportLab Table object.
        """
        if self.group_data.empty:
            return None

        columns = self.layout_config.TABLE_COLUMNS
        rows_count = math.ceil(len(self.group_data) / columns)

        table_data = []

        # Create header row
        header_cell = self._create_header_cell()
        header_row = [header_cell] + [""] * (columns - 1)
        table_data.append(header_row)

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
        col_width = self.layout_config.TABLE_COL_WIDTH
        table = Table(table_data, colWidths=[col_width] * columns, repeatRows=1)

        # Span the header row
        self.table_styles["main_grid"].add("SPAN", (0, 0), (-1, 0))
        self.table_styles["main_grid"].add("ALIGN", (0, 0), (-1, 0), "CENTER")

        table.setStyle(self.table_styles["main_grid"])

        return table
