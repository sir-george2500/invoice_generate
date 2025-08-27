import os
from pathlib import Path
"""
Application Configuration
"""
import os
from dotenv import load_dotenv


load_dotenv()
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


class Settings:
    """Application settings"""
    
    # VSDC API Configuration
    VSDC_API_URL = "http://localhost:8080/vsdc/trnsSales/saveSales"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # Company Information
    COMPANY_NAME = "KABISA ELECTRIC Ltd"
    COMPANY_ADDRESS = "KIGALI CITY NYARUGENGE NYARUGENGE Nyarugenge"
    COMPANY_TEL = "0785757324"
    COMPANY_EMAIL = "finance@gokabisa.com"
    COMPANY_TIN = "120732779"
    
    # VSDC Configuration
    VSDC_TIN = "944000008"
    VSDC_BHF_ID = "00"
    VSDC_SDC_ID = "SDC010053151"
    VSDC_MRC = "WIS00058003"
    
    # QR Code Configuration
    QR_CODE_TYPE = os.getenv('QR_CODE_TYPE', 'text')  # 'url' for RRA verification URL (production only), 'text' for text-based
    RRA_VERIFICATION_BASE_URL = "https://myrra.rra.gov.rw/common/link/ebm/receipt/indexEbmReceiptData"
    
    @property
    def cloudinary_config(self) -> dict:
        return {
            'cloud_name': self.CLOUDINARY_CLOUD_NAME,
            'api_key': self.CLOUDINARY_API_KEY,
            'api_secret': self.CLOUDINARY_API_SECRET
        }
    
    def is_cloudinary_configured(self) -> bool:
        return all(self.cloudinary_config.values())

settings = Settings()
