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

    def convert_ebm_response_to_invoice_model(self, ebm_response: dict, zoho_data: dict, vsdc_payload: dict) -> Invoice:
        """Convert EBM response, Zoho data, and VSDC payload to Invoice model with proper mapping"""
        try:
            invoice_data = zoho_data.get("invoice", zoho_data)
            logger.debug(f"Converting EBM response: {ebm_response}")
            logger.debug(f"Using Zoho data: {invoice_data}")
            logger.debug(f"Using VSDC payload: {vsdc_payload}")

            # Company information
            company = Company(
                name=settings.COMPANY_NAME,
                address=settings.COMPANY_ADDRESS,
                tel=settings.COMPANY_TEL,
                email=settings.COMPANY_EMAIL,
                tin=str(invoice_data.get("cf_custtin", settings.COMPANY_TIN)),
                cashier=f"admin({invoice_data.get('cf_custtin', settings.COMPANY_TIN)})"
            )

            # Client information
            client = Client(
                name=str(vsdc_payload.get("custNm", invoice_data.get("customer_name", "Unknown Customer"))),
                tin=str(vsdc_payload.get("custTin", invoice_data.get("cf_custtin", "")))
            )

            # Convert items
            items = []
            zoho_items = invoice_data.get("line_items", [])
            vsdc_items = vsdc_payload.get("itemList", [])
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

            # Invoice number
            invoice_number = str(ebm_response.get("data", {}).get("rcptNo", ""))
            if not invoice_number:
                invoice_number_raw = str(invoice_data.get("invoice_number", "INV-UNKNOWN"))
                numeric_part = "".join(re.findall(r'\d+', invoice_number_raw))
                invoice_number = numeric_part if numeric_part else "0"

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
            receipt_number = f"{invoice_number}/{invoice_number}NS"

            # Totals
            total_tax_b = float(vsdc_payload.get("taxAmtB", invoice_data.get("tax_total", 0)))
            total_b = float(vsdc_payload.get("taxblAmtB", invoice_data.get("sub_total", 0)))
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
                total_aex=f"{vsdc_payload.get('taxblAmtA', 0):,.2f}",
                total_b=f"{total_b:,.2f}",
                total_tax_a=f"{vsdc_payload.get('taxAmtA', 0):,.2f}",
                total_tax_b=f"{total_tax_b:,.2f}",
                total_tax=f"{total_tax_b:,.2f}"  # Only B tax present
            )

            return invoice

        except Exception as e:
            logger.error(f"Error converting to invoice model: {str(e)}")
            raise

    async def generate_advanced_pdf(self, ebm_response: dict, zoho_data: dict, vsdc_payload: dict) -> Dict[str, Any]:
        """Generate PDF using the advanced invoice generator"""
        try:
            invoice = self.convert_ebm_response_to_invoice_model(ebm_response, zoho_data, vsdc_payload)
            invoice_data = invoice.to_dict()
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

    async def generate_credit_note_pdf(self, ebm_response: dict, zoho_data: dict, vsdc_payload: dict) -> Dict[str, Any]:
        """Generate PDF for credit note (refund)"""
        try:
            # Convert using the same method, but modify some fields to reflect refund
            invoice = self.convert_ebm_response_to_invoice_model(ebm_response, zoho_data, vsdc_payload)
            
            # Adjust totals (display as positive numbers, but note that it's a refund)
            invoice.total_rwf = f"{abs(float(invoice.total_rwf.replace(',', ''))):,.2f}"
            invoice.total_b = f"{abs(float(invoice.total_b.replace(',', ''))):,.2f}"
            invoice.total_tax_b = f"{abs(float(invoice.total_tax_b.replace(',', ''))):,.2f}"
            invoice.total_tax = f"{abs(float(invoice.total_tax.replace(',', ''))):,.2f}"
            
            invoice_data = invoice.to_dict()
            invoice_data["invoice_type"] = "Credit Note"  # Set it in the dictionary instead
            
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
            return result
            
        except Exception as e:
            logger.error(f"Error generating credit note PDF: {str(e)}")
            raise PDFGenerationError(f"Failed to generate credit note PDF: {str(e)}")
