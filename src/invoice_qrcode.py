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
        """Generate QR code data as complete receipt text
        
        Note: RRA verification URLs only work in production environment.
        Using complete receipt text format for better compatibility.
        """
        # Use text-based QR code with complete receipt information
        return self.generate_invoice_qr_data_text_fallback(invoice_data)
    
    def generate_invoice_qr_data_text_fallback(self, invoice_data):
        """Generate QR code data with only essential SDC information"""
        
        # Get receipt number - try different sources
        vsdc_receipt_no = invoice_data.get("vsdc_receipt_no", invoice_data.get("receipt_number", ""))
        invoice_number = invoice_data.get("invoice_number_numeric", invoice_data.get("invoice_number", ""))
        
        # Clean invoice number to show only numeric part
        if invoice_number:
            # Extract only digits from invoice number
            import re
            numeric_parts = re.findall(r'\d+', str(invoice_number))
            if numeric_parts:
                # Take the last/largest numeric part (e.g., from "INV-000061" get "61")
                invoice_number_clean = str(int(numeric_parts[-1]))  # Remove leading zeros
            else:
                invoice_number_clean = str(invoice_number)
        else:
            invoice_number_clean = ""
        
        # Simple QR code with only SDC verification information
        qr_text = f"""SDC ID: {invoice_data.get("sdc_id", "")}
Receipt Number: {vsdc_receipt_no}/{vsdc_receipt_no}
Internal Data: {invoice_data.get("vsdc_internal_data", "")}
Receipt Signature: {invoice_data.get("vsdc_receipt_signature", "")}
Receipt Number: {invoice_number_clean}"""
        
        print(f"QR Code generated with length: {len(qr_text)} characters")
        print(f"QR Code content: {qr_text}")
        
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
    
    def analyze_verification_pattern(self, example_code="10141255500ZPKRT6GD55DGTZBM"):
        """Analyze the RRA verification code pattern to understand the structure"""
        print(f"Analyzing RRA verification code pattern: {example_code}")
        print(f"Total length: {len(example_code)}")
        
        # Try to identify different segments
        # Common patterns might be:
        # - SDC ID + Receipt Number + Signature
        # - Receipt Number + Date + Signature  
        # - Internal Data + Receipt Signature
        
        possible_patterns = [
            {"name": "SDC_ID (11 chars) + Signature", "sdc": example_code[:11], "signature": example_code[11:]},
            {"name": "Receipt (10 chars) + Signature", "receipt": example_code[:10], "signature": example_code[10:]},
            {"name": "Mixed (8+8+10)", "part1": example_code[:8], "part2": example_code[8:16], "part3": example_code[16:]},
        ]
        
        for pattern in possible_patterns:
            print(f"\nPattern: {pattern['name']}")
            for key, value in pattern.items():
                if key != 'name':
                    print(f"  {key}: '{value}' (length: {len(value)})")
        
        return possible_patterns

    def generate_rra_verification_data(self, invoice_data):
        """Generate RRA verification data string from VSDC response
        
        Based on expert analysis of real RRA verification URL:
        URL: 10141255500ZPKRT6GD55DGTZBM
        Pattern: [TIN (9 digits)] + [Branch ID (2 digits)] + [Receipt_Signature (16 chars)]
        
        Breakdown:
        - TIN: 101412555 (9 digits - seller's taxpayer ID)
        - Branch ID: 00 (2 digits - bhfId from VSDC, "00" for main branch)  
        - Receipt Signature: ZPKRT6GD55DGTZBM (16 chars, hyphens removed from ZPKR-T6GD-55DG-TZBM)
        
        Total: 27 characters exactly (9+2+16)
        """
        try:
            # Get required data
            receipt_signature = invoice_data.get("vsdc_receipt_signature", "").strip()
            company_tin = invoice_data.get("company_tin", "").strip()
            
            # Get branch ID from VSDC payload or default to "00" (main branch)
            branch_id = "00"  # Standard main branch ID in RRA EBM system
            
            print(f"RRA Verification Code Generation:")
            print(f"  Company TIN: '{company_tin}'")
            print(f"  Branch ID: '{branch_id}' (bhfId)") 
            print(f"  Receipt Signature: '{receipt_signature}'")
            
            # Validate required data
            if not company_tin or not receipt_signature:
                missing = []
                if not company_tin: missing.append("company_tin")
                if not receipt_signature: missing.append("receipt_signature")
                raise ValueError(f"Missing required data: {missing}")
            
            # Clean TIN (remove non-digits) and ensure exactly 9 digits
            tin_clean = ''.join(c for c in company_tin if c.isdigit())
            if len(tin_clean) > 9:
                tin_clean = tin_clean[-9:]  # Take last 9 digits if longer
            elif len(tin_clean) < 9:
                tin_clean = tin_clean.zfill(9)  # Pad with leading zeros if shorter
            
            # Ensure branch ID is exactly 2 digits
            if len(branch_id) != 2:
                branch_id = "00"  # Default fallback
            
            # Clean receipt signature (remove hyphens/spaces) and ensure exactly 16 chars
            signature_clean = ''.join(c for c in receipt_signature if c.isalnum()).upper()
            if len(signature_clean) != 16:
                print(f"Warning: Receipt signature length is {len(signature_clean)}, expected 16")
                # Pad or truncate to 16 chars
                if len(signature_clean) < 16:
                    signature_clean = signature_clean.ljust(16, '0')
                else:
                    signature_clean = signature_clean[:16]
            
            # Combine: TIN (9) + Branch ID (2) + Signature (16) = 27 chars total
            verification_code = f"{tin_clean}{branch_id}{signature_clean}"
            
            print(f"Generated verification code: {verification_code}")
            print(f"  TIN part: {tin_clean} (length: {len(tin_clean)})")
            print(f"  Branch ID: {branch_id} (length: {len(branch_id)})")
            print(f"  Signature: {signature_clean} (length: {len(signature_clean)})")
            print(f"  Total length: {len(verification_code)}")
            
            # Validate final format
            if len(verification_code) != 27:
                raise ValueError(f"Invalid verification code length: {len(verification_code)}, expected 27")
            
            return verification_code
            
        except Exception as e:
            print(f"Error generating verification data: {str(e)}")
            raise ValueError(f"Cannot generate valid RRA verification URL: {str(e)}")

    def generate_and_upload_qr(self, invoice_data, qr_type="url"):
        """Complete process: Generate QR -> Upload to Cloudinary -> Return URL
        
        Args:
            invoice_data: Invoice data dictionary
            qr_type: "url" for RRA verification URL, "text" for text-based QR
        """
        try:
            # Step 1: Generate QR data based on type
            if qr_type == "url":
                qr_data = self.generate_invoice_qr_data(invoice_data)
            else:
                qr_data = self.generate_invoice_qr_data_text_fallback(invoice_data)
            
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
                'qr_data': qr_data,
                'qr_type': qr_type,
                'verification_url': qr_data if qr_type == "url" else None
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
