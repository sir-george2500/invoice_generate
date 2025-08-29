from pathlib import Path
from jinja2 import FileSystemLoader, Environment
from weasyprint import HTML

class InvoiceGenerator:
    def __init__(self, template_dir="templates", assets_dir="assets", qr_generator=None):
        self.template_dir = Path(template_dir)
        self.assets_dir = Path(assets_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.qr_generator = qr_generator  # Add QR generator support
        
    def _get_template_name(self, invoice_data, template_name):
        """Determine the appropriate template based on invoice type"""
        # If template_name is explicitly provided, use it (backward compatibility)
        if template_name != "invoice_template.html":
            return template_name
            
        # Auto-detect template based on invoice_type in data
        invoice_type = invoice_data.get('invoice_type', '').lower()
        if invoice_type == 'credit note':
            return "credit_note_template.html"
        else:
            return "invoice_template.html"  # Default to invoice template
        
    def generate_pdf(self, invoice_data, output_path="output/pdf/invoice.pdf", template_name="invoice_template.html"):
        """Generate PDF invoice from template and data"""
        
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update image paths to be absolute file URLs
        invoice_data = self._update_asset_paths(invoice_data)
        
        # Determine the correct template to use
        actual_template_name = self._get_template_name(invoice_data, template_name)
        
        # Load and render template
        template = self.env.get_template(actual_template_name)
        html_content = template.render(**invoice_data)
        
        # CRITICAL: Set base_url to the template directory
        # This allows WeasyPrint to resolve relative paths correctly
        base_url = self.template_dir.resolve().as_uri() + "/"
        
        # Generate PDF with WeasyPrint
        html_doc = HTML(string=html_content, base_url=base_url)
        html_doc.write_pdf(target=str(output_path))
        
        print(f"PDF generated: {output_path}")
        return output_path
    
    def generate_pdf_with_qr(self, invoice_data, output_path="output/pdf/invoice.pdf", 
                            template_name="invoice_template.html", generate_qr=True, qr_type="url"):
        """Generate PDF with QR code generation and upload to Cloudinary
        
        Args:
            qr_type: "url" for RRA verification URL QR code, "text" for text-based QR code
        """
        
        # Generate QR code if requested and QR generator is available
        if generate_qr and self.qr_generator:
            print(f"Generating and uploading QR code ({qr_type}) to Cloudinary...")
            qr_result = self.qr_generator.generate_and_upload_qr(invoice_data, qr_type)
            
            if qr_result['success']:
                # Use Cloudinary URL directly for the QR code
                invoice_data['qr_code_path'] = qr_result['secure_url']
                invoice_data['qr_public_id'] = qr_result['public_id']  # Store for potential cleanup
                invoice_data['qr_verification_url'] = qr_result.get('verification_url')  # Store verification URL
                print(f"QR code uploaded to Cloudinary: {qr_result['secure_url']}")
                if qr_type == "url" and qr_result.get('verification_url'):
                    print(f"QR code links to: {qr_result['verification_url']}")
            else:
                print(f"QR generation failed: {qr_result['error']}")
                invoice_data['qr_code_path'] = None
        
        # Generate PDF using existing method
        return self.generate_pdf(invoice_data, output_path, template_name)
        
    def generate_html(self, invoice_data, output_path="output/html/invoice.html", template_name="invoice_template.html"):
        """Generate HTML preview"""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        invoice_data = self._update_asset_paths(invoice_data)
        
        # Determine the correct template to use
        actual_template_name = self._get_template_name(invoice_data, template_name)
        
        template = self.env.get_template(actual_template_name)
        html_content = template.render(**invoice_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML generated: {output_path}")
        return output_path
    
    def generate_html_with_qr(self, invoice_data, output_path="output/html/invoice.html", 
                             template_name="invoice_template.html", generate_qr=True, qr_type="url"):
        """Generate HTML preview with QR code
        
        Args:
            qr_type: "url" for RRA verification URL QR code, "text" for text-based QR code
        """
        
        # Generate QR code if requested and QR generator is available
        if generate_qr and self.qr_generator:
            print(f"Generating and uploading QR code ({qr_type}) to Cloudinary for HTML...")
            qr_result = self.qr_generator.generate_and_upload_qr(invoice_data, qr_type)
            
            if qr_result['success']:
                invoice_data['qr_code_path'] = qr_result['secure_url']
                invoice_data['qr_public_id'] = qr_result['public_id']
                invoice_data['qr_verification_url'] = qr_result.get('verification_url')
                print(f"QR code uploaded to Cloudinary: {qr_result['secure_url']}")
                if qr_type == "url" and qr_result.get('verification_url'):
                    print(f"QR code links to: {qr_result['verification_url']}")
            else:
                print(f"QR generation failed: {qr_result['error']}")
                invoice_data['qr_code_path'] = None
        
        # Generate HTML using existing method
        return self.generate_html(invoice_data, output_path, template_name)
    
    def generate_pdf_bytes(self, invoice_data, template_name="invoice_template.html"):
        """Generate PDF as bytes"""
        
        invoice_data = self._update_asset_paths(invoice_data)
        
        # Determine the correct template to use
        actual_template_name = self._get_template_name(invoice_data, template_name)
        
        template = self.env.get_template(actual_template_name)
        html_content = template.render(**invoice_data)
        
        # Set base_url for asset resolution
        base_url = self.template_dir.resolve().as_uri() + "/"
        html_doc = HTML(string=html_content, base_url=base_url)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
    
    def generate_pdf_bytes_with_qr(self, invoice_data, template_name="invoice_template.html", generate_qr=True, qr_type="url"):
        """Generate PDF as bytes with QR code from Cloudinary
        
        Args:
            qr_type: "url" for RRA verification URL QR code, "text" for text-based QR code
        """
        
        # Generate QR code if requested
        if generate_qr and self.qr_generator:
            print(f"Generating QR code ({qr_type}) for PDF bytes...")
            qr_result = self.qr_generator.generate_and_upload_qr(invoice_data, qr_type)
            
            if qr_result['success']:
                invoice_data['qr_code_path'] = qr_result['secure_url']
                invoice_data['qr_public_id'] = qr_result['public_id']
                invoice_data['qr_verification_url'] = qr_result.get('verification_url')
            else:
                invoice_data['qr_code_path'] = None
        
        # Update paths and generate PDF bytes
        invoice_data = self._update_asset_paths(invoice_data)
        
        # Determine the correct template to use
        actual_template_name = self._get_template_name(invoice_data, template_name)
        
        template = self.env.get_template(actual_template_name)
        html_content = template.render(**invoice_data)
        
        base_url = self.template_dir.resolve().as_uri() + "/"
        html_doc = HTML(string=html_content, base_url=base_url)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes, invoice_data.get('qr_public_id')  # Return public_id for cleanup if needed
    
    # Additional convenience methods for credit notes
    def generate_credit_note_pdf(self, invoice_data, output_path="output/pdf/credit_note.pdf", generate_qr=True):
        """Generate credit note PDF - convenience method"""
        invoice_data['invoice_type'] = 'Credit Note'
        return self.generate_pdf_with_qr(
            invoice_data, 
            output_path, 
            template_name="credit_note_template.html", 
            generate_qr=generate_qr
        )
    
    def generate_credit_note_html(self, invoice_data, output_path="output/html/credit_note.html", generate_qr=True):
        """Generate credit note HTML - convenience method"""
        invoice_data['invoice_type'] = 'Credit Note'
        return self.generate_html_with_qr(
            invoice_data, 
            output_path, 
            template_name="credit_note_template.html", 
            generate_qr=generate_qr
        )
    
    def _update_asset_paths(self, invoice_data):
        """Convert image paths to absolute file URLs for WeasyPrint, keep Cloudinary URLs as-is"""
        data = invoice_data.copy()
        
        # Handle local images (company logo and rwanda seal)
        if 'company_logo_path' in data and data['company_logo_path']:
            if not data['company_logo_path'].startswith('http'):
                logo_path = self.assets_dir / "images" / data['company_logo_path']
                if logo_path.exists():
                    data['company_logo_path'] = logo_path.resolve().as_uri()
            
        if 'rwanda_seal_path' in data and data['rwanda_seal_path']:
            if not data['rwanda_seal_path'].startswith('http'):
                seal_path = self.assets_dir / "images" / data['rwanda_seal_path']
                if seal_path.exists():
                    data['rwanda_seal_path'] = seal_path.resolve().as_uri()
        
        # QR code path - if it's a Cloudinary URL (starts with http), keep as-is
        # WeasyPrint can handle external URLs directly
        if 'qr_code_path' in data and data['qr_code_path']:
            if data['qr_code_path'].startswith('http'):
                # It's already a Cloudinary URL - keep as-is
                pass
            else:
                # Local QR code file (fallback case)
                qr_path = self.assets_dir / "images" / data['qr_code_path']
                if qr_path.exists():
                    data['qr_code_path'] = qr_path.resolve().as_uri()
                else:
                    # File doesn't exist, remove the path
                    data['qr_code_path'] = None
            
        return data
    
    def cleanup_qr_code(self, public_id):
        """Clean up QR code from Cloudinary"""
        if self.qr_generator and public_id:
            success = self.qr_generator.delete_qr_from_cloudinary(public_id)
            if success:
                print(f"QR code {public_id} deleted from Cloudinary")
                return True
            else:
                print(f"Failed to delete QR code {public_id}")
                return False
        return False
