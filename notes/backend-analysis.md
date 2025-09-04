# Backend System Analysis

## System Overview

This is a **FastAPI-based invoice generation and tax compliance system** designed to integrate Zoho CRM with Rwanda's VSDC (Virtual Sales Device Controller) system for tax-compliant invoice processing.

## Application Type & Architecture

### Core Technology Stack
- **Framework**: FastAPI 0.115.11 (Modern Python web framework)
- **Database**: PostgreSQL with SQLAlchemy 2.0.39 ORM + Alembic migrations
- **Authentication**: JWT with PyJWT 2.8.0 + bcrypt password hashing
- **PDF Generation**: WeasyPrint 65.1 + custom invoice templates
- **QR Codes**: qrcode 8.2 library + Cloudinary hosting
- **Async Support**: httpx for external API calls, databases for async DB operations
- **Architecture Pattern**: Clean Architecture with Repository + Service + Controller layers

### Design Patterns Used
1. **Repository Pattern**: Data access layer abstraction (`repositories/`)
2. **Service Layer Pattern**: Business logic separation (`services/`)
3. **Controller Pattern**: API endpoint handling (`controllers/v1/`)
4. **Dependency Injection**: Service initialization in main app
5. **Factory Pattern**: Model creation and transformation services
6. **Strategy Pattern**: Multiple QR code generation strategies

## Main Entry Points

### Primary Entry Point
**File**: `main.py`
- **Purpose**: FastAPI application initialization with clean architecture
- **Features**: 
  - Service dependency injection
  - Global exception handling
  - CORS middleware for Zoho integration
  - Application lifespan management
  - Health check endpoints

### Key Initialization Services
```python
# Service Layer Initialization
pdf_service = PDFService()
vsdc_service = VSSDCInvoiceService(settings.cloudinary_config)
payload_transformer = PayloadTransformer(vsdc_service)

# Controller Initialization with DI
webhook_controller = WebhookController(vsdc_service, payload_transformer)
utility_controller = UtilityController(pdf_service, vsdc_service, payload_transformer)
```

## Key Files & Their Purposes

### Configuration & Settings
- **`config/settings.py`**: Application configuration with environment variable management
- **`database/connection.py`**: SQLAlchemy database connection and session management
- **`requirements.txt`**: Comprehensive dependency list (99 packages)

### Models & Database
- **`models/base.py`**: SQLAlchemy declarative base
- **`models/user.py`**: User authentication model + password reset OTP
- **`models/business.py`**: Business/tenant model with Zoho integration
- **`models/transaction.py`**: Transaction records + daily reports
- **`models/webhook_activity.py`**: Webhook processing audit trail

### Data Access Layer
- **`repositories/user_repository.py`**: User CRUD operations
- **`repositories/business_repository.py`**: Business management operations
- **`repositories/transaction_repository.py`**: Transaction data access
- **`repositories/webhook_activity_repository.py`**: Webhook audit operations

### Business Logic Services
- **`services/vsdc_service.py`**: VSDC integration and PDF generation
- **`services/payload_transformer.py`**: Zoho to VSDC data transformation
- **`services/auth_service.py`**: JWT authentication and user management
- **`services/email_service.py`**: Email notifications and password reset
- **`services/business_service.py`**: Business/tenant management

### API Controllers
- **`controllers/v1/auth_controller.py`**: Authentication endpoints
- **`controllers/v1/webhook_controller.py`**: Zoho webhook processing
- **`controllers/v1/business_controller.py`**: Business management API
- **`controllers/v1/utility_controller.py`**: File downloads and testing
- **`controllers/v1/transaction_controller.py`**: Transaction management
- **`controllers/v1/report_controller.py`**: Financial reporting

## Database Models & Schemas

### Core Models

#### User Model (`models/user.py`)
```python
class User(Base):
    id: int (primary key)
    username: str (unique, indexed)
    email: Optional[str] (unique, indexed)
    hashed_password: str (bcrypt)
    role: str (default="admin")
    business_id: Optional[int] (foreign key)
    is_active: bool (default=True)
    created_at/updated_at: timestamps
```

#### Business Model (`models/business.py`)
```python
class Business(Base):
    id: int (primary key)
    business_name: str (indexed)
    email: str (unique, indexed)
    tin_number: str (unique, indexed)
    location: Optional[str]
    phone_number: Optional[str]
    is_active: bool (default=True)
    zoho_organization_id: Optional[str] (unique)
    ebm_service_url: Optional[str]
    webhook_config: Optional[JSON]
    setup_completed_at: Optional[datetime]
    created_at/updated_at: timestamps
```

#### Transaction Model (`models/transaction.py`)
```python
class Transaction(Base):
    id: int (primary key)
    business_id: int (foreign key)
    invoice_number: str (indexed)
    transaction_type: str (SALE, VOID, REFUND)
    total_amount/tax_amount/net_amount: Numeric(15,2)
    payment_method: str (CASH, CARD, MOBILE)
    customer_name/customer_tin: Optional[str]
    receipt_number: Optional[str]
    vsdc_receipt_id/vsdc_signature: Optional[str]
    is_voided: bool (default=False)
    transaction_date: datetime
```

#### Webhook Activity Model (`models/webhook_activity.py`)
```python
class WebhookActivity(Base):
    id: int (primary key)
    webhook_type: Enum (INVOICE, CREDIT_NOTE)
    status: Enum (PENDING, SUCCESS, FAILED, TIMEOUT, RETRY)
    business_tin: Optional[str] (indexed)
    invoice_number: Optional[str] (indexed)
    zoho_payload/vsdc_payload/vsdc_response: Optional[JSON]
    error_code/error_message: Optional[str]
    processing_time_ms: Optional[int]
    pdf_generated: bool (default=False)
    created_at/processed_at: timestamps
```

### Database Features
- **Migrations**: Alembic for version control
- **Relationships**: SQLAlchemy ORM relationships between models
- **Indexes**: Strategic indexing for performance
- **JSON Fields**: Flexible payload storage
- **Audit Trail**: Comprehensive logging of webhook processing

## API Endpoints & Their Purposes

### Authentication Endpoints (`/api/v1/auth/`)
- **POST `/login`**: JWT token authentication
- **POST `/register`**: User registration with business assignment
- **GET `/me`**: Current user information
- **GET `/verify`**: Token validation
- **POST `/forgot-password`**: Password reset OTP generation
- **POST `/verify-otp`**: OTP verification
- **POST `/reset-password`**: Password reset with OTP

### Webhook Endpoints (`/api/v1/webhooks/`)
- **POST `/zoho/invoice`**: Process Zoho invoice webhooks
- **POST `/zoho/credit-note`**: Process Zoho credit note webhooks

### Business Management (`/api/v1/businesses/`)
- **POST `/`**: Create new business
- **GET `/`**: List all businesses (admin only)
- **GET `/{business_id}`**: Get specific business
- **PUT `/{business_id}`**: Update business information
- **DELETE `/{business_id}`**: Soft delete business

### File Management
- **GET `/download-pdf/{filename}`**: Download generated PDFs
- **GET `/api/v1/pdfs/list`**: List all PDF files

### Testing & Utilities
- **POST `/test/transform-payload`**: Test payload transformation
- **POST `/test/generate-pdf`**: Test PDF generation
- **GET `/health`**: System health check

## Authentication & Authorization

### JWT Authentication System
- **Algorithm**: HS256 with configurable secret key
- **Expiration**: 24 hours (1440 minutes)
- **Token Payload**: username, role, business_id (if applicable)
- **Password Hashing**: bcrypt with salt rounds

### Authorization Patterns
- **Role-Based**: admin, user, business_admin, business_user
- **Business-Scoped**: Users can only access their business data
- **Middleware**: `get_current_user` dependency for protected routes
- **Token Validation**: JWT signature verification + user existence check

### Password Reset System
- **OTP Generation**: 6-digit codes with expiration
- **Email Integration**: SMTP with HTML templates
- **Security**: OTP single-use validation
- **Templates**: `templates/password_reset_*.html`

## Integration with Other Components

### Zoho CRM Integration
- **Webhook Reception**: Receives invoice and credit note data
- **Custom Field Mapping**: Extracts business TIN, customer info, tax rates
- **Multi-Business Support**: Routes data based on TIN or organization ID

### VSDC (Rwanda Tax Authority) Integration
- **API Endpoint**: Configurable VSDC API URL
- **Request Format**: Transforms Zoho data to VSDC-compliant format
- **Error Handling**: Comprehensive VSDC error code mapping
- **Response Processing**: Extracts receipt numbers and tax compliance data

### Cloudinary Integration
- **QR Code Hosting**: Generates and hosts QR codes for receipts
- **Configuration**: Cloud name, API key, API secret
- **Fallback**: Text-based QR codes if Cloudinary unavailable

### PDF Generation Pipeline
1. **Data Transformation**: Zoho → Internal model → VSDC format
2. **VSDC API Call**: Submit transaction for tax compliance
3. **QR Code Generation**: Create verification QR code
4. **PDF Creation**: WeasyPrint with HTML templates
5. **File Storage**: Local storage in `output/pdf/` directory

## Configuration & Setup Requirements

### Environment Variables
```bash
# Database
POSTGRES_URL=postgresql://...

# JWT Authentication
JWT_SECRET_KEY=your-secret-key

# Cloudinary (for QR codes)
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Email (for password reset)
MAIL_HOST=smtp.gmail.com
MAIL_USERNAME=...
MAIL_PASSWORD=...
```

### Business Configuration
```python
# Company Settings (per business)
COMPANY_NAME = "Business Name"
COMPANY_ADDRESS = "Business Address"
COMPANY_TIN = "Tax ID Number"
VSDC_SDC_ID = "SDC Device ID"
VSDC_MRC = "MRC Number"
```

### Directory Structure
```
backend/
├── output/pdf/          # Generated PDF invoices
├── output/html/         # Generated HTML versions
├── templates/           # HTML templates for PDF generation
├── assets/images/       # Logos and images
└── migrations/versions/ # Database migration files
```

## Key Features & Capabilities

### Invoice Processing Pipeline
1. **Webhook Reception**: Zoho sends invoice/credit note data
2. **Business Identification**: Extract TIN or organization ID
3. **Data Transformation**: Convert to VSDC format with tax calculations
4. **Tax Compliance**: Submit to VSDC API for receipt number
5. **PDF Generation**: Create professional invoice with QR code
6. **Audit Logging**: Record all processing steps and errors

### Tax Calculation System
- **Dynamic Tax Rates**: Supports multiple VAT categories (A: 0%, B: 18%, C: custom)
- **Tax-Inclusive/Exclusive**: Handles both pricing models
- **Category Mapping**: Automatic tax category assignment
- **Compliance**: Rwanda Revenue Authority requirements

### Multi-Tenant Business Support
- **Business Isolation**: Each business has separate data
- **Custom Configuration**: Business-specific VSDC settings
- **User Management**: Business-scoped user access
- **Webhook Routing**: Automatic business identification

### Error Handling & Monitoring
- **Comprehensive Logging**: All operations logged with context
- **VSDC Error Mapping**: Specific error codes to HTTP status codes
- **Audit Trail**: Complete webhook processing history
- **Retry Logic**: Failed webhook processing can be retried

### File Management
- **PDF Storage**: Local file system with organized structure
- **Download API**: Secure file download endpoints
- **Metadata**: File listing with creation timestamps
- **Cleanup**: Automatic old file management capabilities

This backend system provides a robust, scalable foundation for invoice generation and tax compliance, with clean architecture patterns that support future extensions and multi-tenant operations.