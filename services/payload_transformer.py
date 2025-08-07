import logging
import re
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from utils.tax_calculator import calculate_tax, validate_required_fields  
import random

logger = logging.getLogger(__name__)

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

    def transform_zoho_to_vsdc(self, zoho_payload: dict) -> dict:
        """Transform Zoho payload to match VSDC API format"""
        try:
            # Validate required fields first
            validate_required_fields(zoho_payload)
            
            # Extract invoice data
            invoice_data = zoho_payload.get("invoice", zoho_payload)
            # Extract numeric invoice number
            invoice_number_raw = str(invoice_data.get("invoice_number")).strip()
            try:
                numeric_part = re.findall(r'\d+', invoice_number_raw)
                if numeric_part:
                    invoice_no = int(numeric_part[-1])
                else:
                    raise ValueError(f"Could not extract numeric part from invoice number: {invoice_number_raw}")
            except (ValueError, IndexError):
                try:
                    invoice_no = int(invoice_number_raw)
                except ValueError:
                    invoice_no = int(datetime.now().strftime("%Y%m%d%H%M%S")[-8:])
                    logger.warning(f"Could not parse invoice number {invoice_number_raw}, using timestamp-based number: {invoice_no}")
            
            customer_name = invoice_data.get("customer_name", "Unknown Customer")

            # FIX: Extract TINs and Purchase Code correctly
            custom_field_hash = invoice_data.get("custom_field_hash", {})

            tin = custom_field_hash.get("cf_tin")
            cust_tin = custom_field_hash.get("cf_custtin")
            purchase_code = custom_field_hash.get("cf_purchasecode")

            # Fallback: check custom_fields list if hash is missing
            if not tin or not cust_tin or not purchase_code:
                for field in invoice_data.get("custom_fields", []):
                    api_name = field.get("api_name")
                    if api_name == "cf_tin":
                        tin = tin or field.get("value")
                    elif api_name == "cf_custtin":
                        cust_tin = cust_tin or field.get("value")
                    elif api_name == "cf_purchasecode":
                        purchase_code = purchase_code or field.get("value")

            # Strip whitespace
            if tin:
                tin = tin.strip()
            if cust_tin:
                cust_tin = cust_tin.strip()
            if purchase_code:
                purchase_code = purchase_code.strip()

            logger.info(f"Customer TIN and TIN: {cust_tin}, {tin}, Purchase Code: {purchase_code}")

            # Get customer mobile
            customer_mobile = None
            contact_persons = invoice_data.get("contact_persons_details", [])
            if contact_persons:
                first_contact = contact_persons[0]
                customer_mobile = first_contact.get("mobile") or first_contact.get("phone")
            
            items = invoice_data.get("line_items", [])
            
            # Handle sales date
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
            
            # Build VSDC payload
            vsdc_payload = {
                "tin": tin,
                "bhfId": "00",
                "invcNo": invoice_no + random.randint(1, 1000),
                "orgInvcNo": 0,
                "custTin": cust_tin if cust_tin else None,
                "prcOrdCd": purchase_code if purchase_code else None,
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
            
            # Process items
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
            
            # Round amounts
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
    def transform_zoho_credit_note_to_vsdc(self, zoho_payload: dict) -> dict:
        try:
            credit_note = zoho_payload.get("creditnote", {})
            
            # Extract TINs
            custom_fields = credit_note.get("custom_fields", [])
            tin = next((f["value"] for f in custom_fields if f.get("api_name") == "cf_tn"), "000000000")
            customer_tin = next((f["value"] for f in custom_fields if f.get("api_name") == "cf_customer_tin"), None)
            
            credit_note_number = credit_note.get("creditnote_number", "CN0000")
            invoice_number = credit_note.get("invoices_credited", [{}])[0].get("invoice_number", "INV0000")
            customer_name = credit_note.get("customer_name", "Unknown Customer")
            items = credit_note.get("line_items", [])
            refund_date = credit_note.get("date", datetime.now().strftime("%Y-%m-%d"))
            
            invc_no = int(''.join(filter(str.isdigit, credit_note_number)) or random.randint(100000, 999999))
            org_invc_no = int(''.join(filter(str.isdigit, invoice_number)) or 0)
            
            # Totals
            taxbl_amt_b = 0
            tax_amt_b = 0
            total_amt = 0
            item_list = []
            
            for idx, item in enumerate(items, start=1):
                # Extract the exact same way as your working invoice transform
                price = float(item.get("rate", 0))
                quantity = float(item.get("quantity", 1))
                supply_amount = round(price * quantity, 2)
                
                # Use the imported calculate_tax function, not self.calculate_tax
                # This matches exactly what your working invoice transform does
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
                
                item_list.append(vsdc_item)
                taxbl_amt_b += supply_amount
                tax_amt_b += tax_amount
                total_amt += supply_amount
            
            vsdc_payload = {
                "tin": tin,
                "bhfId": "00",
                "invcNo": invc_no,
                "orgInvcNo": org_invc_no,
                "custTin": None,
                "prcOrdCd": None,
                "custNm": customer_name,
                "salesTyCd": "N",
                "rcptTyCd": "R",  # Refund receipt
                "pmtTyCd": "01",
                "salesSttsCd": "02",
                "cfmDt": datetime.now().strftime("%Y%m%d%H%M%S"),
                "salesDt": datetime.strptime(refund_date, "%Y-%m-%d").strftime("%Y%m%d"),
                "stockRlsDt": datetime.now().strftime("%Y%m%d%H%M%S"),
                "cnclReqDt": None,
                "cnclDt": None,
                "rfdDt": datetime.strptime(refund_date, "%Y-%m-%d").strftime("%Y%m%d%H%M%S"),
                "rfdRsnCd": "01",
                "totItemCnt": len(items),
                "taxblAmtA": 0,
                "taxblAmtB": round(taxbl_amt_b, 2),
                "taxblAmtC": 0,
                "taxblAmtD": 0,
                "taxRtA": 0,
                "taxRtB": 18,
                "taxRtC": 0,
                "taxRtD": 0,
                "taxAmtA": 0,
                "taxAmtB": round(tax_amt_b, 2),
                "taxAmtC": 0,
                "taxAmtD": 0,
                "totTaxblAmt": round(taxbl_amt_b, 2),
                "totTaxAmt": round(tax_amt_b, 2),
                "totAmt": round(total_amt, 2),  # Tax-exclusive total
                "prchrAcptcYn": "N",
                "remark": credit_note.get("notes", ""),
                "regrId": "11999",
                "regrNm": "TestVSDC",
                "modrId": "45678",
                "modrNm": "TestVSDC",
                "receipt": {
                    "custTin": customer_tin,
                    "custMblNo": credit_note.get("customer_mobile", "0795577896"),
                    "rptNo": 1,
                    "trdeNm": "Maryshop",
                    "adrs": "KICUKIRO-KABEZA",
                    "topMsg": "Maryshop",
                    "btmMsg": "Welcome",
                    "prchrAcptcYn": "N"
                },
                "itemList": item_list
            }
            
            return vsdc_payload
            
        except Exception as e:
            logger.error(f"Error transforming Zoho credit note: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to transform credit note: {str(e)}")
