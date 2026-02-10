# Technical Documentation: SUN Reader's Dictionary PDF Generator

## 1. Project Overview
This project is a Python-based application designed to generate the **Symbolic Universal Notation (SUN) Reader's Dictionary** in PDF format. It automates the layout of complex dictionary data, including text, SVG symbols, and dynamic indices.

The system uses **ReportLab** for PDF generation, **Pandas** for data manipulation, and **SQLAlchemy** for database interaction. 

## 2. Prerequisites & Dependencies

### 2.1. Core Libraries
*   **ReportLab**: The engine for creating PDFs. Used for low-level drawing (Canvas) and high-level layout (Platypus Flowables).
*   **Svglib**: Converts SVG files (vector graphics) into ReportLab `Drawing` objects. Essential for rendering the SUN symbols.
*   **Pandas**: Handles the SQL data as DataFrames, allowing for easy sorting, grouping, and cleaning before rendering.
*   **SQLAlchemy / Psycopg2**: Manages the PostgreSQL database connection.

### 2.2. Environment Setup
The application relies on a `.env` file for configuration. Required variables:
*   **Database**: `DB_NAME`, `DB_HOST`, `DB_USER`, `DB_PORT`, `DB_PASSWORD`.
*   **Fonts**: `FONT_PATH` (Regular), `FONT_BOLD_PATH`, `FONT_ITALIC_PATH`, `FONT_BOLD_ITALIC_PATH`.

## 3. Architecture & Workflow

The application follows a linear pipeline:

1.  **Initialization**: `main.py` loads environment variables, registers custom fonts with ReportLab, and connects to the DB.
2.  **Data Retrieval**: SQL queries fetch dictionary entries, joined with language-specific data.
3.  **Story Assembly**: The `PDFReportGenerator` converts raw data into a list of ReportLab "Flowables" (Paragraphs, Tables, Images).
4.  **Multi-Pass Build**: The PDF engine runs multiple passes (usually 2-3) to resolve dynamic elements like the TOC.
5.  **Rendering**: The final PDF is written to disk.

## 4. Database Interaction (`data_query.py`)

The system queries a specific schema (`sun`) in PostgreSQL. The core query joins four tables to construct the view:

*   **`sun.readers`**: Defines the Section (e.g., "MAN") and Subsection structure.
*   **`sun.readersdetail`**: Maps individual words to specific Sections and defines the order (`pageorderby`).
*   **`sun.wordlists`**: The central dictionary table containing the Word, its SVG filename (`unicode_id_id`), Related Meanings, and "Made From" components.
*   **`sun.language`**: Used to localize section names and fetch UI strings (e.g., Cover Page text).

## 5. Directory Structure & Components

```text
root/
├── main.py                     # Entry point (CLI & DB setup)
├── data_query.py               # SQL queries
├── utils.py                    # Helper functions (SVG loading, string cleaning)
├── configs/
│   ├── report_styles.py        # Centralized visual styles (Fonts, TableStyles)
│   └── report_config.py        # Constants (Paths, Fonts)
├── pdf_elements/
│   ├── pdf_report_generator.py # Main orchestration logic
│   ├── table_of_contents.py    # Dynamic TOC logic (Multi-pass listener)
│   ├── header.py               # Section headers (Text + SVG)
│   ├── footer.py               # Page footer (Page numbers, Date, Language)
│   ├── word_table.py           # Main dictionary content grid
│   ├── inline_example.py       # Mixed text/SVG renderer
│   ├── cover_page.py           # Front cover
│   ├── instructions_page.py    # Static instruction text
│   └── word_index.py           # Alphabetical index at end of book
```

## 6. Component Deep Dive

### 6.1. The Table of Contents System (`table_of_contents.py`)
This is the most complex component, utilizing a multi-build mechanism to resolve page numbers.

1.  **`TOCReportingDocTemplate`**: A custom document template. It overrides `afterFlowable()`. Every time it draws an element, it checks if that element has a `toc_entry` attribute. If so, it broadcasts a notification containing the current page number.
2.  **`TableOfContents` (Flowable)**:
    *   **`isIndexing()`**: Returns `True`, registering itself as a listener.
    *   **`notify()`**: Collects `(page, name, icon)` data during the build pass.
    *   **`isSatisfied()`**: Compares data collected in the *current* pass vs. the *previous* pass. If they differ, it forces ReportLab to restart the build from page 1.
    *   **`draw()`**: In the final pass, it uses the stabilized data to render the visual table.
    *   **`split()`/`wrap()`**: Essential for allowing the TOC to span multiple pages.

### 6.2. SVG Handling (`utils.py`)
*   **`load_and_scale_svg`**: This function is critical for visual consistency. It reads an SVG file and scales it to fit within a bounding box (e.g., 0.5 inch square) while **preserving the aspect ratio**. This prevents symbols from looking stretched or squashed.

### 6.3. Word Table (`word_table.py`)
Renders the actual dictionary entries.
*   **Layout Algorithm**: Uses a **column-major** layout. If there are 3 columns and 10 items, it calculates how to fill Column 1 (rows 0-3), then Column 2 (rows 0-3), etc., rather than filling Row 1 then Row 2.
*   **Nested Tables**: Each cell is actually a nested Table containing the Symbol (SVG) and the Word details side-by-side. This ensures perfect vertical alignment of the icon relative to the text block.

## 7. Styles & Configuration

*   **`configs/report_styles.py`**: Contains all `ParagraphStyle` and `TableStyle` definitions.
    *   **`toc_style`**: Defines the specific look of the TOC (single line below header, centered symbol column).
*   **Font Registration (`main.py`)**: The application does not assume system fonts. It explicitly registers `.ttf` files provided in the `.env` configuration. If fonts fail to load, it falls back to standard fonts to prevent crashing.

## 8. Usage

```bash
# Standard English generation
python main.py --language 1 --output output.pdf
# Spanish version
python main.py --language 10 --outputSpanish output.pdf

# Single column layout (Large print)
python main.py --layout single

```

## 9. Troubleshooting

*   **Missing SVGs**: If an SVG is missing from the `svg-symbols` folder, the `utils.load_and_scale_svg` function catches the error and returns `None` (or a Spacer), preventing the entire PDF generation from failing. Warnings are printed to the console.
*   **Font Errors**: If the paths in `.env` are incorrect, the system will print a warning and use the default ReportLab fonts (Helvetica/Times).
*   **TOC Loops**: In very rare cases, adding the TOC might shift content enough to change page numbers, which updates the TOC, which shifts content back. ReportLab handles this loop detection, but ensure TOC styles are consistent to avoid infinite "jitter."
