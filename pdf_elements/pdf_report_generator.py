import pandas as pd
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Spacer

from configs import report_styles
from data_query import get_data_query
from pdf_elements.footer import ReportFooter
from pdf_elements.header import SectionHeader
from pdf_elements.table_of_contents import TableOfContents, TOCReportingDocTemplate
from pdf_elements.word_table import WordTable
from utils import clean_text, get_language_name


class PDFReportGenerator:
    """Handles the generation of the PDF report."""

    def __init__(
        self,
        engine,
        output_path,
        layout_config,
        language_id=1,
    ):
        self.engine = engine
        self.output_path = output_path
        self.layout_config = layout_config
        self.language_id = language_id
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
        if self.language_id == 1:
            subsection = clean_text(first_record["subsectionname"])
            header_text = f"{section} {subsection}".strip()
        else:
            header_text = f"{section}".strip()
        header_svg_file = f"{clean_text(first_record['sectionunicode'])}.svg"

        return [
            SectionHeader(header_svg_file, header_text, self.layout_config),
            Spacer(1, self.layout_config.SECTION_SPACER_HEIGHT),
        ]

    def _create_toc(self):
        """Creates the Table of Contents section."""
        story = []
        toc = TableOfContents(self.styles)
        story.append(Paragraph("Table of Contents", self.styles["header"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(toc)
        story.append(PageBreak())
        return story

    def build_story(self, df):
        """
        Constructs the list of ReportLab pdf elements from the data.
        """
        story = []

        # --- Table of Contents ---
        story.extend(self._create_toc())

        # --- Dictionary Content ---
        df_sorted = df.sort_values(["pdforderby", "pageorderby"])

        for _, group in df_sorted.groupby("pdforderby"):
            first_record = group.iloc[0]

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

        # Fetch language info for the footer
        language_name = get_language_name(self.engine, self.language_id)

        story = self.build_story(df)

        print(f"Building PDF: {self.output_path}...")

        # Use our custom DocTemplate that knows how to report TOC entries
        doc = TOCReportingDocTemplate(
            self.output_path,
            pagesize=self.layout_config.PAGE_SIZE,
            leftMargin=self.layout_config.MARGIN_LEFT,
            rightMargin=self.layout_config.MARGIN_RIGHT,
            topMargin=self.layout_config.MARGIN_TOP,
            bottomMargin=self.layout_config.MARGIN_BOTTOM,
        )

        try:
            footer = ReportFooter(self.layout_config, language_name)
            # multiBuild is required for the TOC to learn page numbers
            doc.multiBuild(story, onFirstPage=footer, onLaterPages=footer)
            print("Success.")
        except Exception as e:
            print(f"Failed to build PDF: {e}")
            import traceback

            traceback.print_exc()
