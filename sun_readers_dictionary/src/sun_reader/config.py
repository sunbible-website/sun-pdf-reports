from reportlab.lib.pagesizes import letter, A4
from pathlib import Path
import os

# --------------------------------------------------
# Base Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"

SVG_FOLDER = ASSETS_DIR / "svg-symbols"



# --------------------------------------------------
# PDF Settings
# --------------------------------------------------

MAX_ROWS_PER_PAGE = 42
# adjust if TOC length changes
TOC_LAST_PAGE = 2


# --------------------------------------------------
# Default App Settings
# --------------------------------------------------

DEFAULT_LANGUAGE_ID = 1 # will update this to either use CLI args or config file

# --------------------------------------------------
# Database Configuration (Non-sensitive)
# --------------------------------------------------

class Config:
    DB_NAME = os.environ.get("SUN_DB_NAME", "sundb")
    DB_HOST = os.environ.get("SUN_DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("SUN_DB_PORT", 5432))
    DB_USER = os.environ.get("SUN_DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("SUN_DB_PASSWORD")
    
    if DB_PASSWORD is None:
        raise ValueError("Environment variable SUN_DB_PASSWORD is not set.")
    
    
# --------------------------------------------------
# Page Layout Settings
# --------------------------------------------------

PAGE_SIZES = {
    "letter": letter,
    "A4": A4,
    # custom sizes as tuples (width, height)
    "custom": (500, 700),
}

PAGE_MARGINS = {
    "letter": (72,72,72,72),
    "A4": (72,72,72,72),
    "custom": (50,50,50,50)
    
}