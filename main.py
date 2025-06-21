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
    """Enhanced webhook endpoint with dynamic tax calculation"""
    try:
        # Get the raw JSON payload
        zoho_payload = await request.json()
        logger.info(f"Received Zoho webhook payload")

          # Get the raw JSON payload
        zoho_payload = await request.json()
         
        
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
            
            if response.status_code == 200:
                ebm_response = response.json()

                # Log
                logger.info(f"Successfully forwarded to VSDC API: {ebm_response.get('invcNo')}")
                
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
                            "pdf_error": str(pdf_error)
                        }
                    )
            else:
                logger.error(f"Failed to forward to VSDC API: {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to forward to VSDC API: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

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

# @app.post("/test/generate-advanced-pdf")
# async def test_pdf_generation():
#     """Test the advanced PDF generation with sample data"""
#     try:
#         # Sample EBM response
#         sample_ebm_response = {
#             "tin": settings.VSDC_TIN,
#             "invcNo": 12345,
#             "custNm": "ALSM ADVISORY LTD",
#             "custTin": "118692892",
#             "totAmt": 85000.00,
#             "taxblAmtB": 85000.00,
#             "taxAmtB": 15300.00,
#             "totTaxAmt": 15300.00,
#             "itemList": [
#                 {
#                     "itemCd": "SRV001",
#                     "itemNm": "Software Development",
#                     "qty": 40,
#                     "taxTyCd": "B",
#                     "prc": 1500,
#                     "totAmt": 60000.00
#                 },
#                 {
#                     "itemCd": "SRV002",
#                     "itemNm": "System Integration",
#                     "qty": 1,
#                     "taxTyCd": "B",
#                     "prc": 25000,
#                     "totAmt": 25000.00
#                 }
#             ]
#         }
#
#         # Sample Zoho data
#         sample_zoho_data = {
#             "invoice": {
#                 "customer_name": "ALSM ADVISORY LTD",
#                 "invoice_number": "TEST-12345",
#                 "date": datetime.now().strftime("%Y-%m-%d")
#             }
#         }
#
#         # Generate advanced PDF
#         pdf_result = await vsdc_service.generate_advanced_pdf(sample_ebm_response, sample_zoho_data,vsdc_payload)
#
#         return JSONResponse(
#             status_code=200,
#             content={
#                 "message": "Advanced test PDF generated successfully",
#                 "pdf_generation": pdf_result,
#                 "download_url": f"/download-pdf/{pdf_result['pdf_filename']}"
#             }
#         )
        
#    except Exception as e:
#        logger.error(f"Error generating test PDF: {str(e)}")
 #       raise HTTPException(status_code=500, detail=f"Error generating test PDF: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
