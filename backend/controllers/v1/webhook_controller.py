from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging
import json
from datetime import datetime

from services.vsdc_service import VSSDCInvoiceService
from services.payload_transformer import PayloadTransformer
from config.settings import settings

logger = logging.getLogger(__name__)

class WebhookController:
    """Controller for webhook-related endpoints"""
    
    def __init__(self, vsdc_service: VSSDCInvoiceService, payload_transformer: PayloadTransformer):
        self.vsdc_service = vsdc_service
        self.payload_transformer = payload_transformer
        self.router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all webhook routes"""
        self.router.add_api_route(
            "/zoho/invoice", 
            self.handle_zoho_invoice_webhook, 
            methods=["POST"],
            summary="Process Zoho Invoice Webhook",
            description="Receives invoice data from Zoho, transforms it to VSDC format, and generates PDF with QR code",
            responses={
                200: {
                    "description": "Invoice processed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Webhook processed successfully",
                                "invoice_number": "INV-001",
                                "vsdc_receipt_number": "123456789",
                                "pdf_generation": {"status": "success"},
                                "download_url": "/download-pdf/invoice_123.pdf"
                            }
                        }
                    }
                },
                400: {"description": "Invalid request payload"},
                422: {"description": "VSDC business logic error"},
                502: {"description": "VSDC API communication error"},
                504: {"description": "VSDC API timeout"}
            }
        )
        self.router.add_api_route(
            "/zoho/credit-note", 
            self.handle_zoho_credit_note_webhook, 
            methods=["POST"],
            summary="Process Zoho Credit Note Webhook",
            description="Receives credit note data from Zoho, transforms it to VSDC format, and generates PDF with QR code",
            responses={
                200: {
                    "description": "Credit note processed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Credit note webhook processed successfully",
                                "credit_note_number": "CN-001",
                                "vsdc_receipt_number": "987654321",
                                "pdf_generation": {"status": "success"},
                                "download_url": "/download-pdf/credit_note_123.pdf"
                            }
                        }
                    }
                },
                400: {"description": "Invalid request payload or transformation error"},
                422: {"description": "VSDC business logic error"},
                502: {"description": "VSDC API communication error"},
                504: {"description": "VSDC API timeout"}
            }
        )
    
    def _log_vsdc_response_detailed(self, ebm_response: dict, document_type: str = "invoice"):
        """Log VSDC response in detail for debugging receipt numbers"""
        try:
            logger.info(f"=== VSDC RESPONSE ANALYSIS ({document_type.upper()}) ===")
            
            # Log the full response structure
            logger.info(f"Full VSDC Response: {json.dumps(ebm_response, indent=2)}")
            
            # Extract key fields
            result_code = ebm_response.get('resultCd', 'MISSING')
            result_message = ebm_response.get('resultMsg', 'MISSING')
            
            logger.info(f"Result Code: {result_code}")
            logger.info(f"Result Message: {result_message}")
            
            # Extract data section
            data_section = ebm_response.get('data', {})
            if data_section:
                logger.info(f"Data Section Present: Yes")
                logger.info(f"Data Section: {json.dumps(data_section, indent=2)}")
                
                # Key receipt fields
                rcpt_no = data_section.get('rcptNo', 'MISSING')
                sdc_id = data_section.get('sdcId', 'MISSING')
                mrc_no = data_section.get('mrcNo', 'MISSING')
                vsdc_date = data_section.get('vsdcRcptPbctDate', 'MISSING')
                
                logger.info(f"Receipt Number (rcptNo): {rcpt_no}")
                logger.info(f"SDC ID: {sdc_id}")
                logger.info(f"MRC Number: {mrc_no}")
                logger.info(f"VSDC Receipt Date: {vsdc_date}")
                
                # Check if receipt number is valid
                if rcpt_no and str(rcpt_no).strip() and rcpt_no != 'MISSING':
                    logger.info(f"Receipt Number Status: VALID")
                    logger.info(f"Receipt Number Type: {type(rcpt_no)}")
                    logger.info(f"Receipt Number Length: {len(str(rcpt_no))}")
                else:
                    logger.warning(f"Receipt Number Status: INVALID OR MISSING")
            else:
                logger.warning(f"Data Section Present: No")
                logger.warning(f"This is unusual for a successful VSDC response")
            
            # Tax information
            tax_amt_a = ebm_response.get('taxAmtA', 'N/A')
            tax_amt_b = ebm_response.get('taxAmtB', 'N/A')
            tot_tax_amt = ebm_response.get('totTaxAmt', 'N/A')
            
            logger.info(f"Tax Amount A: {tax_amt_a}")
            logger.info(f"Tax Amount B: {tax_amt_b}")
            logger.info(f"Total Tax Amount: {tot_tax_amt}")
            
            logger.info(f"=======================================")
            
        except Exception as e:
            logger.error(f"Error logging VSDC response: {str(e)}")

    def _log_business_info(self, zoho_payload: dict, vsdc_payload: dict, document_type: str = "invoice"):
        """Helper function to log business information for debugging"""
        try:
            invoice_data = zoho_payload.get("invoice", zoho_payload.get("creditnote", zoho_payload))
            
            # Extract business info from VSDC payload
            business_name = vsdc_payload.get("receipt", {}).get("trdeNm", "Not Found")
            business_address = vsdc_payload.get("receipt", {}).get("adrs", "Not Found")
            business_tin = vsdc_payload.get("tin", "Not Found")
            
            # Extract from Zoho data
            custom_field_hash = invoice_data.get("custom_field_hash", {})
            zoho_business_tin = custom_field_hash.get("cf_tin", "Not Found")
            
            logger.info(f"=== Business Info Debug ({document_type.upper()}) ===")
            logger.info(f"VSDC Business Name: {business_name}")
            logger.info(f"VSDC Business Address: {business_address}")
            logger.info(f"VSDC Business TIN: {business_tin}")
            logger.info(f"Zoho Business TIN: {zoho_business_tin}")
            logger.info(f"===================================")
            
        except Exception as e:
            logger.warning(f"Error logging business info: {str(e)}")

    async def handle_zoho_invoice_webhook(self, request: Request):
        """Enhanced webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
        try:
            # Get the raw JSON payload
            zoho_payload = await request.json()
            logger.info(f"Received Zoho webhook payload")
            
            # Transform Zoho payload to VSDC format
            vsdc_payload = self.payload_transformer.transform_zoho_to_vsdc(zoho_payload)
            logger.info(f"Transformed to VSDC payload for invoice: {vsdc_payload['invcNo']}")
            
            # Log business information for debugging
            self._log_business_info(zoho_payload, vsdc_payload, "invoice")
            
            # Forward to VSDC API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.VSDC_API_URL,
                    json=vsdc_payload,
                    timeout=30.0,
                    headers={"Content-Type": "application/json"}
                )
                
                # VSDC always returns HTTP 200, check resultCd in response body
                if response.status_code == 200:
                    try:
                        ebm_response = response.json()
                        
                        # Detailed VSDC response logging
                        self._log_vsdc_response_detailed(ebm_response, "invoice")
                        
                        # Log VSDC data for QR code generation
                        data_section = ebm_response.get("data", {})
                        logger.info(f"VSDC QR Data Available:")
                        logger.info(f"  - Internal Data: '{data_section.get('intrlData', 'MISSING')}'")
                        logger.info(f"  - Receipt Signature: '{data_section.get('rcptSign', 'MISSING')}'")
                        logger.info(f"  - Receipt Number: '{data_section.get('rcptNo', 'MISSING')}'")
                        logger.info(f"  - SDC ID: '{data_section.get('sdcId', 'MISSING')}'")
                        
                        # Check if we have enough data for URL-based QR codes
                        has_internal_data = bool(data_section.get('intrlData', '').strip())
                        has_signature = bool(data_section.get('rcptSign', '').strip())
                        logger.info(f"QR URL Generation Possible: {has_internal_data or has_signature}")
                        
                    except ValueError as e:
                        logger.error(f"Invalid JSON response from VSDC: {response.text}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"Invalid JSON response from VSDC API: {str(e)}"
                        )
                    
                    # Check VSDC result code (000 means success)
                    result_code = ebm_response.get('resultCd', '999')
                    result_message = ebm_response.get('resultMsg', 'Unknown error')
                    
                    if result_code == '000':
                        # Success case
                        logger.info(f"Successfully processed by VSDC API: {vsdc_payload['invcNo']}")
                        
                        # Generate advanced PDF with QR code using corrected business info
                        try:
                            # Log what's being passed to PDF generation
                            invoice_data = zoho_payload.get("invoice", zoho_payload)
                            business_name = vsdc_payload.get("receipt", {}).get("trdeNm", settings.COMPANY_NAME)
                            logger.info(f"Generating PDF with business name: {business_name}")
                            
                            pdf_result = await self.vsdc_service.generate_advanced_pdf(
                                ebm_response=ebm_response, 
                                zoho_data=zoho_payload, 
                                vsdc_payload=vsdc_payload
                            )
                            
                            # Enhanced response with business info
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "message": "Webhook processed successfully with dynamic tax calculation",
                                    "invoice_number": vsdc_payload["invcNo"],
                                    "vsdc_receipt_number": ebm_response.get("data", {}).get("rcptNo", "NOT_PROVIDED"),
                                    "business_info": {
                                        "name": business_name,
                                        "tin": vsdc_payload.get("tin"),
                                        "address": vsdc_payload.get("receipt", {}).get("adrs")
                                    },
                                    "vsdc_response": ebm_response,
                                    "pdf_generation": pdf_result,
                                    "download_url": f"/download-pdf/{pdf_result['pdf_filename']}",
                                    "tax_summary": {
                                        "total_tax_a": f"{ebm_response.get('taxAmtA', 0):,.2f}",
                                        "total_tax_b": f"{ebm_response.get('taxAmtB', 0):,.2f}",
                                        "total_tax": f"{ebm_response.get('totTaxAmt', 0):,.2f}"
                                    }
                                }
                            )
                            
                        except Exception as pdf_error:
                            logger.error(f"Error generating advanced PDF: {str(pdf_error)}")
                            logger.error(f"PDF Error Details: {pdf_error.__class__.__name__}: {str(pdf_error)}")
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "message": "Webhook forwarded successfully but PDF generation failed",
                                    "invoice_number": vsdc_payload["invcNo"],
                                    "vsdc_receipt_number": ebm_response.get("data", {}).get("rcptNo", "NOT_PROVIDED"),
                                    "business_info": {
                                        "name": vsdc_payload.get("receipt", {}).get("trdeNm"),
                                        "tin": vsdc_payload.get("tin")
                                    },
                                    "vsdc_response": ebm_response,
                                    "pdf_error": str(pdf_error),
                                    "tax_summary": {
                                        "total_tax_a": f"{ebm_response.get('taxAmtA', 0):,.2f}",
                                        "total_tax_b": f"{ebm_response.get('taxAmtB', 0):,.2f}",
                                        "total_tax": f"{ebm_response.get('totTaxAmt', 0):,.2f}"
                                    }
                                }
                            )
                    else:
                        # VSDC API returned an error
                        logger.error(f"VSDC API error - Code: {result_code}, Message: {result_message}")
                        
                        # Map common VSDC error codes to appropriate HTTP status codes
                        error_mapping = {
                            '881': 400,  # Purchase is mandatory
                            '882': 400,  # Purchase code is invalid
                            '883': 409,  # Purchase already used
                            '884': 400,  # Invalid customer TIN
                            '901': 401,  # Not valid device
                            '910': 400,  # Request parameter error
                            '921': 422,  # Sales data cannot be received
                            '922': 422,  # Sales invoice data can be received after sales data
                            '994': 409,  # Overlapped data
                        }
                        
                        http_status = error_mapping.get(result_code, 422)  # Default to 422 for unprocessable entity
                        
                        return JSONResponse(
                            status_code=http_status,
                            content={
                                "message": "VSDC API processing failed",
                                "invoice_number": vsdc_payload["invcNo"],
                                "vsdc_error": {
                                    "code": result_code,
                                    "message": result_message,
                                    "full_response": ebm_response
                                },
                                "error_type": "vsdc_business_logic_error"
                            }
                        )
                else:
                    # HTTP-level error (network, server down, etc.)
                    logger.error(f"HTTP error from VSDC API: {response.status_code} - {response.text}")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "message": "Failed to communicate with VSDC API",
                            "invoice_number": vsdc_payload["invcNo"],
                            "http_error": {
                                "status_code": response.status_code,
                                "response_text": response.text
                            },
                            "error_type": "vsdc_communication_error"
                        }
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal server error while processing webhook",
                    "error": str(e),
                    "error_type": "internal_processing_error"
                }
            )

    async def handle_zoho_credit_note_webhook(self, request: Request):
        """Enhanced credit note webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
        try:
            # Get the raw JSON payload
            zoho_payload = await request.json()
            logger.info(f"Received Zoho credit note webhook payload")
            
            # Enhanced payload structure logging
            logger.info(f"Credit note payload structure: {list(zoho_payload.keys())}")
            
            # Enhanced transformation with better error handling
            try:
                vsdc_payload = self.payload_transformer.transform_zoho_credit_note_to_vsdc(zoho_payload)
                logger.info(f"Transformed to VSDC credit note payload for: {vsdc_payload['invcNo']}")
            except (IndexError, KeyError, ValueError, TypeError) as transform_error:
                logger.error(f"Credit note transformation error: {str(transform_error)}")
                logger.error(f"Zoho payload structure: {list(zoho_payload.keys())}")
                
                # Log credit note-specific structure
                if "creditnote" in zoho_payload:
                    credit_note_data = zoho_payload["creditnote"]
                    logger.error(f"Credit note keys: {list(credit_note_data.keys())}")
                    
                    # Log invoices_credited specifically
                    invoices_credited = credit_note_data.get("invoices_credited", "NOT_FOUND")
                    logger.error(f"invoices_credited: {invoices_credited}")
                    logger.error(f"invoices_credited type: {type(invoices_credited)}")
                    
                    if isinstance(invoices_credited, list):
                        logger.error(f"invoices_credited length: {len(invoices_credited)}")
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Failed to transform credit note payload",
                        "error": str(transform_error),
                        "error_type": "credit_note_transformation_error",
                        "payload_keys": list(zoho_payload.keys()),
                        "document_type": "credit_note"
                    }
                )
            except Exception as transform_error:
                logger.error(f"Unexpected credit note transformation error: {str(transform_error)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Unexpected error during credit note transformation",
                        "error": str(transform_error),
                        "error_type": "internal_transformation_error",
                        "document_type": "credit_note"
                    }
                )
            
            # Log business information for debugging
            self._log_business_info(zoho_payload, vsdc_payload, "credit_note")
            
            # Enhanced VSDC API communication with better error handling
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        settings.VSDC_API_URL,  # Same endpoint for credit notes
                        json=vsdc_payload,
                        timeout=30.0,
                        headers={"Content-Type": "application/json"}
                    )
            except httpx.TimeoutException:
                logger.error(f"VSDC API timeout for credit note: {vsdc_payload.get('invcNo', 'UNKNOWN')}")
                return JSONResponse(
                    status_code=504,
                    content={
                        "message": "VSDC API request timeout",
                        "credit_note_number": vsdc_payload.get("invcNo", "UNKNOWN"),
                        "error_type": "vsdc_timeout_error",
                        "document_type": "credit_note"
                    }
                )
            except httpx.RequestError as req_error:
                logger.error(f"VSDC API request error for credit note: {str(req_error)}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "message": "Failed to connect to VSDC API",
                        "credit_note_number": vsdc_payload.get("invcNo", "UNKNOWN"),
                        "error": str(req_error),
                        "error_type": "vsdc_connection_error",
                        "document_type": "credit_note"
                    }
                )
            
            # VSDC always returns HTTP 200, check resultCd in response body
            if response.status_code == 200:
                try:
                    ebm_response = response.json()
                    
                    # Detailed VSDC response logging for credit notes
                    self._log_vsdc_response_detailed(ebm_response, "credit_note")
                    
                    # Log VSDC data for QR code generation (credit notes)
                    data_section = ebm_response.get("data", {})
                    logger.info(f"VSDC Credit Note QR Data Available:")
                    logger.info(f"  - Internal Data: '{data_section.get('intrlData', 'MISSING')}'")
                    logger.info(f"  - Receipt Signature: '{data_section.get('rcptSign', 'MISSING')}'")
                    logger.info(f"  - Receipt Number: '{data_section.get('rcptNo', 'MISSING')}'")
                    
                    # Check if we have enough data for URL-based QR codes
                    has_internal_data = bool(data_section.get('intrlData', '').strip())
                    has_signature = bool(data_section.get('rcptSign', '').strip())
                    logger.info(f"Credit Note QR URL Generation Possible: {has_internal_data or has_signature}")
                    
                except ValueError as e:
                    logger.error(f"Invalid JSON response from VSDC: {response.text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Invalid JSON response from VSDC API: {str(e)}"
                    )
                
                # Check VSDC result code (000 means success)
                result_code = ebm_response.get('resultCd', '999')
                result_message = ebm_response.get('resultMsg', 'Unknown error')
                
                if result_code == '000':
                    # Success case
                    logger.info(f"Credit note successfully processed by VSDC API: {vsdc_payload['invcNo']}")
                    
                    # Generate credit note PDF with QR code using corrected business info
                    try:
                        # Log what's being passed to PDF generation
                        credit_note_data = zoho_payload.get("creditnote", zoho_payload)
                        business_name = vsdc_payload.get("receipt", {}).get("trdeNm", settings.COMPANY_NAME)
                        logger.info(f"Generating credit note PDF with business name: {business_name}")
                        
                        pdf_result = await self.vsdc_service.generate_credit_note_pdf(
                            ebm_response=ebm_response, 
                            zoho_data=zoho_payload, 
                            vsdc_payload=vsdc_payload
                        )
                        
                        # Enhanced response with business info
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Credit note webhook processed successfully with dynamic tax calculation",
                                "credit_note_number": vsdc_payload["invcNo"],
                                "vsdc_receipt_number": ebm_response.get("data", {}).get("rcptNo", "NOT_PROVIDED"),
                                "business_info": {
                                    "name": business_name,
                                    "tin": vsdc_payload.get("tin"),
                                    "address": vsdc_payload.get("receipt", {}).get("adrs")
                                },
                                "vsdc_response": ebm_response,
                                "pdf_generation": pdf_result,
                                "download_url": f"/download-pdf/{pdf_result['pdf_filename']}",
                                "tax_summary": {
                                    "refund_tax_a": f"{abs(ebm_response.get('taxAmtA', 0)):,.2f}",
                                    "refund_tax_b": f"{abs(ebm_response.get('taxAmtB', 0)):,.2f}",
                                    "total_refund_tax": f"{abs(ebm_response.get('totTaxAmt', 0)):,.2f}"
                                },
                                "document_type": "credit_note"
                            }
                        )
                        
                    except Exception as pdf_error:
                        logger.error(f"Error generating credit note PDF: {str(pdf_error)}")
                        logger.error(f"Credit Note PDF Error Details: {pdf_error.__class__.__name__}: {str(pdf_error)}")
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Credit note webhook forwarded successfully but PDF generation failed",
                                "credit_note_number": vsdc_payload["invcNo"],
                                "vsdc_receipt_number": ebm_response.get("data", {}).get("rcptNo", "NOT_PROVIDED"),
                                "business_info": {
                                    "name": vsdc_payload.get("receipt", {}).get("trdeNm"),
                                    "tin": vsdc_payload.get("tin")
                                },
                                "vsdc_response": ebm_response,
                                "pdf_error": str(pdf_error),
                                "tax_summary": {
                                    "refund_tax_a": f"{abs(ebm_response.get('taxAmtA', 0)):,.2f}",
                                    "refund_tax_b": f"{abs(ebm_response.get('taxAmtB', 0)):,.2f}",
                                    "total_refund_tax": f"{abs(ebm_response.get('totTaxAmt', 0)):,.2f}"
                                },
                                "document_type": "credit_note"
                            }
                        )
                else:
                    # VSDC API returned an error
                    logger.error(f"VSDC Credit Note API error - Code: {result_code}, Message: {result_message}")
                    
                    # Map common VSDC error codes to appropriate HTTP status codes
                    # Credit notes might have specific error codes
                    error_mapping = {
                        '881': 400,  # Purchase is mandatory
                        '882': 400,  # Purchase code is invalid
                        '883': 409,  # Purchase already used
                        '884': 400,  # Invalid customer TIN
                        '885': 400,  # Original invoice not found (credit note specific)
                        '886': 409,  # Credit note already exists for this invoice
                        '901': 401,  # Not valid device
                        '910': 400,  # Request parameter error
                        '921': 422,  # Sales data cannot be received
                        '922': 422,  # Sales invoice data can be received after sales data
                        '923': 400,  # Invalid refund amount (exceeds original invoice)
                        '994': 409,  # Overlapped data
                    }
                    
                    http_status = error_mapping.get(result_code, 422)  # Default to 422 for unprocessable entity
                    
                    return JSONResponse(
                        status_code=http_status,
                        content={
                            "message": "VSDC Credit Note API processing failed",
                            "credit_note_number": vsdc_payload["invcNo"],
                            "vsdc_error": {
                                "code": result_code,
                                "message": result_message,
                                "full_response": ebm_response
                            },
                            "error_type": "vsdc_credit_note_business_logic_error",
                            "document_type": "credit_note"
                        }
                    )
            else:
                # HTTP-level error (network, server down, etc.)
                logger.error(f"HTTP error from VSDC Credit Note API: {response.status_code} - {response.text}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "message": "Failed to communicate with VSDC Credit Note API",
                        "credit_note_number": vsdc_payload.get("invcNo", "UNKNOWN"),
                        "http_error": {
                            "status_code": response.status_code,
                            "response_text": response.text
                        },
                        "error_type": "vsdc_credit_note_communication_error",
                        "document_type": "credit_note"
                    }
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing credit note webhook: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal server error while processing credit note webhook",
                    "error": str(e),
                    "error_type": "internal_credit_note_processing_error",
                    "document_type": "credit_note"
                }
            )
