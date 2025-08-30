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
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        "POSTGRES_URL", 
        "postgresql://postgres.eyriqifciwpjrxlrkpgz:p6GT4JHiGqPwBiv2@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    
    @property
    def database_url(self) -> str:
        """Get database URL with proper scheme for SQLAlchemy"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        # Clean up invalid Supabase pooler parameters
        if "supa=" in url:
            # Remove the supa parameter and anything after it
            url = url.split("&supa=")[0]
        
        return url
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # VSDC API Configuration
    VSDC_API_URL = "http://localhost:8080/vsdc/trnsSales/saveSales"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # Email Configuration
    MAIL_HOST = os.getenv('MAIL_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'codebeta2500@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'sojc kfrh ozpt czlb')
    MAIL_FROM = os.getenv('MAIL_FROM', 'codebeta2500@gmail.com')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'VSDC Integration System')
    
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
    
    @property
    def mail_config(self) -> dict:
        return {
            'MAIL_HOST': self.MAIL_HOST,
            'MAIL_PORT': self.MAIL_PORT,
            'MAIL_USERNAME': self.MAIL_USERNAME,
            'MAIL_PASSWORD': self.MAIL_PASSWORD,
            'MAIL_FROM': self.MAIL_FROM,
            'MAIL_FROM_NAME': self.MAIL_FROM_NAME,
            'USE_CREDENTIALS': True,
            'VALIDATE_CERTS': True,
            'MAIL_STARTTLS': True,
            'MAIL_SSL_TLS': False
        }
    
    def is_mail_configured(self) -> bool:
        return bool(self.MAIL_USERNAME and self.MAIL_PASSWORD)

settings = Settings()
