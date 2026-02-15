from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from pdf.styles import *
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from config import PAGE_SIZES, PAGE_MARGINS

story = []
 
class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas that adds footer page numbering
    starting after a specified page.
    """
    def __init__(self, *args, language_abvr=None, start_numbering_after=1, **kwargs):
        super().__init__(*args, **kwargs)
        self._language_abvr = language_abvr
        self._start_numbering_after = start_numbering_after
        self._pdf_page_counter = 0
        self._pages_with_footer = set()  # track which pages already got a footer

    def draw_footer(self):
        page_num = self.getPageNumber()
        # Only start numbering after specified page
        if page_num > self._start_numbering_after and page_num not in self._pages_with_footer:
            self._pdf_page_counter += 1
            footer = (
                f"Reader's Dictionary – "
                f"{datetime.now().strftime('%B %d, %Y')} – "
                f"{self._language_abvr} – "
                f"Page No. {self._pdf_page_counter}"
            )
            self.setFont("Helvetica", 9)
            self.drawCentredString(4.25 * inch, 0.5 * inch, footer)
            self._pages_with_footer.add(page_num)

    def showPage(self):
        self.draw_footer()
        super().showPage()

    def save(self):
        # Only draw footer if this page hasn't been numbered yet
        if self.getPageNumber() not in self._pages_with_footer:
            self.draw_footer()
        super().save()
        
def build_doc(output_pdf_path):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=PAGE_SIZES['letter'],
        rightMargin=PAGE_MARGINS['custom'][0],
        leftMargin=PAGE_MARGINS['custom'][1],
        topMargin=PAGE_MARGINS['custom'][2],
        bottomMargin=PAGE_MARGINS['custom'][3]
    )
    return doc

def toc():
    story.append(Paragraph("Table of Contents", instruction_title_style))
    story.append(Spacer(1, 0.2 * inch))

    toc_placeholder_index = len(story)
    story.append(Spacer(1, 1))  # placeholder for TOC table

    story.append(PageBreak())
    return toc_placeholder_index

def buid_pdf(doc, language_abvr, TOC_LAST_PAGE, output_pdf_path):
    try:
        # adjust based on your story
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: NumberedCanvas(
                *args,
                language_abvr=language_abvr,
                start_numbering_after=TOC_LAST_PAGE,
                **kwargs
            )
        )


        print(f"PDF created: {output_pdf_path}")
    except Exception as e:
        print(f"PDF build error: {e}")