import os

import pandas as pd
from svglib.svglib import svg2rlg

from configs import report_config as config


def get_db_connection_string(dbname, host, user, port=5432, password=None):
    """Builds the SQLAlchemy connection string."""
    if password:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    return f"postgresql+psycopg2://{user}@{host}:{port}/{dbname}"


def clean_text(value):
    """
    Cleans text fields from the database.
    Removes whitespace and ensures we don't have "None" appear
    in the pdf.
    """
    return str(value).strip() if pd.notna(value) and str(value).strip() else ""


def load_and_scale_svg(svg_filename, max_width, max_height):
    """
    Loads an SVG file and scales it to fit within the specified dimensions.

    Example:
        If an SVG is 100x100 and max_width=50, max_height=50:
        - scale_w = 50/100 = 0.5
        - scale_h = 50/100 = 0.5
        - scale = 0.5
        Result: The drawing is resized to 50x50.

    Returns:
        Drawing: A ReportLab Drawing object resized to fit, or None if invalid.
    """
    if not svg_filename:
        print("Warning: load_and_scale_svg called with empty/None filename")
        return None

    path = os.path.join(config.SVG_FOLDER, svg_filename)
    if not os.path.exists(path):
        print(f"Warning: SVG file not found - {svg_filename}")
        return None

    try:
        drawing = svg2rlg(path)
        if drawing and drawing.height > 0 and drawing.width > 0:
            scale_w = max_width / drawing.width
            scale_h = max_height / drawing.height
            scale = min(scale_w, scale_h, 1)
            drawing.width *= scale
            drawing.height *= scale
            drawing.scale(scale, scale)
            return drawing
        else:
            print(
                f"Warning: SVG parsed but empty or invalid dimensions - {svg_filename}"
            )
    except Exception as e:
        print(f"Found a bad svg - {svg_filename}. Error: {e}")
        pass
    return None


def get_language_name(engine, language_id):
    """
    Fetches the language name from the database.
    """
    query = """
    SELECT name, language_abvr
    FROM sun.language
    WHERE language_id = %(language_id)s
    """
    df = pd.read_sql_query(query, engine, params={"language_id": language_id})

    if df.empty:
        raise ValueError(f"No language found for language_id={language_id}")

    return df.iloc[0]["name"]
