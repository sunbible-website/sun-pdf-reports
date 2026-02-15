#!/usr/bin/env python3

from database.connection import get_engine
from pdf.builder import create_pdf_report
from services.language import get_language_name
import logging

def main():

    engine = get_engine()

    logger = logging.getLogger(__name__)
    logger.info("Generating PDF...")
    language_id = 1
    language_name, language_abvr = get_language_name(engine, language_id)
    create_pdf_report(engine, f"SUN_Readers_Dictionary_Report_{language_abvr}.pdf", language_id)
    logger.info(f"Done generating {language_name} report.")

if __name__ == "__main__":
    main()