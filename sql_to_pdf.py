import os
import math
import getpass
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from datetime import datetime
from svglib.svglib import svg2rlg
from collections import defaultdict
import re

QUOTE_RE = re.compile(r'“([^”]+)”|"([^"]+)"')

GRAMMAR_SVG_RE = re.compile(r"[]")
WORD_RE = re.compile(r"\b\w+\b")

# Folder containing SVGs
SVG_FOLDER = "svg-symbols"
SUN_LOGO = "sun_logo.png"

MAX_ROWS_PER_PAGE = 42

class NumberedCanvas(canvas.Canvas):
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
       
class SvgAndWordHeader(Flowable):
    """Flowable to display an SVG and a word (section + subsection) side by side"""
    def __init__(self, svg_path, word, max_height=0.4*inch):
        super().__init__()
        self.word = word
        self.max_height = max_height
        self.drawing = None
        if os.path.exists(svg_path):
            self.drawing = svg2rlg(svg_path)
            if self.drawing.height > 0:
                scale = min(max_height / self.drawing.height, 1)
                self.drawing.width *= scale
                self.drawing.height *= scale
                self.drawing.scale(scale, scale)

    def wrap(self, availWidth, availHeight):
        return availWidth, self.max_height

    def draw(self):
        x_offset = 0
        if self.drawing:
            renderPDF.draw(self.drawing, self.canv, 0, 0)
            x_offset = self.drawing.width + 5  # space between symbol and text
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawString(x_offset, 0, self.word)
        

class InlineExampleLine(Flowable):
    def __init__(self, word_or_words, sentence, style, word_to_svg,
                 svg_height=0.22 * inch, gap=4):
        super().__init__()

        # Detect list vs single word
        self.is_list = isinstance(word_or_words, (list, tuple))

        if self.is_list:
            self.words = list(word_or_words)
            self.word = self.words[0] if self.words else ""
        else:
            self.word = word_or_words
            self.words = [word_or_words]

        self.sentence = sentence
        self.style = style
        self.word_to_svg = word_to_svg
        self.svg_height = svg_height
        self.gap = gap
        self.parts = []

        self._build_parts()

    def _load_svg(self, svg_filename):
        svg_path = os.path.join(SVG_FOLDER, svg_filename)
        if not os.path.exists(svg_path):
            return None

        drawing = svg2rlg(svg_path)
        if drawing.height <= 0:
            return None

        scale = self.svg_height / drawing.height
        drawing.scale(scale, scale)
        drawing.width *= scale
        drawing.height *= scale
        return drawing

    def _build_parts(self):
        # --- MAIN WORD(S) ---
        for word in self.words:
            # Only print text if NOT a list
            if not self.is_list:
                self.parts.append(("text", word + " ", "bold"))

            svg_filename = self.word_to_svg.get(word.lower())
            if svg_filename:
                drawing = self._load_svg(svg_filename)
                if drawing:
                    self.parts.append(("svg", drawing))

        # --- SENTENCE (with quoted words + SVGs) ---
        pos = 0
        for match in QUOTE_RE.finditer(self.sentence):
            start, end = match.span()
            qword = match.group(1) or match.group(2)

            if start > pos:
                self.parts.append(("text", self.sentence[pos:start], "normal"))

            self.parts.append(("text", f"“{qword}”", "normal"))

            svg_filename = self.word_to_svg.get(qword.lower())
            if svg_filename:
                drawing = self._load_svg(svg_filename)
                if drawing:
                    self.parts.append(("svg", drawing))

            pos = end

        if pos < len(self.sentence):
            self.parts.append(("text", self.sentence[pos:], "normal"))

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = max(self.style.leading, self.svg_height)
        return availWidth, self.height

    def draw(self):
        c = self.canv
        x = 0
        y = 0

        for part in self.parts:
            if part[0] == "text":
                text, weight = part[1], part[2]
                font = "Helvetica-Bold" if weight == "bold" else self.style.fontName
                c.setFont(font, self.style.fontSize)
                c.drawString(x, y, text)
                x += c.stringWidth(text, font, self.style.fontSize)
            else:
                drawing = part[1]
                renderPDF.draw(
                    drawing,
                    c,
                    x,
                    y - (drawing.height - self.style.fontSize) / 2
                )
                x += drawing.width + self.gap

class InlineGrammarLine(Flowable):
    def __init__(self, text, style, word_to_svg, svg_words=None,
                 svg_height=0.22 * inch, gap=4):
        super().__init__()
        self.text = text
        self.style = style
        self.word_to_svg = word_to_svg
        self.svg_words = svg_words or []   # <-- list for 
        self.svg_height = svg_height
        self.gap = gap
        self.parts = []

        self._build_parts()

    def _load_svg(self, svg_filename):
        svg_path = os.path.join(SVG_FOLDER, svg_filename)
        if not os.path.exists(svg_path):
            return None

        drawing = svg2rlg(svg_path)
        scale = self.svg_height / drawing.height
        drawing.scale(scale, scale)
        drawing.width *= scale
        drawing.height *= scale
        return drawing

    def _build_parts(self):
        pos = 0

        for match in GRAMMAR_SVG_RE.finditer(self.text):
            start, end = match.span()
            symbol = match.group()

            # text before symbol
            if start > pos:
                self.parts.append(("text", self.text[pos:start]))

            words_for_svg = []

            # --- RULE 1: explicit list always wins ---
            if self.svg_words:
                words_for_svg = self.svg_words

            # --- RULE 2:  logic ---
            elif symbol == "":
                after = self.text[end:]
                before = self.text[:start]

                # if '=' exists → words after '='
                if "=" in after:
                    rhs = after.split("=", 1)[1]
                    words_for_svg = WORD_RE.findall(rhs)
                    
                if "=" in before:
                    lhs = before.rsplit("=", 1)[0]
                    words = WORD_RE.findall(lhs)
                    if words:
                        words_for_svg = [words[-1]]

                # else → word before 
                else:
                    before = self.text[:start]
                    words = WORD_RE.findall(before)
                    if words:
                        words_for_svg = [words[-1]]

            # --- RULE 3:  logic (list only, no text) ---
            elif symbol == "" and self.svg_words:
                words_for_svg = self.svg_words

            # render SVGs
            for word in words_for_svg:
                svg_filename = self.word_to_svg.get(word.lower())
                if svg_filename:
                    drawing = self._load_svg(svg_filename)
                    if drawing:
                        self.parts.append(("svg", drawing))

            pos = end

        # remaining text
        if pos < len(self.text):
            self.parts.append(("text", self.text[pos:]))

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = max(self.style.leading, self.svg_height)
        return availWidth, self.height

    def draw(self):
        c = self.canv
        x = 0
        y = 0

        for part in self.parts:
            if part[0] == "text":
                c.setFont(self.style.fontName, self.style.fontSize)
                c.drawString(x, y, part[1])
                x += c.stringWidth(part[1], self.style.fontName, self.style.fontSize)
            else:
                drawing = part[1]
                renderPDF.draw(
                    drawing,
                    c,
                    x,
                    y - (drawing.height - self.style.fontSize) / 2
                )
                x += drawing.width + self.gap


def get_language_name(engine, language_id):
    query = """
    SELECT name, language_abvr
    FROM sun.language
    WHERE language_id = %(language_id)s
    """
    df = pd.read_sql_query(query, engine, params={"language_id": language_id})

    if df.empty:
        raise ValueError(f"No language found for language_id={language_id}")

    return df.iloc[0]["name"], df.iloc[0]["language_abvr"]


def small_svg_for_word(word, word_to_svg, size=0.25 * inch):
    svg_filename = word_to_svg.get(word.lower())
    if not svg_filename:
        return Spacer(1, size)

    svg_path = os.path.join(SVG_FOLDER, svg_filename)
    if not os.path.exists(svg_path):
        return Spacer(1, size)

    drawing = svg2rlg(svg_path)
    scale = min(size / drawing.width, size / drawing.height)
    drawing.scale(scale, scale)
    drawing.width *= scale
    drawing.height *= scale
    return drawing


def create_pdf_report(engine, output_pdf_path, language_id):
    """Create a PDF report from sun schema SQL tables with SVG symbols."""
    # --- READ DATA ---
    try:
        query = """
        SELECT
            readersdetail.readersdetailid,
            readersdetail.sectionid,
            readersdetail.unicodeid,
            readersdetail.pageorderby,

            readers.unicodeid AS sectionunicode,
            readers.sectionname,
            readers.subsectionname,
            readers.pdforderby,

            wordlists.word,
            wordlists.unicode_id_id,
            wordlists.unicode_id_id || '.svg' AS svgname,
            wordlists.related_meaning,
            wordlists.made_from_word_1,
            wordlists.made_from_word_2,
            wordlists.made_from_word_3,
            wordlists.made_from_word_4,
            wordlists.made_from_word_5,
            wordlists.made_from_word_6,
            wordlists.made_from_word_7,
            wordlists.related_meaning,

            language.txt_readers_dict_cover_1,
            language.txt_page_no

        FROM sun.readersdetail
        JOIN sun.readers
            ON readersdetail.sectionid = readers.sectionid
        JOIN sun.wordlists AS wordlists
            ON readersdetail.unicodeid = wordlists.unicode_id_id
           AND readers.languageid = wordlists.language_id_id
        JOIN sun.language AS language
            ON readers.languageid = language.language_id
        WHERE readers.languageid = %(language_id)s
        ORDER BY readers.pdforderby, readersdetail.pageorderby ASC;
        """
        df = pd.read_sql_query(query, engine, params={"language_id": language_id})
        # --- Build word -> svg filename lookup ---
        word_to_svg = {}
        for _, row in df.iterrows():
            word = str(row["word"]).strip().lower()
            unicode_id = str(row["unicode_id_id"]).strip()
            if word and unicode_id:
                word_to_svg[word] = f"{unicode_id}.svg"

        print(f"Loaded {len(df)} records from database")
    except Exception as e:
        print(f"Error reading SQL data: {e}")
        return
    
    # --- Get language name ---
    language_name, language_abvr = get_language_name(engine, language_id)

    # --- PDF SETUP ---
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=1,  # CENTER
        spaceAfter=12
    )

    cover_subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        alignment=1,
        spaceAfter=24
    )

    cover_meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontSize=10,
        alignment=1,
        spaceAfter=8
    )
    
    instruction_title_style = ParagraphStyle(
        "InstructionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        alignment=1,  # center
        spaceAfter=18
    )

    instruction_body_style = ParagraphStyle(
        "InstructionBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=10
    )

    instruction_list_style = ParagraphStyle(
        "InstructionList",
        parent=styles["Normal"],
        fontSize=11,
        leftIndent=18,
        leading=14,
        spaceAfter=6
)
    detail_style = ParagraphStyle(
        "Detail",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=2
    )


    appendix_style = ParagraphStyle(
        "Detail",
        parent=styles["Normal"],
        fontSize=7,
        spaceAfter=2
    )
    
    sun_title_style = ParagraphStyle(
    "SUNTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=120,
    leading=120,
    alignment=1,
    spaceAfter=36
)

    
    story = []

    # --- FRONT PAGE ---
    now = datetime.now()

    story.extend([
        Spacer(1, 0.5 * inch),

        Paragraph("SUN", sun_title_style),
        
        Spacer(1, 0.1 * inch),
        
        Paragraph("Symbolic Universal Notation", cover_title_style),
        Paragraph(f"READER'S DICTIONARY - {language_name}", cover_subtitle_style),

        Spacer(1, 0.5 * inch),
        
        #insert png logo here centered
        Image(SUN_LOGO, width=2*inch, height=2*inch, hAlign='CENTER'),
        
        Spacer(1, 0.5 * inch),

        Paragraph(
            f"Wycliffe Associates - Version {now.strftime('%Y-%m-%d')}<br/>"
            f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            cover_meta_style
        ),

        Spacer(1, 0.15 * inch),

        Paragraph(
            "This work is licensed under a Creative Commons "
            "Attribution-ShareAlike 4.0 International License.",
            cover_meta_style
        ),

        PageBreak()
        
    ])
    
    # --- HOW TO USE PAGE ---

    story.append(Paragraph(
        "How to Use the SUN Reader’s Dictionary",
        instruction_title_style
    ))

    story.append(Paragraph(
        "This dictionary contains all the words in the Bible and is useful for a reader to look up the "
        "meaning of a new symbol that they encounter in the text.",
        instruction_body_style
    ))

    story.append(Paragraph(
        "The dictionary is organized by the basic, core symbols. The Table of Contents lists all the "
        "basic symbols and gives the page number where a basic symbol’s changes and combinations "
        "can be found. Page numbers are located at the bottom of the page.",
        instruction_body_style
    ))

    story.append(Paragraph(
        "In addition, at the end of the Table of Contents there are page numbers for the Proper Noun "
        "combinations.",
        instruction_body_style
    ))
    steps = [
        "When a symbol with a change or combination needs to be found, look carefully at all the "
        "basic symbols that are a part of the combination.",
        "Choose one of the basic symbols that will be the most helpful for you.",
        "In the Table of Contents, find that basic symbol and its page number.",
        "Turn to that page number and search for the change or combination that you need. It may "
        "be easiest to search down the columns.",
        "The main meaning is in bold print and the other secondary meanings are in italics below "
        "the main meaning.",
        "The words in the parentheses are teaching aids to explain the combination."
    ]

    for i, step in enumerate(steps, start=1):
        story.append(Paragraph(f"{i}. {step}", instruction_list_style))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("<b>Examples:</b>", instruction_body_style))

    story.append(
        InlineExampleLine(
            "father",
            "This symbol can be found in the “man” and “love” sections.",
            instruction_body_style,
            word_to_svg
        )
    )

    examples = [
        ("eternal", "This symbol can be found in the “all” and “time” sections."),
        ("give", "This symbol can be found in the “hand” and “love” sections."),
        ("descend", "This symbol can be found in the “straight” and “arrow” sections."),
    ]

    for word, text in examples:
        story.append(InlineExampleLine(
            word,
            text,
            instruction_body_style,
            word_to_svg
        ))

        
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("<b>Exceptions:</b>", instruction_body_style))

    story.append(InlineExampleLine(
        "money",
        "Circle is not a basic symbol, so look under “king” to find this symbol.",
        instruction_body_style,
        word_to_svg
    ))

    story.append(InlineExampleLine(
        "deep",
        "The squiggly line is not a basic symbol, so look under “arrow” for this symbol.",
        instruction_body_style,
        word_to_svg
    ))


    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph(
        "<u>Proper nouns:</u> Proper nouns always have a small up arrow on the upper left of the symbol. Locate the "
        "Proper Noun base symbol category at the end of the Table of Contents. The category for "
        "“Proper Nouns Other” includes Bible, people groups, festival days, angels, idols, etc.",
        instruction_body_style
    ))

# --- SUN GRAMMAR RULES PAGE ---
    story.append(PageBreak())

    story.append(Paragraph(
        "SUN Grammar Rules for Readers",
        instruction_title_style
    ))

    # Grammar instructions
    grammar_paragraphs = [
        "1) Proper nouns have a special indicator mark, a small arrow in the upper left corner of "
        "the symbol. Proper nouns are names of people and places.",
    ]

    for para in grammar_paragraphs:
        story.append(Paragraph(para, instruction_body_style))
        story.append(Spacer(1, 0.1*inch))
        
    story.append(
        InlineGrammarLine(
            "2) Plural words are typed twice. Example: things = . Exceptions are:",
            instruction_body_style,
            word_to_svg,
            svg_words=["thing", "thing"]
        )
    )

    grammar_lines = [
        
        "boys = , sons = , brothers = , girls = , daughters = ",
        "sisters = , children = . Only nouns are made plural in SUN, not verbs.",
    ]

    for line in grammar_lines:
        story.append(
            InlineGrammarLine(
                line,
                instruction_body_style,
                word_to_svg
            )
        )
    special = {
        "   • Ordinal numbers are followed by a singular noun.": [],
        "       Example:  = third day.":["three", "sun"],
        "   • Cardinal numbers are followed by a plural noun.":[],
        "       Example:  = three days.":["three", "sun", "sun"],
        "       All day = ":["all", "sun"],
        "       Every day = ":["all", "sun", "sun"],
        "3) Black dots in the corner of words mean the word is possesive":[]
        
    }
    for line, wrds in special.items():
        story.append(
            InlineGrammarLine(
                str(line),
                instruction_body_style,
                word_to_svg,
                svg_words=list(wrds)
            )
        )
        story.append(Spacer(1, 0.08 * inch))

    # --- Possessive examples ---
    story.append(Paragraph("<b>Possessive words:</b>", instruction_body_style))

    possessive_examples = [
        (["possessive","me"], " = my"),
        (["possessive","you"], " = yours"),
        (["possessive","us"], " = our"),
        (["possessive","they"], " = theirs"),
    ]

    for words, text in possessive_examples:
        story.append(
            InlineExampleLine(
                words,
                text,
                instruction_body_style,
                word_to_svg
            )
        )
# --- Sentence Structure Rules Page ---
    story.append(PageBreak())

    # Intro paragraph
    story.append(Paragraph(
        "4.) All sentences follow this sentence structure:",
        instruction_body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    # Bullet points
    structure_points = [
        "Subject, Verb, Direct Object",
        "Adjectives before the noun",
        "Adverbs before the verb",
    ]

    for point in structure_points:
        story.append(Paragraph(f"   • {point}", instruction_body_style))
        story.append(Spacer(1, 0.05*inch))

    story.append(
        InlineGrammarLine(
            "   • Possessives before the thing they possess. Example: God’s house.: ",
            instruction_body_style,
            word_to_svg,
            svg_words=["God", "possessive", "house"]
            ))
    # Exceptions header
    story.append(Paragraph("<b>Exceptions:</b>", instruction_body_style))

    # Exception examples: (text, optional word for SVG)
    exception_examples = [
        ("      1. If the verse is a command, it begins with a verb.", None), 
        ("      Example: put oil in flour ", ["put", "oil", "in", "flour", "period"]),
        ("      2. Some verses begin with an if clause. The second sentence completes the thought. ", None),
        ("      For instance: if cloud cover tent. people no go in tent. ", ["if", "cloud", "cover", "tent","period", "people", "no", "go", "in", "tent", "period"]),
        ("      3. Some verses begin with a because clause. The second sentence completes the thought. ", None),
        ("      For instance: because you past gentiles in Egypt. love gentile same love self. ", None),
        ("      ", ["because", "you", "past", "gentiles", "in", "Egypt", "period", "love", "gentile", "same", "love", "self", "period"]),
        ("      4. Some verses begin with a time reference, beginning with 'when', 'after', 'day', or 'night.' ", None),
        ("      For instance: after you prepare grain offering. take grain offering to Yahweh. ", None),
        ("      ", ["after", "you", "prepare", "grain", "offering","period" , "take", "grain", "offering", "to", "Yahweh", "period"])
    ]

    for text, svg_words in exception_examples:
        if svg_words:
            story.append(
                InlineGrammarLine(
                    text,
                    instruction_body_style,
                    word_to_svg,
                    svg_words=svg_words
                )
            )
        else:
            story.append(Paragraph(text, instruction_body_style))
        story.append(Spacer(1, 0.05*inch))

    # Length & numbers
    story.append(Paragraph(
        "5.) All sentences are no more than 7 symbols long.", instruction_body_style
    ))
    story.append(Spacer(1, 0.05*inch))

    story.append(Paragraph(
        "6.) Numbers greater than ten are written separately.", instruction_body_style
    ))
    story.append(Spacer(1, 0.1*inch))

    # Number examples: (word, sentence text)
    number_examples = [
        (["one", "two"], " = twelve"),
        (["two","three"], " = twenty-three"),
        (["one", "four", "five"], " = one hundred forty-five"),
        (["six", "zero", "zero"], " = six hundred"),
        (["nine", "zero", "one","three"], " = nine thousand thirteen")
    ]

    for words, text in number_examples:
        # use first word of description for SVG
        story.append(
            InlineExampleLine(
                words,
                text,
                instruction_body_style,
                word_to_svg
            )
        )

    story.append(PageBreak())
    story.append(Paragraph("Table of Contents", instruction_title_style))
    story.append(Spacer(1, 0.2 * inch))

    toc_placeholder_index = len(story)
    story.append(Spacer(1, 1))  # placeholder for TOC table

    story.append(PageBreak())


    # --- SORT & GROUP ---
    df_sorted = df.sort_values(["pdforderby", "pageorderby"])
    

    def clean(value):
        return str(value).strip() if pd.notna(value) and str(value).strip() else ""

    def boost_strokes(drawing, min_stroke=1.2):
        for elem in drawing.contents:
            if hasattr(elem, "strokeWidth") and elem.strokeWidth:
                elem.strokeWidth = max(elem.strokeWidth, min_stroke)
            if hasattr(elem, "contents"):
                boost_strokes(elem, min_stroke)
    
    # Keep track of which words appear on which pages
    word_page_map = {}
    current_page_number = 1
    
    count = 0
    
    for pdf_order, group_data in df_sorted.groupby("pdforderby"):
        first = group_data.iloc[0]

        # --- HEADER: symbol + section + subsection ---
        section_name = clean(first["sectionname"])
        subsection_name = clean(first["subsectionname"])
        header_text = section_name
        if subsection_name:
            header_text = subsection_name + " - " + section_name

        # val = first['unicode_id_id']
        first_svg_file = f"{str(first['sectionunicode']).strip()}.svg"
        if not subsection_name:
            first_svg_path = os.path.join(SVG_FOLDER, first_svg_file)
        else:
            first_svg_path = ""
        
        story.append(SvgAndWordHeader(first_svg_path, header_text))
        story.append(Spacer(1, 0.15*inch))

        # --- DETAIL RECORDS AS TABLE ---
        if len(group_data) > 0:
            # Convert group_data to a list of dicts (or DataFrame rows)
            group_rows = group_data.to_dict(orient="records")

            # Split into pages of at most MAX_ROWS_PER_PAGE
            for page_start in range(0, len(group_rows), MAX_ROWS_PER_PAGE):
                
                words_on_page = []
                page_rows = group_rows[page_start:page_start + MAX_ROWS_PER_PAGE]

                # BUILD TABLE FOR THIS PAGE
                table_data = []

                # Header row
                header_row = []
                for _ in range(3):  # 3 columns
                    header_row.extend([Paragraph("<b>Symbol</b>", detail_style),
                                    Paragraph("<b>Word</b>", detail_style)])
                table_data.append(header_row)

                # Build table rows
                rows_per_column = math.ceil(len(page_rows) / 3)
                for r in range(rows_per_column):
                    row_cells = []
                    for c in range(3):
                        idx = c * rows_per_column + r
                        if idx < len(page_rows):
                            row = page_rows[idx]
                            #insert word to words_on_page
                            words_on_page.append(clean(row['word']))

                            # SYMBOL
                            svg_file = f"{str(row['unicode_id_id']).strip()}.svg"
                            svg_path = os.path.join(SVG_FOLDER, svg_file)
                            if os.path.exists(svg_path):
                                drawing = svg2rlg(svg_path)
                                scale = min(0.5*inch / drawing.width, 0.5*inch / drawing.height)
                                drawing.width *= scale
                                drawing.height *= scale
                                drawing.scale(scale, scale)
                                boost_strokes(drawing)
                                row_cells.append(drawing)
                            else:
                                row_cells.append(Paragraph("", detail_style))

                            # WORD
                            made_from_cols = [col for col in row.keys() if col.startswith("made_from_word_")]
                            # rel_cols = [col for col in row.keys() if col.startswith("made_from_word_")]
                            if row['related_meaning']:
                                all_words = [str(row['related_meaning']).strip()]
                            else:
                                all_words = []
                            mf_words = [str(row[col]).strip() for col in made_from_cols if row[col]]
                            all_words += mf_words
                            if all_words:
                                row_cells.append(
                                    Paragraph(f"{clean(row['word']).replace('_', ' ')}<br/><font size='7'><i>({', '.join(all_words)})</i></font>", detail_style)
                                )
                            else:
                                row_cells.append(Paragraph(f"{clean(row['word']).replace('_', ' ')}", detail_style))
                        else:
                            row_cells.extend([Paragraph("", detail_style), Paragraph("", detail_style)])
                    table_data.append(row_cells)

                # Create table
                table = Table(table_data, colWidths=[0.7*inch, 1.8*inch]*3)
                table.setStyle(TableStyle([
                    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("LEFTPADDING", (0,0), (-1,-1), 4),
                    ("RIGHTPADDING", (0,0), (-1,-1), 4),
                    ("TOPPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
                ]))
                
                # if words_on_page does not exist in map, add it
                if tuple(words_on_page) not in word_page_map.keys():
                    word_page_map[tuple(words_on_page)] = current_page_number
                else:
                    word_page_map[tuple(words_on_page)+(str(count),)] = current_page_number
                story.append(table)
                story.append(PageBreak())
                current_page_number += 1  # increment page counter for TOC
                count += 1

    # TOC table header
    toc_table_data = [
        [Paragraph("<b>Word</b>", detail_style),
        Paragraph("<b>Symbol</b>", detail_style),
        Paragraph("<b>Page No.</b>", detail_style),
        Paragraph("<b>Word</b>", detail_style),
        Paragraph("<b>Symbol</b>", detail_style),
        Paragraph("<b>Page No.</b>", detail_style)]
    ]

    # Sort words in the same order as table pages
    words_in_order = [str(row['word']).strip() for _, row in df_sorted.iterrows()]
    words_in_order = list(dict.fromkeys(words_in_order))  # remove duplicates while preserving order
    rows = []
    for i in range(0, len(words_in_order), 2):
        row_cells = []
        for j in range(2):
            if i+j < len(words_in_order):
                word = words_in_order[i+j]
                page_nos = []
                for words_tuple, page_no in word_page_map.items():
                    if word in words_tuple:
                        page_nos.append(page_no)
                page_no = page_nos[0]
                symbol = small_svg_for_word(word, word_to_svg, size=0.25*inch)
                row_cells.extend([Paragraph(word.replace("_", " "), detail_style), symbol, Paragraph(str(page_no), detail_style)])
            else:
                row_cells.extend([Paragraph("", detail_style), Paragraph("", detail_style), Paragraph("", detail_style)])
        toc_table_data.append(row_cells)

    toc_table = Table(toc_table_data, colWidths=[1.8*inch, 0.7*inch, 0.7*inch]*2)
    story[toc_placeholder_index] = toc_table
    toc_table.setStyle(TableStyle([
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("LEFTPADDING", (0,0), (-1,-1), 4),
                ("RIGHTPADDING", (0,0), (-1,-1), 4),
                ("TOPPADDING", (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ]))

    # Filter lowercase words only
    lowercase_words = [
        str(row['word']).strip() 
        for _, row in df_sorted.iterrows()
        if str(row['word']).strip() and str(row['word']).strip()[0].islower()
    ]

    word_pages = defaultdict(list)
    for _, row in df_sorted.iterrows():
        word = str(row['word']).strip()
        if word and word[0].islower():
            for words_tuple, page_no in word_page_map.items():
                page_nos = []
                if word in words_tuple:
                    page_nos.append(page_no)
                
                if page_nos is not None:
                    word_pages[word].extend(page_nos)

    # Sort words alphabetically
    sorted_words = sorted(word_pages.keys())


    index_table_data = []
    first_lowercase = []

    # Split words into 3 columns
    col1, col2, col3 = [], [], []
    for i, word in enumerate(sorted_words):
        # Format: word ..page1, page2, ...
        pages = ", ".join(str(p) for p in sorted(list(set(word_pages[word]))))
        if word[0] not in first_lowercase:
            text = f"<b>{word.replace("_", " ")}</b> – <i>{pages}</i>"
            first_lowercase.append(word[0])
        else:
            text = f"{word.replace("_", " ")} – <i>{pages}</i>"

        # Cycle through 3 columns
        if i % 3 == 0:
            col1.append(text)
        elif i % 3 == 1:
            col2.append(text)
        else:
            col3.append(text)

    # Make all columns the same length by padding with empty strings
    max_len = max(len(col1), len(col2), len(col3))
    col1 += [""] * (max_len - len(col1))
    col2 += [""] * (max_len - len(col2))
    col3 += [""] * (max_len - len(col3))

    # Combine into table rows
    for r in range(max_len):
        index_table_data.append([Paragraph(col1[r], appendix_style),
                                Paragraph(col2[r], appendix_style),
                                Paragraph(col3[r], appendix_style)])

    # Add a page break and header
    # story.append(PageBreak())
    story.append(Paragraph("Common words", instruction_title_style))
    story.append(Spacer(1, 0.2*inch))

    # Create the table
    index_table = Table(index_table_data, colWidths=[2.2*inch]*3)
    index_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(index_table)
    
    # Filter uppercase words only
    uppercase_words = [
        str(row['word']).strip() 
        for _, row in df_sorted.iterrows()
        if str(row['word']).strip() and str(row['word']).strip()[0].isupper()
    ]
    uword_pages = defaultdict(list)
    for _, row in df_sorted.iterrows():
        uword = str(row['word']).strip()
        if uword and uword[0].isupper():
            for words_tuple, page_no in word_page_map.items():
                page_nos = []
                if uword in words_tuple:
                    page_nos.append(page_no)
                if page_nos is not None:
                    uword_pages[uword].extend(page_nos)

    # Sort words alphabetically
    usorted_words = sorted(uword_pages.keys())

    uindex_table_data = []
    first_uppercase = []

    # Split words into 3 columns
    ucol1, ucol2, ucol3 = [], [], []
    for i, uword in enumerate(usorted_words):
        # Format: word ..page1, page2, ...
        pages = ", ".join(str(p) for p in sorted(list(set(uword_pages[uword]))))
        if uword[0] not in first_uppercase:
            text = f"<b>{uword.replace("_", " ")}</b> – <i>{pages}</i>"
            first_uppercase.append(uword[0])
        else:
            text = f"{uword.replace("_", " ")} – <i>{pages}</i>"

        # Cycle through 3 columns
        if i % 3 == 0:
            ucol1.append(text)
        elif i % 3 == 1:
            ucol2.append(text)
        else:
            ucol3.append(text)

    # Make all columns the same length by padding with empty strings
    umax_len = max(len(ucol1), len(ucol2), len(ucol3))
    ucol1 += [""] * (umax_len - len(ucol1))
    ucol2 += [""] * (umax_len - len(ucol2))
    ucol3 += [""] * (umax_len - len(ucol3))

    # Combine into table rows
    for r in range(umax_len):
        uindex_table_data.append([Paragraph(ucol1[r], appendix_style),
                                Paragraph(ucol2[r], appendix_style),
                                Paragraph(ucol3[r], appendix_style)])

    # Add a page break and header
    story.append(PageBreak())
    story.append(Paragraph("Proper Nouns", instruction_title_style))
    story.append(Spacer(1, 0.2*inch))

    # Create the table
    uindex_table = Table(uindex_table_data, colWidths=[2.2*inch]*3)
    uindex_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(uindex_table)
    # --- BUILD PDF ---
    try:
        toc_last_page = 29  # adjust based on your story
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: NumberedCanvas(
                *args,
                language_abvr=language_abvr,
                start_numbering_after=toc_last_page,
                **kwargs
            )
        )


        print(f"PDF created: {output_pdf_path}")
    except Exception as e:
        print(f"PDF build error: {e}")

def main():
    DB_CONFIG = {
        "dbname": "sundb",
        "host": "localhost",
        "user": "postgres",
        "port": 5432,
        "password": getpass.getpass("Enter database password: ")
    }

    password = quote_plus(DB_CONFIG["password"])
    conn_str = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )

    engine = create_engine(conn_str)

    print("Generating PDF report...")
    language_id = 1
    language_name, language_abvr = get_language_name(engine, language_id)
    create_pdf_report(engine, f"SUN_Readers_Dictionary_Report_{language_abvr}.pdf", language_id)
    print("Done.")


if __name__ == "__main__":
    main()
