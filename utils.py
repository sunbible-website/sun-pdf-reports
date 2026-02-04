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
    """Sanitizes text fields from the database."""
    return str(value).strip() if pd.notna(value) and str(value).strip() else ""


def load_and_scale_svg(svg_filename, max_width, max_height):
    """
    Loads an SVG file and scales it to fit within the specified dimensions.
    Returns a reportlab Drawing object or None if the file is missing/invalid.
    """
    if not svg_filename:
        return None

    path = os.path.join(config.SVG_FOLDER, svg_filename)
    if not os.path.exists(path):
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
    except Exception:
        pass  # Gracefully handle corrupt or invalid SVGs
    return None
