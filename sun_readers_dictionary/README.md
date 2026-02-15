# SUN Reader Dictionary PDF Generator

This project generates the **SUN Reader’s Dictionary** PDF from data stored in a PostgreSQL database.

It reads symbol and word data from the `sun` schema and produces a fully formatted dictionary with:

- Table of contents
- Sectioned symbol tables
- Word index
- Proper noun index
- Page numbering with custom footer

The PDF is generated using ReportLab and SVG symbol rendering.

---

## Requirements

- Python 3.10+
- PostgreSQL
- SVG symbol files
- `sun` database schema populated

---

## Installation

Clone the repository:

```bash
git clone https://github.com/sunbible-website/sun-pdf-reports.git
cd sun-reader-dictionary
```

### Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

```bash
export SUN_DB_PASSWORD=yourpassword
```

### SVG assets must exist in:

```bash
assets/svg-symbols/
```

## Running the Generator

```bash
cd src/sun_reader
python main.py
```

The generated PDF will be saved in `src\sun_reader` as:

```bash
SUN_Readers_Dictionary_Report_<LANG>.pdf
```

## Project Structure

```
src/sun_reader/
├── main.py             # Entry point
├── config.py           # App configuration
├── database/           # DB connection + queries
├── pdf/                # PDF generation logic
│   ├── builder.py
│   ├── canvas.py
│   ├── flowables.py
│   ├── styles.py
│   └── utils.py
├── services/           # Query logic
└── utils/              # Text helpers
```
