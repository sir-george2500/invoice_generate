#!/usr/bin/env python3
"""
Main FastAPI Application - Clean and focused on routing
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import httpx
import logging
from datetime import datetime
import json
from typing import Optional

# Import services
from services.vsdc_service import VSSDCInvoiceService
from services.payload_transformer import PayloadTransformer
from services.pdf_service import PDFService
from config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VSDC Integration with Dynamic Tax Calculation",
    description="FastAPI application for Zoho to VSDC integration with advanced PDF generation",
    version="1.0.0"
)

# Initialize services
pdf_service = PDFService()
vsdc_service = VSSDCInvoiceService(settings.cloudinary_config)
payload_transformer = PayloadTransformer(vsdc_service)

def log_business_info(zoho_payload: dict, vsdc_payload: dict, document_type: str = "invoice"):
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

@app.post("/webhooks/zoho/invoice")
async def handle_zoho_webhook(request: Request):
    """Enhanced webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
    try:
        # Get the raw JSON payload
        zoho_payload = await request.json()
        logger.info(f"Received Zoho webhook payload")
        # log the payload 
        logger.info(zoho_payload)
        
        # Transform Zoho payload to VSDC format
        vsdc_payload = payload_transformer.transform_zoho_to_vsdc(zoho_payload)
        logger.info(f"Transformed to VSDC payload for invoice: {vsdc_payload['invcNo']}")
        
        # FIXED: Log business information for debugging
        log_business_info(zoho_payload, vsdc_payload, "invoice")
        
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
                    
                    # FIXED: Generate advanced PDF with QR code using corrected business info
                    try:
                        # Log what's being passed to PDF generation
                        invoice_data = zoho_payload.get("invoice", zoho_payload)
                        business_name = vsdc_payload.get("receipt", {}).get("trdeNm", settings.COMPANY_NAME)
                        logger.info(f"Generating PDF with business name: {business_name}")
                        
                        # ✅ UPDATED: Pass vsdc_payload as Optional[dict] - it can be None
                        pdf_result = await vsdc_service.generate_advanced_pdf(
                            ebm_response=ebm_response, 
                            zoho_data=zoho_payload, 
                            vsdc_payload=vsdc_payload  # This is now properly handled as Optional[dict]
                        )
                        
                        # Enhanced response with business info
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Webhook processed successfully with dynamic tax calculation",
                                "invoice_number": vsdc_payload["invcNo"],
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

@app.post("/webhooks/zoho/credit-note")
async def handle_zoho_credit_note_webhook(request: Request):
    """Enhanced credit note webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
    try:
        # Get the raw JSON payload
        zoho_payload = await request.json()
        logger.info(f"📥 Received Zoho credit note webhook payload")
        # logger.info(zoho_payload)
        
        # ✅ Enhanced payload structure logging
        logger.info(f"🔍 Credit note payload structure: {list(zoho_payload.keys())}")
        
        # ✅ Enhanced transformation with better error handling
        try:
            vsdc_payload = payload_transformer.transform_zoho_credit_note_to_vsdc(zoho_payload)
            logger.info(f"✅ Transformed to VSDC credit note payload for: {vsdc_payload['invcNo']}")
        except (IndexError, KeyError, ValueError, TypeError) as transform_error:
            logger.error(f"❌ Credit note transformation error: {str(transform_error)}")
            logger.error(f"❌ Zoho payload structure: {list(zoho_payload.keys())}")
            
            # Log credit note-specific structure
            if "creditnote" in zoho_payload:
                credit_note_data = zoho_payload["creditnote"]
                logger.error(f"❌ Credit note keys: {list(credit_note_data.keys())}")
                
                # Log invoices_credited specifically
                invoices_credited = credit_note_data.get("invoices_credited", "NOT_FOUND")
                logger.error(f"❌ invoices_credited: {invoices_credited}")
                logger.error(f"❌ invoices_credited type: {type(invoices_credited)}")
                
                if isinstance(invoices_credited, list):
                    logger.error(f"❌ invoices_credited length: {len(invoices_credited)}")
            
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
            logger.error(f"❌ Unexpected credit note transformation error: {str(transform_error)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Unexpected error during credit note transformation",
                    "error": str(transform_error),
                    "error_type": "internal_transformation_error",
                    "document_type": "credit_note"
                }
            )
        
        # FIXED: Log business information for debugging
        log_business_info(zoho_payload, vsdc_payload, "credit_note")
        
        # ✅ Enhanced VSDC API communication with better error handling
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.VSDC_API_URL,  # Same endpoint for credit notes
                    json=vsdc_payload,
                    timeout=30.0,
                    headers={"Content-Type": "application/json"}
                )
        except httpx.TimeoutException:
            logger.error(f"❌ VSDC API timeout for credit note: {vsdc_payload.get('invcNo', 'UNKNOWN')}")
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
            logger.error(f"❌ VSDC API request error for credit note: {str(req_error)}")
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
            except ValueError as e:
                logger.error(f"❌ Invalid JSON response from VSDC: {response.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Invalid JSON response from VSDC API: {str(e)}"
                )
            
            # Check VSDC result code (000 means success)
            result_code = ebm_response.get('resultCd', '999')
            result_message = ebm_response.get('resultMsg', 'Unknown error')
            
            if result_code == '000':
                # Success case
                logger.info(f"✅ Credit note successfully processed by VSDC API: {vsdc_payload['invcNo']}")
                
                # FIXED: Generate credit note PDF with QR code using corrected business info
                try:
                    # Log what's being passed to PDF generation
                    credit_note_data = zoho_payload.get("creditnote", zoho_payload)
                    business_name = vsdc_payload.get("receipt", {}).get("trdeNm", settings.COMPANY_NAME)
                    logger.info(f"🎯 Generating credit note PDF with business name: {business_name}")
                    
                    # ✅ UPDATED: Pass vsdc_payload as Optional[dict] - it can be None
                    pdf_result = await vsdc_service.generate_credit_note_pdf(
                        ebm_response=ebm_response, 
                        zoho_data=zoho_payload, 
                        vsdc_payload=vsdc_payload  # This is now properly handled as Optional[dict]
                    )
                    
                    # Enhanced response with business info
                    return JSONResponse(
                        status_code=200,
                        content={
                            "message": "Credit note webhook processed successfully with dynamic tax calculation",
                            "credit_note_number": vsdc_payload["invcNo"],
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
                    logger.error(f"❌ Error generating credit note PDF: {str(pdf_error)}")
                    logger.error(f"❌ Credit Note PDF Error Details: {pdf_error.__class__.__name__}: {str(pdf_error)}")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "message": "Credit note webhook forwarded successfully but PDF generation failed",
                            "credit_note_number": vsdc_payload["invcNo"],
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
                logger.error(f"❌ VSDC Credit Note API error - Code: {result_code}, Message: {result_message}")
                
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
            logger.error(f"❌ HTTP error from VSDC Credit Note API: {response.status_code} - {response.text}")
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
        logger.error(f"❌ Error processing credit note webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error while processing credit note webhook",
                "error": str(e),
                "error_type": "internal_credit_note_processing_error",
                "document_type": "credit_note"
            }
        )

@app.get("/download-pdf/{filename}")
async def serve_pdf_file(filename: str):
    """Download generated PDF invoice"""
    try:
        pdf_path = pdf_service.get_pdf_path(filename)
        logger.info(f"Serving PDF file: {filename}")
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except FileNotFoundError:
        available_files = pdf_service.get_available_files()
        raise HTTPException(
            status_code=404,
            detail=f"PDF file not found: {filename}. Available files: {available_files}"
        )
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")

@app.get("/list-pdfs")
async def get_pdf_list():
    """List all generated PDF files"""
    try:
        pdf_info = pdf_service.list_generated_pdfs()
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Found {len(pdf_info)} PDF files",
                "pdfs": pdf_info
            }
        )
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing PDFs: {str(e)}")

@app.post("/test/transform-payload")
async def test_payload_transform():
    """Test payload transformation with sample Zoho data"""
    try:
        # Sample Zoho payload with business info
        sample_zoho_payload = {
            "invoice": {
                "invoice_number": "INV-2024-001",
                "customer_name": "Test Customer Ltd",
                "date": "2024-06-21",
                "custom_field_hash": {
                    "cf_tin": "123456789",  # Business TIN
                    "cf_customer_tin": "987654321",  # Customer TIN
                    "cf_purchase_code": "PO-2024-001"
                },
                "line_items": [
                    {
                        "name": "Software License",
                        "description": "Annual software license",
                        "quantity": 1,
                        "rate": 118000,  # Price inclusive of 18% VAT
                        "tax_rate": 18,
                        "price_includes_tax": True
                    },
                    {
                        "name": "Support Services", 
                        "description": "Technical support",
                        "quantity": 12,
                        "rate": 5000,  # Price exclusive of VAT
                        "tax_rate": 18,
                        "price_includes_tax": False
                    }
                ]
            }
        }
        
        # Transform payload
        vsdc_payload = payload_transformer.transform_zoho_to_vsdc(sample_zoho_payload)
        
        # Log business info for testing
        log_business_info(sample_zoho_payload, vsdc_payload, "test")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Payload transformation test successful",
                "original_zoho_payload": sample_zoho_payload,
                "transformed_vsdc_payload": vsdc_payload,
                "business_info_extracted": {
                    "name": vsdc_payload.get("receipt", {}).get("trdeNm"),
                    "address": vsdc_payload.get("receipt", {}).get("adrs"),
                    "tin": vsdc_payload.get("tin")
                },
                "tax_summary": {
                    "total_taxable_a": f"{vsdc_payload['taxblAmtA']:,.2f}",
                    "total_taxable_b": f"{vsdc_payload['taxblAmtB']:,.2f}",
                    "total_tax_a": f"{vsdc_payload['taxAmtA']:,.2f}",
                    "total_tax_b": f"{vsdc_payload['taxAmtB']:,.2f}",
                    "total_amount": f"{vsdc_payload['totAmt']:,.2f}"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in payload transformation test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in payload transformation test: {str(e)}")

@app.post("/test/generate-pdf")
async def test_pdf_generation():
    """Test PDF generation with sample data (for cases where vsdc_payload might be None)"""
    try:
        # Sample EBM response
        sample_ebm_response = {
            "resultCd": "000",
            "resultMsg": "Success",
            "data": {
                "rcptNo": "20240001",
                "vsdcRcptPbctDate": "20240621120000",
                "sdcId": "SDC001",
                "mrcNo": "MRC001"
            }
        }
        
        # Sample Zoho data
        sample_zoho_data = {
            "invoice": {
                "invoice_number": "INV-2024-001",
                "customer_name": "Test Customer Ltd",
                "date": "2024-06-21",
                "sub_total": 100000,
                "tax_total": 18000,
                "custom_field_hash": {
                    "cf_organizationname": "Test Company Ltd",
                    "cf_seller_company_address": "Kigali, Rwanda",
                    "cf_seller_company_email": "test@company.com",
                    "cf_tin": "123456789",
                    "cf_customer_tin": "987654321"
                },
                "line_items": [
                    {
                        "description": "Test Service",
                        "quantity": 1,
                        "rate": 100000,
                        "tax_rate": 18
                    }
                ]
            }
        }
        
        # Test with vsdc_payload as None to verify the fix works
        pdf_result = await vsdc_service.generate_advanced_pdf(
            ebm_response=sample_ebm_response,
            zoho_data=sample_zoho_data,
            vsdc_payload=None  # Testing with None to verify type safety
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "PDF generation test successful (with vsdc_payload=None)",
                "pdf_result": pdf_result,
                "test_scenario": "vsdc_payload_none"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in PDF generation test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in PDF generation test: {str(e)}")

@app.get("/health")
async def api_health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "qr_generator_enabled": vsdc_service.qr_generator is not None,
        "cloudinary_configured": settings.is_cloudinary_configured(),
        "services": {
            "vsdc_service": "initialized",
            "payload_transformer": "initialized", 
            "pdf_service": "initialized"
        },
        "api_endpoints": {
            "webhook": "/webhooks/zoho/invoice",
            "credit_note_webhook": "/webhooks/zoho/credit-note",
            "download_pdf": "/download-pdf/{filename}",
            "list_pdfs": "/list-pdfs",
            "test_transform": "/test/transform-payload",
            "test_pdf": "/test/generate-pdf",
            "health": "/health"
        }
    }

@app.get("/")
async def api_root():
    """Root endpoint with API information"""
    return {
        "message": "VSDC Integration API with Dynamic Tax Calculation",
        "version": "1.0.0",
        "description": "FastAPI application for Zoho to VSDC integration",
        "features": [
            "Dynamic tax calculation",
            "Advanced PDF generation with QR codes",
            "Cloudinary integration for QR codes",
            "Comprehensive error handling",
            "Modular service architecture",
            "Business name extraction from Zoho data",
            "Type-safe vsdc_payload handling"
        ],
        "endpoints": {
            "webhook": "POST /webhooks/zoho/invoice",
            "credit_note_webhook": "POST /webhooks/zoho/credit-note",
            "download": "GET /download-pdf/{filename}",
            "list_pdfs": "GET /list-pdfs",
            "health": "GET /health",
            "test_transform": "POST /test/transform-payload",
            "test_pdf": "POST /test/generate-pdf"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }

# Error handlers
@app.exception_handler(Exception)
async def handle_global_exception(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
