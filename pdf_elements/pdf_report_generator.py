import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
)

from configs import report_styles
from data_query import get_data_query
from pdf_elements.footer import ReportFooter
from pdf_elements.header import SectionHeader
from pdf_elements.word_table import WordTable
from utils import clean_text


class PDFReportGenerator:
    """Handles the generation of the PDF report."""

    def __init__(
        self,
        engine,
        output_path,
        layout_config,
        language_id=1,
        include_section_headers=True,
    ):
        self.engine = engine
        self.output_path = output_path
        self.layout_config = layout_config
        self.language_id = language_id
        self.include_section_headers = include_section_headers
        self.styles = report_styles.get_report_styles()
        self.detail_style = self.styles["detail"]
        self.meta_style = self.styles["meta"]

    def fetch_data(self):
        """Fetches data from the database."""
        print(f"Fetching data for Language ID: {self.language_id}...")
        try:
            df = pd.read_sql_query(get_data_query(self.language_id), self.engine)
            print(f"Loaded {len(df)} records.")
            return df
        except Exception as e:
            print(f"Error reading from database: {e}")
            return None

    def _create_section_headers(self, first_record):
        """Creates the section header elements (Header + Spacer)."""
        section = clean_text(first_record["sectionname"])
        subsection = clean_text(first_record["subsectionname"])
        header_text = f"{section} {subsection}".strip()
        header_svg_file = f"{clean_text(first_record['unicode_id_id'])}.svg"

        return [
            SectionHeader(header_svg_file, header_text, self.layout_config),
            Spacer(1, self.layout_config.SECTION_SPACER_HEIGHT),
        ]

    def build_story(self, df):
        """
        Constructs the list of ReportLab pdf elements from the data.

        Process:
        1. Sorts data by Section (pdforderby) and then by Word (pageorderby).
        2. Groups the data by Section.
        3. For each section:
           - Creates a 'SectionHeader' with the section title and symbol.
           - Creates a 'WordTable' containing all words in that section.
           - Adds these elements to the list with spacers in between.

        Returns:
            list: A list of flowables (Headers, Spacers, Tables) ready for the PDF engine.
        """
        story = []
        df_sorted = df.sort_values(["pdforderby", "pageorderby"])

        for _, group in df_sorted.groupby("pdforderby"):
            first_record = group.iloc[0]

            if self.include_section_headers:
                story.extend(self._create_section_headers(first_record))

            table_builder = WordTable(
                group, self.detail_style, self.meta_style, self.layout_config
            )
            table = table_builder.build()
            if table:
                story.append(table)
                story.append(Spacer(1, self.layout_config.TABLE_SPACER_HEIGHT))
        return story

    def generate(self):
        """Executes the full report generation process."""
        df = self.fetch_data()
        if df is None or df.empty:
            print("No data found or error occurred.")
            return

        story = self.build_story(df)

        print(f"Building PDF: {self.output_path}...")
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=self.layout_config.PAGE_SIZE,
            leftMargin=self.layout_config.MARGIN_LEFT,
            rightMargin=self.layout_config.MARGIN_RIGHT,
            topMargin=self.layout_config.MARGIN_TOP,
            bottomMargin=self.layout_config.MARGIN_BOTTOM,
        )

        try:
            footer = ReportFooter(self.layout_config)
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            print("Success.")
        except Exception as e:
            print(f"Failed to build PDF: {e}")
