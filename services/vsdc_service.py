import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import re
from src.invoice_generator import InvoiceGenerator
from src.models import Invoice, Company, Client, InvoiceItem
from src.invoice_qrcode import InvoiceQRGenerator
from utils.tax_calculator import (
    extract_vat_from_inclusive_price, 
    calculate_exclusive_price,
    calculate_vat_amount,
    get_tax_category
)
from exceptions.custom_exceptions import TaxCalculationError, PDFGenerationError
from config.settings import settings

logger = logging.getLogger(__name__)

class VSSDCInvoiceService:
    """Service to handle VSDC integration with dynamic tax calculation"""
    
    def __init__(self, cloudinary_config: Dict[str, str]):
        self.cloudinary_config = cloudinary_config
        
        # Initialize QR code generator if Cloudinary is configured
        self.qr_generator = None
        if all(cloudinary_config.values()):
            self.qr_generator = InvoiceQRGenerator(cloudinary_config)
            logger.info("QR code generator initialized with Cloudinary")
        else:
            logger.warning("Cloudinary not configured, QR codes will be disabled")
        
        # Initialize invoice generator
        self.invoice_generator = InvoiceGenerator(qr_generator=self.qr_generator)
        
        # Ensure output directories exist
        os.makedirs("output/pdf", exist_ok=True)
        os.makedirs("output/html", exist_ok=True)

    def extract_receipt_number_safely(self, ebm_response: dict, zoho_data: dict, vsdc_payload: Optional[dict] = None) -> str:
        """Extract receipt number with proper validation and audit trail"""
        try:
            # Priority 1: Use VSDC receipt number from EBM response (most authoritative)
            vsdc_receipt = ebm_response.get("data", {}).get("rcptNo", "")
            if vsdc_receipt and str(vsdc_receipt).strip():
                final_receipt = str(vsdc_receipt).strip()
                logger.info(f"Using VSDC receipt number: {final_receipt}")
                return final_receipt
            
            # Priority 2: Use invoice number from VSDC payload (already processed)
            if vsdc_payload and vsdc_payload.get("invcNo"):
                vsdc_invoice_no = str(vsdc_payload["invcNo"])
                logger.info(f"Using VSDC invoice number: {vsdc_invoice_no}")
                return vsdc_invoice_no
            
            # Priority 3: Extract from original Zoho data (preserve original format)
            if "creditnote" in zoho_data:
                document_data = zoho_data["creditnote"]
                original_number = document_data.get("creditnote_number", document_data.get("number", ""))
            elif "invoice" in zoho_data:
                document_data = zoho_data["invoice"]
                original_number = document_data.get("invoice_number", "")
            else:
                document_data = zoho_data
                original_number = document_data.get("invoice_number", document_data.get("creditnote_number", ""))
            
            if original_number and str(original_number).strip():
                cleaned_number = str(original_number).strip()
                logger.info(f"Using original Zoho number: {cleaned_number}")
                return cleaned_number
            
            # Fallback: Generate safe receipt number
            fallback_number = f"RCP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.warning(f"No valid receipt number found, using fallback: {fallback_number}")
            return fallback_number
            
        except Exception as e:
            logger.error(f"Error extracting receipt number: {str(e)}")
            emergency_fallback = f"ERR-{datetime.now().strftime('%m%d%H%M%S')}"
            logger.error(f"Using emergency fallback: {emergency_fallback}")
            return emergency_fallback

    def generate_safe_receipt_number_format(self, base_number: str) -> str:
        """Generate receipt number in proper format without duplication"""
        try:
            # Clean the base number
            base_clean = str(base_number).strip()
            
            # Don't duplicate if it already has proper format
            if "/" in base_clean and base_clean.endswith("NS"):
                logger.info(f"Receipt number already in proper format: {base_clean}")
                return base_clean
            
            # For simple numbers, use standard format
            if base_clean.isdigit():
                formatted = f"{base_clean}/001NS"
                logger.info(f"Formatted numeric receipt: {base_clean} -> {formatted}")
                return formatted
            
            # For complex formats, keep as-is to avoid corruption
            logger.info(f"Preserving original receipt format: {base_clean}")
            return base_clean
            
        except Exception as e:
            logger.error(f"Error formatting receipt number: {str(e)}")
            return str(base_number)

    def extract_business_info_from_zoho(self, invoice_data: dict, vsdc_payload: Optional[dict] = None) -> dict:
        """Extract business information from Zoho custom fields - Fixed for credit notes"""
        try:
            # Handle both invoice and credit note structures
            if "creditnote" in invoice_data:
                document_data = invoice_data["creditnote"]
                logger.info("Extracting business info from CREDIT NOTE structure")
            elif "invoice" in invoice_data:
                document_data = invoice_data["invoice"]
                logger.info("Extracting business info from INVOICE structure")
            else:
                document_data = invoice_data
                logger.info("Extracting business info from DIRECT structure")
            
            custom_field_hash = document_data.get("custom_field_hash", {})
            
            # Extract business info directly from Zoho custom fields using the exact field names
            business_name = custom_field_hash.get("cf_organizationname", "")
            business_address = custom_field_hash.get("cf_seller_company_address", "")
            business_email = custom_field_hash.get("cf_seller_company_email", "")
            business_tin = custom_field_hash.get("cf_tin", "")
            
            # Fallback to custom_fields array if custom_field_hash is missing values
            if not business_name or not business_address or not business_email or not business_tin:
                for field in document_data.get("custom_fields", []):
                    api_name = field.get("api_name")
                    value = field.get("value", "")
                    
                    if api_name == "cf_organizationname" and not business_name:
                        business_name = value
                    elif api_name == "cf_seller_company_address" and not business_address:
                        business_address = value
                    elif api_name == "cf_seller_company_email" and not business_email:
                        business_email = value
                    elif api_name == "cf_tin" and not business_tin:
                        business_tin = value
            
            # Clean up the values and provide fallbacks
            business_name = business_name.strip() if business_name else settings.COMPANY_NAME
            business_address = business_address.strip() if business_address else settings.COMPANY_ADDRESS
            business_email = business_email.strip() if business_email else settings.COMPANY_EMAIL
            business_tin = business_tin.strip() if business_tin else settings.COMPANY_TIN
            
            logger.info(f"Extracted business info:")
            logger.info(f"   Organization Name: {business_name}")
            logger.info(f"   Address: {business_address}")
            logger.info(f"   Email: {business_email}")
            logger.info(f"   TIN: {business_tin}")
            
            return {
                "name": business_name,
                "address": business_address,
                "tel": settings.COMPANY_TEL,
                "email": business_email,
                "tin": business_tin,
                "cashier": f"admin({business_tin})"
            }
            
        except Exception as e:
            logger.error(f"Error extracting business info from Zoho custom fields: {str(e)}")
            # Fallback to settings
            return {
                "name": settings.COMPANY_NAME,
                "address": settings.COMPANY_ADDRESS,
                "tel": settings.COMPANY_TEL,
                "email": settings.COMPANY_EMAIL,
                "tin": settings.COMPANY_TIN,
                "cashier": f"admin({settings.COMPANY_TIN})"
            }

    def get_tax_rate_from_zoho_item(self, item: dict) -> float:
        """Extract tax rate from Zoho item data"""
        tax_rate = None
        for field in ['tax_rate', 'vat_rate', 'tax_percentage']:
            if field in item:
                try:
                    tax_rate = float(item[field])
                    break
                except (ValueError, TypeError):
                    continue
        if tax_rate is None and 'tax' in item:
            try:
                if isinstance(item['tax'], (int, float)):
                    tax_rate = float(item['tax'])
            except (ValueError, TypeError):
                pass
        if tax_rate is None:
            tax_category = item.get('tax_category', '').upper()
            if tax_category == 'A':
                tax_rate = 0.0
            elif tax_category == 'B':
                tax_rate = 18.0
        if tax_rate is None:
            tax_rate = 18.0
            logger.warning(f"No tax rate found for item {item.get('name', 'Unknown')}, defaulting to 18%")
        return tax_rate

    def calculate_item_totals(self, item: dict) -> dict:
        """Calculate item totals with dynamic tax rates"""
        try:
            price = float(item.get("rate", 0))
            quantity = float(item.get("quantity", 1))
            tax_rate = self.get_tax_rate_from_zoho_item(item)
            
            # Assume price is tax-exclusive (aligns with VSDC splyAmt)
            unit_price_excl_tax = price
            tax_per_unit = calculate_vat_amount(price, tax_rate)
            
            subtotal = round(unit_price_excl_tax * quantity, 2)
            total_tax = round(tax_per_unit * quantity, 2)
            total_amount = round(subtotal, 2)  # Exclude tax for total_price
            
            return {
                'unit_price_excl_tax': unit_price_excl_tax,
                'tax_per_unit': tax_per_unit,
                'subtotal': subtotal,
                'total_tax': total_tax,
                'total_amount': total_amount,
                'tax_rate': tax_rate,
                'tax_category': get_tax_category(tax_rate)
            }
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating item totals: {str(e)}")
            raise TaxCalculationError(f"Invalid data in item calculations: {str(e)}")

    def convert_ebm_response_to_invoice_model(self, ebm_response: dict, zoho_data: dict, vsdc_payload: Optional[dict] = None) -> Invoice:
        """Convert EBM response, Zoho data, and VSDC payload to Invoice model with proper mapping"""
        try:
            # Handle both invoice and credit note structures
            if "creditnote" in zoho_data:
                invoice_data = zoho_data["creditnote"]
                logger.debug(f"Converting EBM response for CREDIT NOTE")
            elif "invoice" in zoho_data:
                invoice_data = zoho_data["invoice"]
                logger.debug(f"Converting EBM response for INVOICE")
            else:
                invoice_data = zoho_data
                logger.debug(f"Converting EBM response for DIRECT structure")
            
            logger.debug(f"Using document data: {invoice_data}")
            logger.debug(f"Using VSDC payload: {vsdc_payload}")
            
            # Extract business information from Zoho custom fields directly
            business_info = self.extract_business_info_from_zoho(zoho_data, vsdc_payload)
            
            # Company information
            company = Company(
                name=business_info["name"],
                address=business_info["address"],
                tel=business_info["tel"],
                email=business_info["email"],
                tin=business_info["tin"],
                cashier=business_info["cashier"]
            )
            
            # Client information
            customer_tin = vsdc_payload.get("custTin", "") if vsdc_payload else ""
            customer_name = "Unknown Customer"
            
            if not customer_tin:
                # Try multiple fallback sources
                custom_field_hash = invoice_data.get("custom_field_hash", {})
                customer_tin = custom_field_hash.get("cf_customer_tin", "")
                
                # Additional fallback for credit notes
                if not customer_tin:
                    customer_custom_field_hash = invoice_data.get("customer_custom_field_hash", {})
                    customer_tin = customer_custom_field_hash.get("cf_custtin", "")
                
                # Try customer_custom_fields array
                if not customer_tin:
                    for field in invoice_data.get("customer_custom_fields", []):
                        if field.get("api_name") == "cf_custtin":
                            customer_tin = field.get("value", "")
                            break
                
                # Try custom_fields array for customer TIN
                if not customer_tin:
                    for field in invoice_data.get("custom_fields", []):
                        if field.get("api_name") == "cf_customer_tin":
                            customer_tin = field.get("value", "")
                            break
                
                # For credit notes, try to extract from referenced invoice
                if not customer_tin and "creditnote" in zoho_data:
                    invoices_credited = invoice_data.get("invoices_credited", [])
                    if invoices_credited and len(invoices_credited) > 0:
                        logger.info(f"Trying to extract customer TIN from credited invoice data")
            
            # Get customer name
            if vsdc_payload:
                customer_name = str(vsdc_payload.get("custNm", invoice_data.get("customer_name", "Unknown Customer")))
            else:
                customer_name = str(invoice_data.get("customer_name", "Unknown Customer"))
            
            logger.info(f"Client Info - Name: {customer_name}, TIN: {customer_tin}")
            
            client = Client(
                name=customer_name,
                tin=str(customer_tin)
            )
            
            # Convert items
            items = []
            zoho_items = invoice_data.get("line_items", [])
            vsdc_items = vsdc_payload.get("itemList", []) if vsdc_payload else []
            
            for idx, vsdc_item in enumerate(vsdc_items, start=1):
                zoho_item = zoho_items[idx-1] if idx-1 < len(zoho_items) else {}
                item_calculations = self.calculate_item_totals(zoho_item)
                item = InvoiceItem(
                    code=str(vsdc_item.get("itemCd", zoho_item.get("item_id", f"RW1NTXU000000{idx:02d}"))),
                    description=str(zoho_item.get("description", vsdc_item.get("itemNm", "Unknown Item"))),
                    quantity=f"{float(vsdc_item.get('qty', zoho_item.get('quantity', 0))):,.2f}",
                    tax=str(vsdc_item.get("taxTyCd", item_calculations.get('tax_category', "B"))),
                    unit_price=f"{float(vsdc_item.get('prc', item_calculations.get('unit_price_excl_tax', 0))):,.2f}",
                    total_price=f"{float(vsdc_item.get('splyAmt', item_calculations.get('subtotal', 0))):,.2f}"
                )
                items.append(item)
            
            # If no vsdc_items, use zoho items only
            if not vsdc_items and zoho_items:
                for idx, zoho_item in enumerate(zoho_items, start=1):
                    item_calculations = self.calculate_item_totals(zoho_item)
                    
                    item = InvoiceItem(
                        code=str(zoho_item.get("item_id", f"RW1NTXU000000{idx:02d}")),
                        description=str(zoho_item.get("description", "Unknown Item")),
                        quantity=f"{float(zoho_item.get('quantity', 0)):,.2f}",
                        tax=str(item_calculations.get('tax_category', "B")),
                        unit_price=f"{item_calculations.get('unit_price_excl_tax', 0):,.2f}",
                        total_price=f"{item_calculations.get('subtotal', 0):,.2f}"
                    )
                    items.append(item)
            
            # Safe invoice number extraction with audit trail
            invoice_number = self.extract_receipt_number_safely(ebm_response, zoho_data, vsdc_payload)
            
            logger.info(f"Final invoice number for PDF: {invoice_number}")
            
            # Extract VSDC data fields
            vsdc_data = ebm_response.get("data", {})
            vsdc_receipt_no = str(vsdc_data.get("rcptNo", ""))
            vsdc_total_receipt_no = str(vsdc_data.get("totRcptNo", ""))
            vsdc_internal_data = str(vsdc_data.get("intrlData", ""))
            vsdc_receipt_signature = str(vsdc_data.get("rcptSign", ""))
            vsdc_receipt_date_raw = str(vsdc_data.get("vsdcRcptPbctDate", ""))
            
            # Format VSDC receipt date
            vsdc_receipt_date = ""
            if vsdc_receipt_date_raw and len(vsdc_receipt_date_raw) >= 14:
                try:
                    parsed_dt = datetime.strptime(vsdc_receipt_date_raw, "%Y%m%d%H%M%S")
                    vsdc_receipt_date = parsed_dt.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    vsdc_receipt_date = vsdc_receipt_date_raw
            
            # Date and time
            invoice_date = ""
            invoice_time = ""
            vsdc_datetime = ebm_response.get("data", {}).get("vsdcRcptPbctDate", "")
            if vsdc_datetime and len(vsdc_datetime) >= 14:
                try:
                    parsed_dt = datetime.strptime(vsdc_datetime, "%Y%m%d%H%M%S")
                    invoice_date = parsed_dt.strftime("%d-%m-%Y")
                    invoice_time = parsed_dt.strftime("%H:%M:%S")
                except ValueError:
                    pass
            if not invoice_date:
                try:
                    parsed_date = datetime.strptime(invoice_data.get("date", ""), "%Y-%m-%d")
                    invoice_date = parsed_date.strftime("%d-%m-%Y")
                except (ValueError, TypeError):
                    invoice_date = datetime.now().strftime("%d-%m-%Y")
            if not invoice_time:
                invoice_time = datetime.now().strftime("%H:%M:%S")
            
            # SDC information
            sdc_id = str(ebm_response.get("data", {}).get("sdcId", settings.VSDC_SDC_ID))
            mrc = str(ebm_response.get("data", {}).get("mrcNo", settings.VSDC_MRC))
            
            # Safe receipt number formatting
            receipt_number = self.generate_safe_receipt_number_format(invoice_number)
            
            # Totals with null safety
            total_tax_b = float(vsdc_payload.get("taxAmtB", invoice_data.get("tax_total", 0)) if vsdc_payload else invoice_data.get("tax_total", 0))
            total_b = float(vsdc_payload.get("taxblAmtB", invoice_data.get("sub_total", 0)) if vsdc_payload else invoice_data.get("sub_total", 0))
            total_rwf = total_b  # Tax-exclusive, per PDF
            
            invoice = Invoice(
                company=company,
                client=client,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                invoice_time=invoice_time,
                sdc_id=sdc_id,
                receipt_number=receipt_number,
                mrc=mrc,
                items=items,
                total_rwf=f"{total_rwf:,.2f}",
                total_aex=f"{vsdc_payload.get('taxblAmtA', 0):,.2f}" if vsdc_payload else "0.00",
                total_b=f"{total_b:,.2f}",
                total_tax_a=f"{vsdc_payload.get('taxAmtA', 0):,.2f}" if vsdc_payload else "0.00",
                total_tax_b=f"{total_tax_b:,.2f}",
                total_tax=f"{total_tax_b:,.2f}",
                vsdc_receipt_no=vsdc_receipt_no,
                vsdc_total_receipt_no=vsdc_total_receipt_no,
                vsdc_internal_data=vsdc_internal_data,
                vsdc_receipt_signature=vsdc_receipt_signature,
                vsdc_receipt_date=vsdc_receipt_date
            )
            
            logger.info(f"Invoice model created - Company: {company.name}, Client: {client.name}, Client TIN: {client.tin}, Company TIN: {company.tin}")
            logger.info(f"Receipt details - Invoice Number: {invoice.invoice_number}, Receipt Number: {invoice.receipt_number}")
            return invoice
            
        except Exception as e:
            logger.error(f"Error converting to invoice model: {str(e)}")
            raise

    async def generate_advanced_pdf(self, ebm_response: dict, zoho_data: dict, vsdc_payload: Optional[dict] = None) -> Dict[str, Any]:
        """Generate PDF using the advanced invoice generator"""
        try:
            invoice = self.convert_ebm_response_to_invoice_model(ebm_response, zoho_data, vsdc_payload)
            invoice_data = invoice.to_dict()
            
            logger.info(f"Generating PDF with company: {invoice_data.get('company_name')}")
            
            pdf_filename = f"invoice_{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = f"output/pdf/{pdf_filename}"
            self.invoice_generator.generate_pdf_with_qr(
                invoice_data, 
                pdf_path, 
                generate_qr=bool(self.qr_generator)
            )
            html_filename = f"invoice_{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_path = f"output/html/{html_filename}"
            self.invoice_generator.generate_html(invoice_data, html_path)
            result = {
                "pdf_path": pdf_path,
                "pdf_filename": pdf_filename,
                "html_path": html_path,
                "html_filename": html_filename,
                "invoice_number": invoice.invoice_number,
                "qr_code_generated": 'qr_code_path' in invoice_data
            }
            if 'qr_code_path' in invoice_data:
                result["qr_code_url"] = invoice_data['qr_code_path']
                result["qr_public_id"] = invoice_data.get('qr_public_id')
            logger.info(f"Advanced PDF generated successfully: {pdf_filename}")
            return result
        except Exception as e:
            logger.error(f"Error generating advanced PDF: {str(e)}")
            raise PDFGenerationError(f"Error generating advanced PDF: {str(e)}")

    async def generate_credit_note_pdf(self, ebm_response: dict, zoho_data: dict, vsdc_payload: Optional[dict] = None) -> Dict[str, Any]:
        """Generate PDF for credit note (refund) - Fixed for proper data extraction"""
        try:
            # Convert using the same method with proper credit note handling
            invoice = self.convert_ebm_response_to_invoice_model(ebm_response, zoho_data, vsdc_payload)
            
            # Adjust totals (display as positive numbers, but note that it's a refund)
            invoice.total_rwf = f"{abs(float(invoice.total_rwf.replace(',', ''))):,.2f}"
            invoice.total_b = f"{abs(float(invoice.total_b.replace(',', ''))):,.2f}"
            invoice.total_tax_b = f"{abs(float(invoice.total_tax_b.replace(',', ''))):,.2f}"
            invoice.total_tax = f"{abs(float(invoice.total_tax.replace(',', ''))):,.2f}"
            
            invoice_data = invoice.to_dict()
            invoice_data["invoice_type"] = "Credit Note"
            
            # Add credit note specific fields
            if "creditnote" in zoho_data:
                credit_note_data = zoho_data["creditnote"]
                # Add original invoice reference if available
                invoices_credited = credit_note_data.get("invoices_credited", [])
                if invoices_credited and len(invoices_credited) > 0:
                    invoice_data["original_invoice_number"] = invoices_credited[0].get("invoice_number", "")
                
                # Add credit reason if available
                invoice_data["credit_reason"] = credit_note_data.get("reason", "Product return/refund")
            
            filename_base = f"credit_note_{invoice.invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            pdf_path = f"output/pdf/{filename_base}.pdf"
            html_path = f"output/html/{filename_base}.html"
            
            self.invoice_generator.generate_pdf_with_qr(
                invoice_data,
                pdf_path,
                generate_qr=bool(self.qr_generator)
            )
            
            self.invoice_generator.generate_html(invoice_data, html_path)
            
            result = {
                "pdf_path": pdf_path,
                "pdf_filename": f"{filename_base}.pdf",
                "html_path": html_path,
                "html_filename": f"{filename_base}.html",
                "invoice_number": invoice.invoice_number,
                "is_credit_note": True,
                "qr_code_generated": 'qr_code_path' in invoice_data
            }
            
            if 'qr_code_path' in invoice_data:
                result["qr_code_url"] = invoice_data['qr_code_path']
                result["qr_public_id"] = invoice_data.get('qr_public_id')
            
            logger.info(f"Credit note PDF generated: {filename_base}.pdf")
            logger.info(f"Credit note details - Company: {invoice.company.name}, Client: {invoice.client.name}, Client TIN: {invoice.client.tin}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating credit note PDF: {str(e)}")
            raise PDFGenerationError(f"Failed to generate credit note PDF: {str(e)}")
