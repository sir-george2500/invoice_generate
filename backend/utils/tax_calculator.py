"""
Tax Calculation Utilities
"""


def calculate_tax(price: float, tax_rate: float = 18.0) -> float:
    """Calculate tax using dynamic tax rate with backwards compatibility"""
    if tax_rate == 0:
        return 0.0
    return round(price * tax_rate / (100 + tax_rate), 2)

def validate_required_fields(zoho_payload: dict) -> None:
    """Validate required fields from Zoho payload"""
    # Extract invoice data (Zoho nests data in 'invoice' object)
    invoice_data = zoho_payload.get("invoice", zoho_payload)
    
    # Check for invoice number - this is critical
    invoice_no = invoice_data.get("invoice_number")
    if not invoice_no or (isinstance(invoice_no, str) and invoice_no.strip() == ""):
        raise ValueError("Invoice number must be a non-empty string")
    
    # Check for line items
    items = invoice_data.get("line_items", [])
    if not items:
        raise ValueError("Invoice must contain at least one line item")
    
    # Validate each item has required fields
    for idx, item in enumerate(items):
        item_name = item.get("name") or item.get("description", "")
        if not item_name.strip():
            raise ValueError(f"Item {idx + 1} must have a name or description")
        if not item.get("rate") or float(item.get("rate", 0)) <= 0:
            raise ValueError(f"Item {idx + 1} must have a valid rate/price")




def extract_vat_from_inclusive_price(price: float, vat_rate: float) -> float:
    """
    Extract VAT from inclusive price using the formula:
    VAT = price * vat_rate / (100 + vat_rate)
    
    Args:
        price: The inclusive price
        vat_rate: The VAT rate as a percentage (e.g., 18 for 18%)
    
    Returns:
        The VAT amount
    """
    return round(price * vat_rate / (100 + vat_rate), 2)

def calculate_exclusive_price(inclusive_price: float, vat_rate: float) -> float:
    """
    Calculate exclusive price from inclusive price
    
    Args:
        inclusive_price: Price including VAT
        vat_rate: VAT rate as percentage
    
    Returns:
        Price excluding VAT
    """
    return round(inclusive_price / (1 + vat_rate/100), 2)

def calculate_vat_amount(exclusive_price: float, vat_rate: float) -> float:
    """
    Calculate VAT amount from exclusive price
    
    Args:
        exclusive_price: Price excluding VAT
        vat_rate: VAT rate as percentage
    
    Returns:
        VAT amount
    """
    return round(exclusive_price * vat_rate / 100, 2)

def get_tax_category(vat_rate: float) -> str:
    """
    Determine tax category based on VAT rate
    
    Args:
        vat_rate: VAT rate as percentage
    
    Returns:
        Tax category ('A' for 0%, 'B' for 18%, 'C' for other rates, 'D' for special cases)
    """
    if vat_rate == 0:
        return 'A'  # VAT_Exempt, VAT_Zero_Rated, Special_Rate
    elif vat_rate == 18:
        return 'B'  # VAT_Standard
    else:
        return 'C'  # Other tax rates
