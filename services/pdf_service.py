"""
PDF Service - Handles PDF generation and file management
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PDFService:
    """Service to handle PDF generation and file operations"""
    
    def __init__(self):
        # Ensure output directories exist
        os.makedirs("output/pdf", exist_ok=True)
        os.makedirs("output/html", exist_ok=True)

    def list_generated_pdfs(self) -> list:
        """List all generated PDF files"""
        try:
            pdf_info = []
            
            # Check output directory
            if os.path.exists("output/pdf"):
                for pdf_file in os.listdir("output/pdf"):
                    if pdf_file.endswith('.pdf'):
                        pdf_path = os.path.join("output/pdf", pdf_file)
                        stat_info = os.stat(pdf_path)
                        pdf_info.append({
                            "filename": pdf_file,
                            "size": stat_info.st_size,
                            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                            "download_url": f"/download-pdf/{pdf_file}",
                            "location": "output/pdf"
                        })
            
            return pdf_info
        except Exception as e:
            logger.error(f"Error listing PDFs: {str(e)}")
            raise

    def get_pdf_path(self, filename: str) -> str:
        """Get the full path for a PDF file"""
        pdf_path = f"output/pdf/{filename}"
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            # Try temp directory as fallback
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            if os.path.exists(temp_path):
                return temp_path
            
            raise FileNotFoundError(f"PDF file not found: {filename}")

    def get_available_files(self) -> list:
        """Get list of available PDF files"""
        available_files = []
        if os.path.exists("output/pdf"):
            available_files = [f for f in os.listdir("output/pdf") if f.endswith('.pdf')]
        return available_files
