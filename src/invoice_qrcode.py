import qrcode
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
from io import BytesIO
from pyzbar import pyzbar
import cv2
import numpy as np
import requests

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
        """Generate QR code data from invoice information in the specific VSDC format"""
        # Format the QR data exactly as specified by the using the same information that was place in the vsdc return jason 
        qr_text = f"""{invoice_data.get("client_name", "Unknown Client")}
Date :{invoice_data.get("invoice_date", "")}  Time:{invoice_data.get("invoice_time", "")}
SDC ID :{invoice_data.get("sdc_id", "")}
RECEIPT NUMBER :         {invoice_data.get("vsdc_receipt_no", invoice_data.get("receipt_number", ""))}/{invoice_data.get("vsdc_receipt_no", invoice_data.get("receipt_number", ""))}NS
Internal Data :
{invoice_data.get("vsdc_internal_data", "")}
Receipt Signature :
{invoice_data.get("vsdc_receipt_signature", "")}
--------------------------------
RECEIPT NUMBER :              {invoice_data.get("original_invoice_number", invoice_data.get("invoice_number", ""))}
Date:{invoice_data.get("invoice_date", "")}  Time:{invoice_data.get("vsdc_receipt_date", invoice_data.get("invoice_time", ""))}
MRC: {invoice_data.get("mrc", "")}"""
        
        return qr_text

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
    def validate_qr_content(self, qr_image_or_url, expected_invoice_data):
        """Validate that the QR code contains the expected invoice information"""
        try:
            # Decode QR code from image or URL
            qr_text = self.decode_qr_code(qr_image_or_url)
            
            if not qr_text:
                return {
                    'valid': False,
                    'error': 'Could not decode QR code'
                }
            
            # Parse the expected format and validate
            validation_result = self._validate_qr_format(qr_text, expected_invoice_data)
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }
    
    def decode_qr_code(self, qr_image_or_url):
        """Decode QR code from PIL Image, file path, or URL"""
        try:
            # Handle different input types
            if isinstance(qr_image_or_url, str):
                if qr_image_or_url.startswith('http'):
                    # Download from URL
                    response = requests.get(qr_image_or_url)
                    qr_image = Image.open(BytesIO(response.content))
                else:
                    # Load from file path
                    qr_image = Image.open(qr_image_or_url)
            else:
                # Assume it's already a PIL Image
                qr_image = qr_image_or_url
            
            # Convert PIL image to OpenCV format for pyzbar
            cv_image = cv2.cvtColor(np.array(qr_image), cv2.COLOR_RGB2BGR)
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(cv_image)
            
            if decoded_objects:
                # Return the data from the first QR code found
                return decoded_objects[0].data.decode('utf-8')
            else:
                return None
                
        except Exception as e:
            print(f"Error decoding QR code: {e}")
            return None
    
    def _validate_qr_format(self, qr_text, expected_data):
        """Validate the QR text against expected invoice data"""
        validation_results = {
            'valid': True,
            'matches': {},
            'mismatches': {},
            'missing_fields': []
        }
        
        # Define the fields to validate
        validation_fields = {
            'client_name': expected_data.get('client_name', ''),
            'invoice_date': expected_data.get('invoice_date', ''),
            'invoice_time': expected_data.get('invoice_time', ''),
            'sdc_id': expected_data.get('sdc_id', ''),
            'vsdc_receipt_no': expected_data.get('vsdc_receipt_no', expected_data.get('receipt_number', '')),
            'vsdc_internal_data': expected_data.get('vsdc_internal_data', ''),
            'vsdc_receipt_signature': expected_data.get('vsdc_receipt_signature', ''),
            'mrc': expected_data.get('mrc', '')
        }
        
        # Check each field
        for field, expected_value in validation_fields.items():
            if not expected_value:
                continue  # Skip empty expected values
                
            if field == 'client_name':
                # Client name should be at the beginning
                if qr_text.startswith(expected_value):
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'found': qr_text.split('\n')[0] if '\n' in qr_text else 'Not found'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'invoice_date':
                search_pattern = f"Date :{expected_value}"
                if search_pattern in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'pattern_searched': search_pattern,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'invoice_time':
                search_pattern = f"Time:{expected_value}"
                if search_pattern in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'pattern_searched': search_pattern,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'sdc_id':
                search_pattern = f"SDC ID :{expected_value}"
                if search_pattern in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'pattern_searched': search_pattern,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'vsdc_receipt_no':
                search_patterns = [
                    f"RECEIPT NUMBER :         {expected_value}/{expected_value}NS",
                    f"RECEIPT NUMBER :              {expected_value}"
                ]
                found = False
                for pattern in search_patterns:
                    if pattern in qr_text:
                        validation_results['matches'][field] = expected_value
                        found = True
                        break
                
                if not found:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'patterns_searched': search_patterns,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'vsdc_internal_data':
                if expected_value in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'vsdc_receipt_signature':
                if expected_value in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
                    
            elif field == 'mrc':
                search_pattern = f"MRC: {expected_value}"
                if search_pattern in qr_text:
                    validation_results['matches'][field] = expected_value
                else:
                    validation_results['mismatches'][field] = {
                        'expected': expected_value,
                        'pattern_searched': search_pattern,
                        'found': 'Not found in QR text'
                    }
                    validation_results['valid'] = False
        
        # Store the actual QR text for debugging
        validation_results['qr_text'] = qr_text
        
        return validation_results
    
    def validate_generated_qr(self, invoice_data):
        """Generate QR code and immediately validate it contains correct data"""
        try:
            # Generate the QR code
            qr_result = self.generate_and_upload_qr(invoice_data)
            
            if not qr_result['success']:
                return {
                    'valid': False,
                    'error': f'QR generation failed: {qr_result["error"]}'
                }
            
            # Download and validate the generated QR code
            validation_result = self.validate_qr_content(qr_result['secure_url'], invoice_data)
            
            # Add QR generation info to the result
            validation_result['qr_url'] = qr_result['secure_url']
            validation_result['public_id'] = qr_result['public_id']
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation process failed: {str(e)}'
            }
