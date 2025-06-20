#!/usr/bin/env python3
"""
Example usage of the invoice generation system
"""

from src.invoice_generator import InvoiceGenerator
from src.models import Invoice, Company, Client, InvoiceItem

def create_sample_invoice():
    """Create a sample invoice using the data models"""
    
    # Company information
    company = Company(
        name="KABISA ELECTRIC Ltd",
        address="KIGALI CITY NYARUGENGE NYARUGENGE Nyarugenge",
        tel="0785757324",
        email="finance@gokabisa.com",
        tin="120732779",
        cashier="admin(120732779)"
    )
    
    # Client information
    client = Client(
        name="ALSM ADVISORY LTD",
        tin="118692892"
    )
    
    # Invoice items
    items = [
        InvoiceItem(
            code="RW3NTXKWT0000001",
            description="EV Charging Services",
            quantity="87.4275",
            tax="B",
            unit_price="400",
            total_price="34,971"
        )
    ]
    
    # Create invoice
    invoice = Invoice(
        company=company,
        client=client,
        invoice_number="3565",
        invoice_date="15-06-2025",
        invoice_time="10:48:53",
        sdc_id="SDC010053151",
        receipt_number="3561/3561NS",
        mrc="WIS00058003",
        items=items,
        total_rwf="34,971.00",
        total_aex="0.00",
        total_b="34,971.00",
        total_tax_b="5,334.56",
        total_tax="5,334.56"
    )
    
    return invoice

def main():
    """Main function to generate invoice"""
    
    # Create sample invoice
    invoice = create_sample_invoice()
    
    # Initialize generator
    generator = InvoiceGenerator()
    
    # Generate PDF
    pdf_path = f"output/pdf/invoice_{invoice.invoice_number}.pdf"
    generator.generate_pdf(invoice.to_dict(), pdf_path)
    
    # Generate HTML preview
    html_path = f"output/html/invoice_{invoice.invoice_number}.html"
    generator.generate_html(invoice.to_dict(), html_path)
    
    print("Invoice generation completed!")

if __name__ == "__main__":
    main()
