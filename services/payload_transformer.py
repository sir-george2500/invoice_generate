import logging
import re
from datetime import datetime
from typing import Optional
from click import utils
from fastapi import HTTPException
from utils.tax_calculator import calculate_tax, validate_required_fields  
logger = logging.getLogger(__name__)

import random
class PayloadTransformer:
    """Service to handle payload transformations between Zoho and VSDC formats"""
    
    def __init__(self, vsdc_service):
        self.vsdc_service = vsdc_service

    def calculate_tax(self, price: float) -> float:
        """Calculate tax using the formula: price * 18 / 118"""
        return round(price * 18 / 118, 2)

    def validate_required_fields(self, zoho_payload: dict) -> None:
        """Validate required fields from Zoho payload"""
        invoice_data = zoho_payload.get("invoice", zoho_payload)
        
        invoice_no = invoice_data.get("invoice_number")
        if not invoice_no or (isinstance(invoice_no, str) and invoice_no.strip() == ""):
            raise ValueError("Invoice number must be a non-empty string")
        
        items = invoice_data.get("line_items", [])
        if not items:
            raise ValueError("Invoice must contain at least one line item")
        
        for idx, item in enumerate(items):
            item_name = item.get("name") or item.get("description", "")
            if not item_name.strip():
                raise ValueError(f"Item {idx + 1} must have a name or description")
            if not item.get("rate") or float(item.get("rate", 0)) <= 0:
                raise ValueError(f"Item {idx + 1} must have a valid rate/price")

    def transform_zoho_to_vsdc(self,zoho_payload: dict) -> dict:
        """Transform Zoho payload to match VSDC API format"""
        try:
            # Validate required fields first
            validate_required_fields(zoho_payload)
            
            # Extract invoice data (Zoho nests data in 'invoice' object)
            invoice_data = zoho_payload.get("invoice", zoho_payload)
            
            # Extract necessary fields from Zoho payload
            invoice_number_raw = str(invoice_data.get("invoice_number")).strip()
            # Extract numeric part from invoice number (e.g., "INV-000005" -> 5)
            try:
                numeric_part = re.findall(r'\d+', invoice_number_raw)
                if numeric_part:
                    invoice_no = int(numeric_part[-1])  # Take the last number found
                else:
                    raise ValueError(f"Could not extract numeric part from invoice number: {invoice_number_raw}")
            except (ValueError, IndexError):
                # Fallback: try to convert the whole string to int, or use timestamp
                try:
                    invoice_no = int(invoice_number_raw)
                except ValueError:
                    # Last resort: use timestamp-based number
                    invoice_no = int(datetime.now().strftime("%Y%m%d%H%M%S")[-8:])
                    logger.warning(f"Could not parse invoice number {invoice_number_raw}, using timestamp-based number: {invoice_no}")
            
            customer_name = invoice_data.get("customer_name", "Unknown Customer")
            
            # Get customer mobile from contact_persons_details
            customer_mobile = None
            contact_persons = invoice_data.get("contact_persons_details", [])
            if contact_persons:
                first_contact = contact_persons[0]
                customer_mobile = first_contact.get("mobile") or first_contact.get("phone")
            
            items = invoice_data.get("line_items", [])
            
            # Handle date formatting
            sales_date_raw = invoice_data.get("date", invoice_data.get("invoice_date"))
            if sales_date_raw:
                try:
                    if isinstance(sales_date_raw, str):
                        for date_format in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                parsed_date = datetime.strptime(sales_date_raw.split()[0], date_format)
                                sales_date = parsed_date.strftime("%Y%m%d")
                                break
                            except ValueError:
                                continue
                        else:
                            sales_date = datetime.now().strftime("%Y%m%d")
                    else:
                        sales_date = datetime.now().strftime("%Y%m%d")
                except:
                    sales_date = datetime.now().strftime("%Y%m%d")
            else:
                sales_date = datetime.now().strftime("%Y%m%d")
            
            # Initialize the VSDC payload structure
            vsdc_payload = {
                "tin": "944000008",
                "bhfId": "00",
                "invcNo": invoice_no+ random.randint(1, 1000),  # Adding a random number to avoid duplicates
                "orgInvcNo": 0,
                "custTin": "998000003",
                "prcOrdCd": "708955",
                "custNm": customer_name,
                "salesTyCd": "N",
                "rcptTyCd": "S",
                "pmtTyCd": "01",
                "salesSttsCd": "02",
                "cfmDt": datetime.now().strftime("%Y%m%d%H%M%S"),
                "salesDt": sales_date,
                "stockRlsDt": datetime.now().strftime("%Y%m%d%H%M%S"),
                "cnclReqDt": None,
                "cnclDt": None,
                "rfdDt": None,
                "rfdRsnCd": None,
                "totItemCnt": len(items),
                "taxblAmtA": 0,
                "taxblAmtB": 0,
                "taxblAmtC": 0,
                "taxblAmtD": 0,
                "taxRtA": 0,
                "taxRtB": 18,
                "taxRtC": 0,
                "taxRtD": 0,
                "taxAmtA": 0,
                "taxAmtB": 0,
                "taxAmtC": 0,
                "taxAmtD": 0,
                "totTaxblAmt": 0,
                "totTaxAmt": 0,
                "totAmt": 0,
                "prchrAcptcYn": "N",
                "remark": None,
                "regrId": "11999",
                "regrNm": "TestVSDC",
                "modrId": "45678",
                "modrNm": "TestVSDC",
                "receipt": {
                    "custTin": None,
                    "custMblNo": customer_mobile,
                    "rptNo": 1,
                    "trdeNm": "Maryshop",
                    "adrs": "KICUKIRO-KABEZA",
                    "topMsg": "Maryshop",
                    "btmMsg": "Welcome",
                    "prchrAcptcYn": "N"
                },
                "itemList": []
            }
            
            # Process each item
            for idx, item in enumerate(items, start=1):
                try:
                    price = float(item.get("rate", 0))
                    quantity = float(item.get("quantity", 1))
                    supply_amount = round(price * quantity, 2)
                    tax_amount = calculate_tax(supply_amount)
                    
                    item_name = item.get("name") or item.get("description") or f"Item_{idx}"
                    
                    vsdc_item = {
                        "itemSeq": idx,
                        "itemCd": item.get("item_id") or f"RW1NTXU000000{idx:02d}",
                        "itemClsCd": item.get("item_class_code", f"50{idx}211080{idx}"),
                        "itemNm": item_name,
                        "bcd": None,
                        "pkgUnitCd": "NT",
                        "pkg": 1,
                        "qtyUnitCd": "U",
                        "qty": quantity,
                        "prc": price,
                        "splyAmt": supply_amount,
                        "dcRt": 0,
                        "dcAmt": 0,
                        "isrccCd": None,
                        "isrccNm": None,
                        "isrcRt": None,
                        "isrcAmt": None,
                        "taxTyCd": "B",
                        "taxblAmt": supply_amount,
                        "taxAmt": tax_amount,
                        "totAmt": supply_amount
                    }
                    
                    vsdc_payload["itemList"].append(vsdc_item)
                    vsdc_payload["taxblAmtB"] += supply_amount
                    vsdc_payload["taxAmtB"] += tax_amount
                    vsdc_payload["totTaxblAmt"] += supply_amount
                    vsdc_payload["totTaxAmt"] += tax_amount
                    vsdc_payload["totAmt"] += supply_amount
                    
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing item {idx}: {str(e)}")
                    raise ValueError(f"Invalid data in item {idx}: {str(e)}")
            
            # Round final amounts
            vsdc_payload["taxblAmtB"] = round(vsdc_payload["taxblAmtB"], 2)
            vsdc_payload["taxAmtB"] = round(vsdc_payload["taxAmtB"], 2)
            vsdc_payload["totTaxblAmt"] = round(vsdc_payload["totTaxblAmt"], 2)
            vsdc_payload["totTaxAmt"] = round(vsdc_payload["totTaxAmt"], 2)
            vsdc_payload["totAmt"] = round(vsdc_payload["totAmt"], 2)
            
            return vsdc_payload
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid Zoho payload: {str(e)}")
        except Exception as e:
            logger.error(f"Error transforming payload: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing payload: {str(e)}")

    def _format_sales_date(self, date_raw: str) -> str:
        """Format sales date to YYYYMMDD"""
        if date_raw:
            try:
                if isinstance(date_raw, str):
                    for date_format in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            parsed_date = datetime.strptime(date_raw.split()[0], date_format)
                            return parsed_date.strftime("%Y%m%d")
                        except ValueError:
                            continue
            except:
                pass
        return datetime.now().strftime("%Y%m%d")

    def _extract_customer_mobile(self, invoice_data: dict) -> Optional[str]:
        """Extract customer mobile from contact details"""
        contact_persons = invoice_data.get("contact_persons_details", [])
        if contact_persons:
            first_contact = contact_persons[0]
            return first_contact.get("mobile") or first_contact.get("phone")
        return None

    def _process_item_with_correct_tax(self, item: dict, idx: int, vsdc_payload: dict):
        """Process individual item with correct VSDC tax calculation matching your working implementation"""
        try:
            price = float(item.get("rate", 0))  # This is tax-inclusive price
            quantity = float(item.get("quantity", 1))
            supply_amount = round(price * quantity, 2)
            tax_amount = self.calculate_tax(supply_amount)
            
            item_name = item.get("name") or item.get("description") or f"Item_{idx}"
            
            vsdc_item = {
                "itemSeq": idx,
                "itemCd": item.get("item_id") or f"RW1NTXU000000{idx:02d}",
                "itemClsCd": item.get("item_class_code", f"50{idx}211080{idx}"),
                "itemNm": item_name,
                "bcd": None,
                "pkgUnitCd": "NT",
                "pkg": 1,
                "qtyUnitCd": "U",
                "qty": quantity,
                "prc": price,
                "splyAmt": supply_amount,
                "dcRt": 0,
                "dcAmt": 0,
                "isrccCd": None,
                "isrccNm": None,
                "isrcRt": None,
                "isrcAmt": None,
                "taxTyCd": "B",
                "taxblAmt": supply_amount,
                "taxAmt": tax_amount,
                "totAmt": supply_amount
            }
            
            vsdc_payload["itemList"].append(vsdc_item)
            vsdc_payload["taxblAmtB"] += supply_amount
            vsdc_payload["taxAmtB"] += tax_amount
            vsdc_payload["totTaxblAmt"] += supply_amount
            vsdc_payload["totTaxAmt"] += tax_amount
            vsdc_payload["totAmt"] += supply_amount
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing item {idx}: {str(e)}")
            raise ValueError(f"Invalid data in item {idx}: {str(e)}")
