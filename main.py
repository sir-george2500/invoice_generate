#!/usr/bin/env python3
"""
Example usage of the invoice generation system
"""
from src.invoice_generator import InvoiceGenerator
from src.models import Invoice, Company, Client, InvoiceItem
from src.invoice_qrcode import InvoiceQRGenerator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    """Main function to generate invoice with QR code"""
    
    # Create sample invoice
    invoice = create_sample_invoice()
    
    # Cloudinary configuration - use environment variables for security
    cloudinary_config = {
        'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME', 'your_cloud_name'),
        'api_key': os.getenv('CLOUDINARY_API_KEY', 'your_api_key'),
        'api_secret': os.getenv('CLOUDINARY_API_SECRET', 'your_api_secret')
    }
    
    # Initialize QR code generator
    qr_generator = InvoiceQRGenerator(cloudinary_config)
    
    # Initialize invoice generator with QR generator
    generator = InvoiceGenerator(qr_generator=qr_generator)
    
    # Convert invoice to dictionary
    invoice_data = invoice.to_dict()
    
    print(f"Generating invoice {invoice.invoice_number} with QR code...")
    
    try:
        # Generate PDF with QR code
        pdf_path = f"output/pdf/invoice_{invoice.invoice_number}.pdf"
        generator.generate_pdf_with_qr(invoice_data, pdf_path, generate_qr=True)
        
        # Generate HTML preview (optional - without QR for now)
        html_path = f"output/html/invoice_{invoice.invoice_number}.html"
        generator.generate_html(invoice_data, html_path)
        
        print("Invoice generation completed!")
        print(f"PDF: {pdf_path}")
        print(f"HTML: {html_path}")
        
        # Print QR code info if available
        if 'qr_code_path' in invoice_data:
            print(f"QR Code URL: {invoice_data['qr_code_path']}")
            print(f"QR Public ID: {invoice_data.get('qr_public_id', 'N/A')}")
        
    except Exception as e:
        print(f"Error generating invoice: {e}")
        
    # Optional: Generate just the QR code separately for testing
    try:
        print("\nGenerating standalone QR code for testing...")
        qr_result = qr_generator.generate_and_upload_qr(invoice_data)
        
        if qr_result['success']:
            print(f"QR Code generated successfully!")
            print(f"Cloudinary URL: {qr_result['secure_url']}")
            print(f"Public ID: {qr_result['public_id']}")
        else:
            print(f"QR Code generation failed: {qr_result['error']}")
            
    except Exception as e:
        print(f"Error generating QR code: {e}")

if __name__ == "__main__":
    main()
