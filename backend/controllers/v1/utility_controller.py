from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
import logging
from datetime import datetime

from services.pdf_service import PDFService
from services.vsdc_service import VSSDCInvoiceService
from services.payload_transformer import PayloadTransformer
from config.settings import settings

logger = logging.getLogger(__name__)

class UtilityController:
    """Controller for PDF downloads, health checks, and test endpoints"""
    
    def __init__(self, pdf_service: PDFService, vsdc_service: VSSDCInvoiceService, payload_transformer: PayloadTransformer):
        self.pdf_service = pdf_service
        self.vsdc_service = vsdc_service
        self.payload_transformer = payload_transformer
        self.router = APIRouter(tags=["Utilities"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all utility routes"""
        # PDF endpoints
        self.router.add_api_route(
            "/download-pdf/{filename}", 
            self.serve_pdf_file, 
            methods=["GET"],
            summary="Download PDF File",
            description="Download a generated PDF invoice or credit note by filename",
            responses={
                200: {
                    "description": "PDF file downloaded successfully",
                    "content": {"application/pdf": {}}
                },
                404: {"description": "PDF file not found"},
                500: {"description": "Error downloading PDF file"}
            }
        )
        self.router.add_api_route(
            "/api/v1/pdfs/list", 
            self.get_pdf_list, 
            methods=["GET"],
            summary="List Generated PDFs",
            description="Get a list of all generated PDF files with metadata",
            responses={
                200: {
                    "description": "List of PDF files retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Found 5 PDF files",
                                "pdfs": [
                                    {
                                        "filename": "invoice_123.pdf",
                                        "size": "245KB",
                                        "created": "2024-06-21T10:30:00"
                                    }
                                ]
                            }
                        }
                    }
                },
                500: {"description": "Error listing PDF files"}
            }
        )
        
        # Health and info endpoints
        self.router.add_api_route(
            "/health", 
            self.api_health_check, 
            methods=["GET"],
            summary="Health Check",
            description="Check the health status of the API and all its services",
            responses={
                200: {
                    "description": "Service is healthy",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "healthy",
                                "timestamp": "2024-06-21T10:30:00",
                                "services": {
                                    "vsdc_service": "initialized",
                                    "pdf_service": "initialized"
                                }
                            }
                        }
                    }
                }
            }
        )
        self.router.add_api_route(
            "/", 
            self.api_root, 
            methods=["GET"],
            summary="API Information",
            description="Get information about the API, its features, and available endpoints",
            responses={
                200: {
                    "description": "API information retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "VSDC Integration API",
                                "version": "2.0.0",
                                "features": ["Dynamic tax calculation", "PDF generation"],
                                "documentation": {
                                    "swagger_ui": "/docs",
                                    "redoc": "/redoc"
                                }
                            }
                        }
                    }
                }
            }
        )
        
        # Test endpoints
        self.router.add_api_route(
            "/api/v1/test/transform-payload", 
            self.test_payload_transform, 
            methods=["POST"],
            summary="Test Payload Transformation",
            description="Test the transformation of Zoho payload to VSDC format with sample data",
            responses={
                200: {
                    "description": "Payload transformation test completed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "Payload transformation test successful",
                                "original_zoho_payload": {},
                                "transformed_vsdc_payload": {},
                                "tax_summary": {
                                    "total_amount": "118,000.00"
                                }
                            }
                        }
                    }
                },
                500: {"description": "Error in payload transformation test"}
            }
        )
        self.router.add_api_route(
            "/api/v1/test/generate-pdf", 
            self.test_pdf_generation, 
            methods=["POST"],
            summary="Test PDF Generation",
            description="Test PDF generation with sample invoice data",
            responses={
                200: {
                    "description": "PDF generation test completed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "PDF generation test successful",
                                "pdf_result": {
                                    "status": "success",
                                    "filename": "test_invoice.pdf"
                                }
                            }
                        }
                    }
                },
                500: {"description": "Error in PDF generation test"}
            }
        )
        self.router.add_api_route(
            "/api/v1/test/validate-qr", 
            self.test_qr_validation, 
            methods=["POST"],
            summary="Test QR Code Validation",
            description="Test QR code generation and validation with sample data",
            responses={
                200: {
                    "description": "QR validation test completed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "QR code validation completed",
                                "validation_result": {
                                    "status": "valid",
                                    "qr_type": "url"
                                }
                            }
                        }
                    }
                },
                400: {"description": "QR generator not available"},
                500: {"description": "QR validation test failed"}
            }
        )
        self.router.add_api_route(
            "/api/v1/test/qr-content", 
            self.test_qr_content, 
            methods=["POST"],
            summary="Test QR Code Content Generation",
            description="Test QR code content generation without uploading to Cloudinary",
            responses={
                200: {
                    "description": "QR content generation test completed successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "message": "QR code content generated",
                                "qr_content": "Sample QR content...",
                                "content_length": 256
                            }
                        }
                    }
                },
                400: {"description": "QR generator not available"},
                500: {"description": "QR content test failed"}
            }
        )
        
        # Mock endpoint
        self.router.add_api_route(
            "/mock/vsdc/api", 
            self.mock_vsdc_api, 
            methods=["POST"],
            summary="Mock VSDC API",
            description="Mock VSDC API endpoint for testing - returns a successful response",
            responses={
                200: {
                    "description": "Mock VSDC response",
                    "content": {
                        "application/json": {
                            "example": {
                                "resultCd": "000",
                                "resultMsg": "Success",
                                "data": {
                                    "rcptNo": "123",
                                    "intrlData": "MOCK-DATA-FOR-TESTING"
                                }
                            }
                        }
                    }
                }
            }
        )
    
    async def serve_pdf_file(self, filename: str):
        """Download generated PDF invoice"""
        try:
            pdf_path = self.pdf_service.get_pdf_path(filename)
            logger.info(f"Serving PDF file: {filename}")
            return FileResponse(
                pdf_path,
                media_type='application/pdf',
                filename=filename,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except FileNotFoundError:
            available_files = self.pdf_service.get_available_files()
            raise HTTPException(
                status_code=404,
                detail=f"PDF file not found: {filename}. Available files: {available_files}"
            )
        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")

    async def get_pdf_list(self):
        """List all generated PDF files"""
        try:
            pdf_info = self.pdf_service.list_generated_pdfs()
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

    async def test_payload_transform(self):
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
            vsdc_payload = self.payload_transformer.transform_zoho_to_vsdc(sample_zoho_payload)
            
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

    async def test_pdf_generation(self):
        """Test PDF generation with sample data"""
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
            pdf_result = await self.vsdc_service.generate_advanced_pdf(
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

    async def test_qr_validation(self):
        """Test QR code generation and validation"""
        try:
            # Sample invoice data for testing
            sample_invoice_data = {
                "client_name": "uwase nicaise",
                "company_name": "Test Company Ltd",
                "company_address": "Kigali, Rwanda",
                "company_tel": "0785757324",
                "company_email": "test@company.com",
                "company_tin": "944000008",
                "client_tin": "998000003",
                "invoice_date": "25-08-2025",
                "invoice_time": "15:42:17",
                "sdc_id": "SDC010013744",
                "vsdc_receipt_no": "91",
                "receipt_number": "91",
                "vsdc_internal_data": "IKBT-G5VU-MWVE-YXO4-C6UX-3PJV-AM",
                "vsdc_receipt_signature": "IOSO-NK3N-CTNT-7BBF",
                "vsdc_receipt_date": "00:00:00",
                "mrc": "WIS00004019",
                "invoice_number": "91",
                "total_rwf": "100,000.00",
                "total_b": "100,000.00",
                "total_tax_b": "15,254.24",
                "total_tax": "15,254.24",
                "items": [
                    {
                        "code": "RW1NTXU00001",
                        "description": "Test Service",
                        "quantity": "1.00",
                        "tax": "B",
                        "unit_price": "100,000.00",
                        "total_price": "100,000.00"
                    }
                ]
            }
            
            # Generate and validate QR code
            if self.vsdc_service.qr_generator:
                validation_result = self.vsdc_service.qr_generator.validate_generated_qr(sample_invoice_data)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "QR code validation completed",
                        "validation_result": validation_result,
                        "sample_data_used": sample_invoice_data
                    }
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "QR generator not available - check Cloudinary configuration",
                        "cloudinary_configured": settings.is_cloudinary_configured()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error in QR validation test: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "QR validation test failed",
                    "error": str(e)
                }
            )

    async def test_qr_content(self):
        """Test QR code content generation without uploading"""
        try:
            # Sample invoice data
            sample_invoice_data = {
                "client_name": "CODACE",
                "company_name": "JEAN MARIE NTIGINAMA",
                "company_address": "Gasabo MUHIMA NYARUGENGE KIGALI CITY",
                "company_tel": "0788672640",
                "company_email": "ntiginamajm@gmail.com",
                "company_tin": "101412555",
                "client_tin": "101407029",
                "invoice_date": "11/03/2024",
                "invoice_time": "13:00:03",
                "sdc_id": "SDC012003144",
                "vsdc_receipt_no": "22",
                "receipt_number": "22",
                "vsdc_internal_data": "YK5Z-DZBT-SPLC-YLCA-LR3N-BZDM-QM",
                "vsdc_receipt_signature": "ZPKR-T6GD-55DG-TZBM",
                "vsdc_receipt_date": "11/03/2024 13:00:03",
                "mrc": "WIS00045236",
                "invoice_number": "22",
                "total_rwf": "320,073",
                "total_aex": "0",
                "total_b": "0",
                "total_tax_a": "0",
                "total_tax_b": "0",
                "total_tax": "0",
                "items": [
                    {
                        "code": "RW3NTXNOX00001",
                        "description": "TRANSPORT SERVICES",
                        "quantity": "1",
                        "tax": "D",
                        "unit_price": "320,073",
                        "total_price": "320,073"
                    }
                ]
            }
            
            # Generate QR content
            if self.vsdc_service.qr_generator:
                qr_content = self.vsdc_service.qr_generator.generate_invoice_qr_data_text_fallback(sample_invoice_data)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "QR code content generated",
                        "qr_content": qr_content,
                        "content_length": len(qr_content),
                        "sample_data_used": sample_invoice_data
                    }
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "QR generator not available - check Cloudinary configuration",
                        "cloudinary_configured": settings.is_cloudinary_configured()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error in QR content test: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": "QR content test failed",
                    "error": str(e)
                }
            )

    async def mock_vsdc_api(self, request: Request):
        """Mock VSDC API endpoint for testing - returns a successful response"""
        try:
            payload = await request.json()
            logger.info(f"Mock VSDC API received payload for invoice: {payload.get('invcNo', 'Unknown')}")
            
            # Mock successful VSDC response
            mock_response = {
                "resultCd": "000",
                "resultMsg": "Success",
                "data": {
                    "rcptNo": str(payload.get('invcNo', '1')),
                    "totRcptNo": "1",
                    "intrlData": "MOCK-DATA-FOR-TESTING-ONLY-ABCD-EFGH",
                    "rcptSign": "MOCK-SIGN-TEST-1234",
                    "vsdcRcptPbctDate": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "sdcId": payload.get('tin', settings.VSDC_SDC_ID),
                    "mrcNo": settings.VSDC_MRC
                },
                "taxAmtA": payload.get('taxAmtA', 0),
                "taxAmtB": payload.get('taxAmtB', 0),
                "totTaxAmt": payload.get('totTaxAmt', 0)
            }
            
            logger.info(f"Mock VSDC API returning success for invoice: {payload.get('invcNo')}")
            return JSONResponse(
                status_code=200,
                content=mock_response
            )
            
        except Exception as e:
            logger.error(f"Mock VSDC API error: {str(e)}")
            return JSONResponse(
                status_code=200,
                content={
                    "resultCd": "999",
                    "resultMsg": f"Mock API Error: {str(e)}",
                    "data": {}
                }
            )

    async def api_health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "qr_generator_enabled": self.vsdc_service.qr_generator is not None,
            "cloudinary_configured": settings.is_cloudinary_configured(),
            "services": {
                "vsdc_service": "initialized",
                "payload_transformer": "initialized", 
                "pdf_service": "initialized"
            },
            "api_endpoints": {
                "webhook": "/api/v1/webhooks/zoho/invoice",
                "credit_note_webhook": "/api/v1/webhooks/zoho/credit-note",
                "auth": "/api/v1/auth/*",
                "download_pdf": "/download-pdf/{filename}",
                "list_pdfs": "/api/v1/pdfs/list",
                "test_endpoints": "/api/v1/test/*",
                "health": "/health"
            }
        }

    async def api_root(self):
        """Root endpoint with API information"""
        return {
            "message": "VSDC Integration API with Dynamic Tax Calculation",
            "version": "2.0.0",
            "description": "Clean architecture FastAPI application for Zoho to VSDC integration",
            "architecture": {
                "pattern": "Repository + Service + Controller",
                "version": "v1",
                "structure": "Clean separation of concerns"
            },
            "features": [
                "Dynamic tax calculation",
                "Advanced PDF generation with QR codes",
                "Cloudinary integration for QR codes",
                "Comprehensive error handling",
                "Repository pattern for data access",
                "Service layer for business logic",
                "Controller layer for HTTP handling",
                "JWT authentication with user management"
            ],
            "api_structure": {
                "auth": "POST /api/v1/auth/{login,register,me,verify}",
                "webhooks": "POST /api/v1/webhooks/zoho/{invoice,credit-note}",
                "pdfs": "GET /api/v1/pdfs/list",
                "tests": "POST /api/v1/test/{transform-payload,generate-pdf,validate-qr,qr-content}",
                "utilities": "GET /{health,download-pdf}"
            },
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            }
        }
