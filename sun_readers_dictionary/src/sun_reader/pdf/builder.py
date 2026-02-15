from database.queries import READERS_QUERY
from services.language import get_language_name
from pdf.flowables import *
from config import SVG_FOLDER, MAX_ROWS_PER_PAGE, TOC_LAST_PAGE
from pdf.utils import *
from utils import clean
import pandas as pd
from reportlab.platypus import Paragraph, Spacer, Table, PageBreak
from pdf.canvas import *
from collections import defaultdict
import math
import os


def create_pdf_report(engine, output_pdf_path, language_id):
    """Create a PDF report from sun schema SQL tables with SVG symbols."""
    # --- READ DATA ---
    try:
        query = READERS_QUERY
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
    doc = build_doc(output_pdf_path)

    toc_placeholder_index = toc() # add TOC header and placeholder
   

    # --- SORT & GROUP ---
    df_sorted = df.sort_values(["pdforderby", "pageorderby"])
    
    
    # Keep track of which words appear on which pages
    word_page_map = {}
    current_page_number = 1
    count = 0
    toc_sections = {}
    
    
    for pdf_order, group_data in df_sorted.groupby("pdforderby"):
        first = group_data.iloc[0]

        # --- HEADER: symbol + section + subsection ---
        section_name = clean(first["sectionname"])
        subsection_name = clean(first["subsectionname"])
        header_text = section_name
        toc_section_name = section_name
        if subsection_name:
            header_text = subsection_name + " - " + section_name
            toc_section_name = subsection_name
        
        if section_name.lower() == "proper nouns":
            toc_section_name = section_name + " " +  subsection_name

        first_svg_file = f"{str(first['sectionunicode']).strip()}.svg"
        if not subsection_name:
            first_svg_path = os.path.join(SVG_FOLDER, first_svg_file)
        else:
            first_svg_path = ""
        
        if toc_section_name not in toc_sections.keys():
            start_page_number = current_page_number
            
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
                            # if row['related_meaning']:
                            #     all_words = [str(row['related_meaning']).strip()]
                            # else:
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
                table_style(table)
                
                # if words_on_page does not exist in map, add it
                if tuple(words_on_page) not in word_page_map.keys():
                    word_page_map[tuple(words_on_page)] = current_page_number
                else:
                    word_page_map[tuple(words_on_page)+(str(count),)] = current_page_number
                story.append(table)
                story.append(PageBreak())
                current_page_number += 1  # increment page counter for TOC
                count += 1
                toc_sections[toc_section_name] = (start_page_number, current_page_number)

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
    
    # Get the first page words and page number
    first_page_words_tuple = next(iter(word_page_map.keys()))
    words_on_first_page = list(dict.fromkeys(first_page_words_tuple))
    
    page_no = word_page_map[first_page_words_tuple]
    
    sections_in_order = words_on_first_page + list(toc_sections.keys())[1:]
  

    for i in range(0, len(sections_in_order), 2):
        row_cells = []
        for j in range(2):
            if i + j < len(sections_in_order):
                section_name = sections_in_order[i + j]
                if section_name not in toc_sections.keys():
                    start = page_no
                    end = page_no
                else:
                    start, end = toc_sections[section_name]
                
                end -= 1
                if start >= end:
                    page_text = f"{start}"
                else:
                    page_text = f"{start} - {end}"
                
                # if section_name.split()[-1].strip().replace("-","").lower() not in word_to_svg:
                #     print("NO SYMBOL FOR:", section_name.split()[-1].strip().replace("-","").lower())

                # Optional: include symbol
                symbol = small_svg_for_word(section_name.split()[-1].strip().replace("-","").lower(), word_to_svg, svg_folder=SVG_FOLDER, size=0.25*inch)
                
                if not symbol:
                    symbol = Paragraph("", detail_style)
                    
                row_cells.extend([
                    Paragraph(section_name.title(), detail_style),
                    symbol,
                    Paragraph(page_text, detail_style)
                ])
            else:
                row_cells.extend([Paragraph("", detail_style), Paragraph("", detail_style), Paragraph("", detail_style)])
        toc_table_data.append(row_cells)


    # Build table and replace placeholder
    toc_table = Table(toc_table_data, colWidths=[1.8*inch, 0.7*inch, 0.7*inch]*2)
    table_style(toc_table, padding=(4,4,2,2))
    story[toc_placeholder_index] = toc_table

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
    table_style(index_table, padding=(4,4,2,2))
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
    table_style(uindex_table, padding=(4,4,2,2))
    story.append(uindex_table)
    
    # --- BUILD PDF ---
    buid_pdf(doc, language_abvr, TOC_LAST_PAGE, output_pdf_path)
