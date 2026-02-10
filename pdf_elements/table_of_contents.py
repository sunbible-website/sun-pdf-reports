from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
from reportlab.platypus.flowables import Flowable

from configs.report_styles import get_table_styles
from utils import load_and_scale_svg


class TableOfContents(Flowable):
    """
    A dynamic Table of Contents (TOC) flowable that generates a table listing sections,
    their symbols, and page numbers.
    """

    def isIndexing(self):
        """
        Signals to the DocTemplate that this Flowable should receive notifications.
        Returns:
            bool: True (always listens for events).
        """
        return True

    def __init__(self, styles):
        """
        Initialize the TableOfContents.

        Args:
            styles (dict): A dictionary of ReportLab ParagraphStyles used for text formatting.
        """
        super().__init__()
        self.styles = styles
        self.entries = []  # Accumulates entries found in the *current* build pass
        self.prev_entries = []  # Stores entries from the *previous* build pass (used for drawing)
        self.table = None

    def notify(self, kind, stuff):
        """
        Callback method invoked by the DocTemplate when an event occurs.

        Args:
            kind (str): The type of notification (e.g., "TOCEntry").
            stuff (tuple): The data associated with the event.
                           Expected format: (page_number, section_name, icon_filename)
        """
        if kind == "TOCEntry":
            self.entries.append(stuff)

    def isSatisfied(self):
        """
        Determines if the TOC data has stabilized across build passes.

        The document build process continues looping until this returns True.

        Returns:
            bool: True if the current pass's entries match the previous pass's entries.
        """
        return self.entries == self.prev_entries

    def beforeBuild(self):
        """
        Lifecycle hook called by DocTemplate before a new build pass begins.

        Moves the entries collected in the *just completed* pass to `prev_entries`
        so they can be used to render the table in the *upcoming* pass.
        Resets `self.entries` to begin collecting fresh data.
        """
        self.prev_entries = list(self.entries)
        self.entries = []

    def afterBuild(self):
        """Lifecycle hook called after a build pass ends. (No-op here)."""
        pass

    def wrap(self, aW, aH):
        """
        Calculates the space required by the Table of Contents.

        Constructs the internal Table object using data from `self.prev_entries`.
        """
        self._build_table()
        if self.table:
            return self.table.wrap(aW, aH)
        return aW, 0

    def split(self, availWidth, availHeight):
        """
        Splits the Table of Contents across multiple pages if it's too tall.

        Returns:
            list: A list of Flowables (split parts of the table).
        """
        self._build_table()
        if self.table:
            return self.table.split(availWidth, availHeight)
        return []

    def draw(self):
        """Draws the constructed Table on the canvas."""
        if self.table:
            self.table.drawOn(self.canv, 0, 0)

    def _build_table(self):
        """
        Constructs the ReportLab Table object using the collected entries.

        This method creates the visual representation of the TOC, including headers,
        rows for each section, and applying styles. It uses `self.prev_entries`
        because that list contains the page numbers found in the previous full document scan.
        """
        if not self.prev_entries:
            self.table = None
            return

        header_row = self._create_header_row()
        table_data = [header_row]

        for entry in self.prev_entries:
            row = self._create_item_cells(entry)
            table_data.append(row)

        # Define Column Widths: [Section Name, Symbol, Page Number]
        col_widths = [4.5 * inch, 1.0 * inch, 1.0 * inch]

        self.table = Table(table_data, colWidths=col_widths)
        self.table.setStyle(self._get_table_style())

    def _create_header_row(self):
        """Creates the header row for the TOC table."""
        section_style = self.styles["toc_text"]
        symbol_style = self.styles["detail"]
        page_style = self.styles["toc_page"]

        headers = [
            Paragraph("<b>Section</b>", section_style),
            Paragraph("<b>Symbol</b>", symbol_style),
            Paragraph("<b>Page</b>", page_style),
        ]
        return headers

    def _create_item_cells(self, entry):
        """
        Creates a single row of cells for a TOC entry.

        Args:
            entry (tuple): (page_num, section_name, svg_file)

        Returns:
            list: [Paragraph(name), Image(symbol), Paragraph(page)]
        """
        page_num, section_name, svg_file = entry

        section_style = self.styles["toc_text"]
        page_style = self.styles["toc_page"]

        icon = load_and_scale_svg(svg_file, 0.5 * inch, 0.25 * inch)
        if not icon:
            icon = Spacer(1, 0.25 * inch)

        return [
            Paragraph(section_name, section_style),
            icon,
            Paragraph(str(page_num), page_style),
        ]

    def _get_table_style(self):
        """Retrieves the TableStyle defined in the global configuration."""
        return get_table_styles()["toc"]


class TOCReportingDocTemplate(SimpleDocTemplate):
    """
    A custom SimpleDocTemplate that acts as a bridge for TOC events.

    It overrides `afterFlowable` to detect specific flowables (like SectionHeaders)
    that want to be indexed. When found, it triggers a 'TOCEntry' notification,
    which is broadcast to any registered listeners (specifically, the TableOfContents flowable).
    """

    def afterFlowable(self, flowable):
        """
        Called automatically by the engine after each flowable is drawn.
        Checks if the flowable has a `toc_entry` attribute and broadcasts it.
        """
        toc_entry = getattr(flowable, "toc_entry", None)
        if toc_entry:
            text, icon = toc_entry
            self.notify("TOCEntry", (self.page, text, icon))

    def notify(self, kind, stuff):
        """
        Broadcasts a notification to all flowables in `_indexingFlowables`.

        The `_indexingFlowables` list is automatically populated by ReportLab
        with any flowables where `isIndexing()` returns True.
        """
        for f in getattr(self, "_indexingFlowables", []):
            f.notify(kind, stuff)
