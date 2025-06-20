import os
from pathlib import Path
from jinja2 import Template, FileSystemLoader, Environment
from weasyprint import HTML

class InvoiceGenerator:
    def __init__(self, template_dir="templates", assets_dir="assets"):
        self.template_dir = Path(template_dir)
        self.assets_dir = Path(assets_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
    def generate_pdf(self, invoice_data, output_path="output/pdf/invoice.pdf", template_name="invoice_template.html"):
        """Generate PDF invoice from template and data"""
        
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update image paths to be absolute file URLs
        invoice_data = self._update_asset_paths(invoice_data)
        
        # Load and render template
        template = self.env.get_template(template_name)
        html_content = template.render(**invoice_data)
        
        # CRITICAL: Set base_url to the template directory
        # This allows WeasyPrint to resolve relative paths correctly
        base_url = self.template_dir.resolve().as_uri() + "/"
        
        # Generate PDF with WeasyPrint
        html_doc = HTML(string=html_content, base_url=base_url)
        html_doc.write_pdf(target=str(output_path))
        
        print(f"PDF generated: {output_path}")
        return output_path
        
    def generate_html(self, invoice_data, output_path="output/html/invoice.html", template_name="invoice_template.html"):
        """Generate HTML preview"""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        invoice_data = self._update_asset_paths(invoice_data)
        
        template = self.env.get_template(template_name)
        html_content = template.render(**invoice_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML generated: {output_path}")
        return output_path
    
    def generate_pdf_bytes(self, invoice_data, template_name="invoice_template.html"):
        """Generate PDF as bytes"""
        
        invoice_data = self._update_asset_paths(invoice_data)
        template = self.env.get_template(template_name)
        html_content = template.render(**invoice_data)
        
        # Set base_url for asset resolution
        base_url = self.template_dir.resolve().as_uri() + "/"
        html_doc = HTML(string=html_content, base_url=base_url)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
    
    def _update_asset_paths(self, invoice_data):
        """Convert image paths to absolute file URLs for WeasyPrint"""
        data = invoice_data.copy()
        
        # Convert to absolute file URLs that WeasyPrint can understand
        if 'company_logo_path' in data:
            logo_path = self.assets_dir / "images" / data['company_logo_path']
            data['company_logo_path'] = logo_path.resolve().as_uri()
            
        if 'rwanda_seal_path' in data:
            seal_path = self.assets_dir / "images" / data['rwanda_seal_path']
            data['rwanda_seal_path'] = seal_path.resolve().as_uri()
            
        if 'qr_code_path' in data and data['qr_code_path']:
            qr_path = self.assets_dir / "images" / data['qr_code_path']
            data['qr_code_path'] = qr_path.resolve().as_uri()
            
        return data
