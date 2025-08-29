"""
Custom Exception Classes
"""

class VSSDCError(Exception):
    """Base exception for VSDC related errors"""
    pass

class PayloadValidationError(VSSDCError):
    """Raised when payload validation fails"""
    pass

class TaxCalculationError(VSSDCError):
    """Raised when tax calculation fails"""
    pass

class PDFGenerationError(VSSDCError):
    """Raised when PDF generation fails"""
    pass

class VSSDCAPIError(VSSDCError):
    """Raised when VSDC API call fails"""
    pass
