import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Directory paths
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
PDF_OUTPUT_DIR = OUTPUT_DIR / "pdf"
HTML_OUTPUT_DIR = OUTPUT_DIR / "html"

# PDF generation settings
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '2cm',
    'margin-right': '2cm',
    'margin-bottom': '2cm',
    'margin-left': '2cm',
    'encoding': "UTF-8",
    'no-outline': None,
    'enable-local-file-access': None
}

# Default file names
DEFAULT_TEMPLATE = "invoice_template.html"
COMPANY_LOGO = "somelogo.png"
RWANDA_SEAL = "seaRR.png"
