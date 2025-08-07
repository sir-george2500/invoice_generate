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

@app.post("/webhooks/zoho/invoice")
async def handle_zoho_webhook(request: Request):
    """Enhanced webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
    try:
        # Get the raw JSON payload
        zoho_payload = await request.json()
        logger.info(f"Received Zoho webhook payload")
        # Transform Zoho payload to VSDC format
        vsdc_payload = payload_transformer.transform_zoho_to_vsdc(zoho_payload)
        logger.info(f"Transformed to VSDC payload for invoice: {vsdc_payload['invcNo']}")
        
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
                    
                    # Generate advanced PDF with QR code
                    try:
                        pdf_result = await vsdc_service.generate_advanced_pdf(ebm_response, zoho_payload, vsdc_payload)
                        
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Webhook processed successfully with dynamic tax calculation",
                                "invoice_number": vsdc_payload["invcNo"],
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
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Webhook forwarded successfully but PDF generation failed",
                                "invoice_number": vsdc_payload["invcNo"],
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
        # Sample Zoho payload
        sample_zoho_payload = {
            "invoice": {
                "invoice_number": "INV-2024-001",
                "customer_name": "Test Customer Ltd",
                "date": "2024-06-21",
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
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Payload transformation test successful",
                "original_zoho_payload": sample_zoho_payload,
                "transformed_vsdc_payload": vsdc_payload,
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
            "download_pdf": "/download-pdf/{filename}",
            "list_pdfs": "/list-pdfs",
            "test_pdf": "/test/generate-advanced-pdf",
            "test_transform": "/test/transform-payload",
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
            "Modular service architecture"
        ],
        "endpoints": {
            "webhook": "POST /webhooks/zoho/invoice",
            "download": "GET /download-pdf/{filename}",
            "list_pdfs": "GET /list-pdfs",
            "health": "GET /health",
            "test_pdf": "POST /test/generate-advanced-pdf",
            "test_transform": "POST /test/transform-payload"
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

@app.post("/webhooks/zoho/credit-note")
async def handle_zoho_credit_note_webhook(request: Request):
    """Enhanced credit note webhook endpoint with dynamic tax calculation and proper VSDC error handling"""
    try:
        # Get the raw JSON payload
        zoho_payload = await request.json()
        logger.info(f"Received Zoho credit note webhook payload")
        # logger.info(f"Zoho credit note payload: {zoho_payload}")
        
        # Transform Zoho credit note payload to VSDC format
        vsdc_payload = payload_transformer.transform_zoho_credit_note_to_vsdc(zoho_payload)
        logger.info(f"Transformed to VSDC credit note payload for: {vsdc_payload['invcNo']}")

        # logger.info(vsdc_payload)
        
        # Forward to VSDC API (credit note endpoint)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.VSDC_API_URL,  # Different endpoint for credit notes
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
                    logger.info(f"Credit note successfully processed by VSDC API: {vsdc_payload['invcNo']}")
                    
                    # Generate credit note PDF with QR code
                    try:
                        pdf_result = await vsdc_service.generate_credit_note_pdf(ebm_response, zoho_payload, vsdc_payload)
                        
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Credit note webhook processed successfully with dynamic tax calculation",
                                "credit_note_number": vsdc_payload["invcNo"],
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
                        return JSONResponse(
                            status_code=200,
                            content={
                                "message": "Credit note webhook forwarded successfully but PDF generation failed",
                                "credit_note_number": vsdc_payload["invcNo"],
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
                        "credit_note_number": vsdc_payload["invcNo"],
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
