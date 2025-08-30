#!/usr/bin/env python3
"""
Main FastAPI Application - Clean Architecture with Controller Pattern
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# Import services
from services.vsdc_service import VSSDCInvoiceService
from services.payload_transformer import PayloadTransformer
from services.pdf_service import PDFService
from config.settings import settings

# Import controllers
from controllers.v1.auth_controller import AuthController
from controllers.v1.webhook_controller import WebhookController
from controllers.v1.utility_controller import UtilityController
from controllers.v1.business_controller import BusinessController

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info("🚀 VSDC Integration API v2.0 - Clean Architecture")
    logger.info("📁 Architecture: Repository + Service + Controller pattern")
    logger.info(f"🔧 Services initialized: PDF, VSDC, PayloadTransformer")
    logger.info(f"🎯 Controllers registered: Auth, Webhook, Utility, Business")
    logger.info(f"☁️  Cloudinary configured: {settings.is_cloudinary_configured()}")
    logger.info(f"🔐 JWT configured: {bool(settings.JWT_SECRET_KEY)}")
    
    yield
    
    # Shutdown
    logger.info("🛑 VSDC Integration API shutting down")

# Initialize FastAPI app
app = FastAPI(
    title="VSDC Integration API - Clean Architecture",
    description="Clean architecture FastAPI application for Zoho to VSDC integration with repository pattern",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Initialize services (dependency injection)
pdf_service = PDFService()
vsdc_service = VSSDCInvoiceService(settings.cloudinary_config)
payload_transformer = PayloadTransformer(vsdc_service)

# Initialize controllers
auth_controller = AuthController()
webhook_controller = WebhookController(vsdc_service, payload_transformer)
utility_controller = UtilityController(pdf_service, vsdc_service, payload_transformer)
business_controller = BusinessController()

# Register controller routes
app.include_router(auth_controller.router)
app.include_router(webhook_controller.router)
app.include_router(utility_controller.router)
app.include_router(business_controller.router)

# Global error handler
@app.exception_handler(Exception)
async def handle_global_exception(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
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
