import argparse
import os
import sys

from dotenv import load_dotenv
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import create_engine

# Ensure root directory is in sys.path
sys.path.append(os.getcwd())

from configs import report_config as config
from pdf_elements.pdf_report_generator import PDFReportGenerator
from utils import get_db_connection_string

# Load environment variables
load_dotenv()

# Register Font
font_path = os.getenv("FONT_PATH")
font_bold_path = os.getenv("FONT_BOLD_PATH")
font_italic_path = os.getenv("FONT_ITALIC_PATH")
font_bold_italic_path = os.getenv("FONT_BOLD_ITALIC_PATH")

try:
    if font_path:
        pdfmetrics.registerFont(TTFont(config.BASE_FONT, font_path))

    if font_bold_path:
        pdfmetrics.registerFont(TTFont(f"{config.BASE_FONT}-Bold", font_bold_path))

    if font_italic_path:
        pdfmetrics.registerFont(TTFont(f"{config.BASE_FONT}-Italic", font_italic_path))

    if font_bold_italic_path:
        pdfmetrics.registerFont(
            TTFont(f"{config.BASE_FONT}-BoldItalic", font_bold_italic_path)
        )

    pdfmetrics.registerFontFamily(
        config.BASE_FONT,
        normal=config.BASE_FONT,
        bold=f"{config.BASE_FONT}-Bold",
        italic=f"{config.BASE_FONT}-Italic",
        boldItalic=f"{config.BASE_FONT}-BoldItalic",
    )
except Exception as e:
    print(f"Warning: Could not register font: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate Reader's Dictionary PDF")
    parser.add_argument(
        "--language", type=int, default=1, help="Language ID (default: 1 for English)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="readersDictionaryReport.pdf",
        help="Output filename",
    )

    args = parser.parse_args()

    # Retrieve DB settings from .env
    dbname = os.getenv("DB_NAME")
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    port = int(os.getenv("DB_PORT", "5432"))
    password = os.getenv("DB_PASSWORD") or None

    db_url = get_db_connection_string(dbname, host, user, port, password)
    engine = create_engine(db_url)

    report_generator = PDFReportGenerator(engine, args.output, args.language)
    report_generator.generate()


if __name__ == "__main__":
    main()
