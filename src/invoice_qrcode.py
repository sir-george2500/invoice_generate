import qrcode
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
from io import BytesIO

class InvoiceQRGenerator:
    def __init__(self, cloudinary_config):
        """
        Initialize QR Generator with Cloudinary configuration
        
        cloudinary_config = {
            'cloud_name': 'your_cloud_name',
            'api_key': 'your_api_key',
            'api_secret': 'your_api_secret'
        }
        """
        # Configure Cloudinary
        cloudinary.config(**cloudinary_config)
        
    def generate_invoice_qr_data(self, invoice_data):
        """Generate QR code data from invoice information"""
        qr_data = {
            "invoice_number": invoice_data.get("invoice_number"),
            "company_name": invoice_data.get("company_name"),
            "company_tin": invoice_data.get("company_tin"),
            "client_name": invoice_data.get("client_name"),
            "client_tin": invoice_data.get("client_tin"),
            "invoice_date": invoice_data.get("invoice_date"),
            "total_amount": invoice_data.get("total_rwf"),
            "total_tax": invoice_data.get("total_tax"),
            "sdc_id": invoice_data.get("sdc_id"),
            "receipt_number": invoice_data.get("receipt_number")
        }
        
        # Convert to JSON string for QR code
        return json.dumps(qr_data, separators=(',', ':'))

    def create_qr_code_image(self, data, size=(300, 300)):
        """Create QR code image from data"""
        qr = qrcode.QRCode(
            version=1,  # Controls size (1 is smallest)
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create PyPNG image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert PyPNGImage to PIL Image
        img_byte_array = BytesIO()
        qr_image.save(img_byte_array)
        img_byte_array.seek(0)
        qr_image = Image.open(img_byte_array)
        
        # Resize if needed
        if size:
            qr_image = qr_image.resize(size, Image.Resampling.LANCZOS)
            
        return qr_image
    def upload_to_cloudinary(self, qr_image, invoice_number):
        """Upload QR code image to Cloudinary"""
        try:
            # Convert PIL image to bytes
            img_byte_array = BytesIO()
            qr_image.save(img_byte_array, format='PNG')
            img_byte_array.seek(0)
            
            # Upload to Cloudinary
            public_id = f"invoice_qr_codes/invoice_{invoice_number}_qr"
            
            upload_result = cloudinary.uploader.upload(
                img_byte_array.getvalue(),
                public_id=public_id,
                resource_type="image",
                format="png",
                overwrite=True,
                folder="invoice_qr_codes",
                # Optional: Set transformations for optimization
                transformation=[
                    {'width': 300, 'height': 300, 'crop': 'fit'},
                    {'quality': 'auto', 'format': 'png'}
                ]
            )
            
            return {
                'success': True,
                'url': upload_result['secure_url'],
                'public_id': upload_result['public_id'],
                'cloudinary_url': upload_result['url']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_and_upload_qr(self, invoice_data):
        """Complete process: Generate QR -> Upload to Cloudinary -> Return URL"""
        try:
            # Step 1: Generate QR data
            qr_data = self.generate_invoice_qr_data(invoice_data)
            
            # Step 2: Create QR code image
            qr_image = self.create_qr_code_image(qr_data)
            
            # Step 3: Upload to Cloudinary
            upload_result = self.upload_to_cloudinary(qr_image, invoice_data['invoice_number'])
            
            if not upload_result['success']:
                return {
                    'success': False,
                    'error': f"Upload failed: {upload_result['error']}"
                }
            
            return {
                'success': True,
                'cloudinary_url': upload_result['url'],
                'secure_url': upload_result['url'],
                'public_id': upload_result['public_id'],
                'qr_data': qr_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_qr_from_cloudinary(self, public_id):
        """Delete QR code from Cloudinary (cleanup)"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result['result'] == 'ok'
        except Exception as e:
            print(f"Error deleting QR code: {e}")
            return False
