# Architecture Analysis Notes

## Application Overview

This is a **Python FastAPI backend application** for VSDC (EBM - Electronic Business Messages) integration, specifically designed to transform Zoho Books invoice data into VSDC format and generate compliant PDF receipts with QR codes.

### Core Technology Stack
- **Framework**: FastAPI 0.115.11
- **Database**: PostgreSQL with SQLAlchemy 2.0.39 ORM
- **Authentication**: JWT with PyJWT 2.8.0
- **Migration**: Alembic 1.15.1
- **PDF Generation**: WeasyPrint 65.1 
- **QR Codes**: qrcode 8.2 + Cloudinary for hosting
- **Password Hashing**: bcrypt 4.2.1
- **Architecture Pattern**: Clean Architecture with Repository + Service + Controller pattern

## Current System Architecture

### 1. Application Framework (FastAPI)
**Location**: `main.py`
- **Purpose**: Entry point with clean architecture setup
- **Pattern**: Dependency injection with service initialization
- **Controllers**: AuthController, WebhookController, UtilityController
- **Services**: VSSDCInvoiceService, PayloadTransformer, PDFService
- **Features**: Global exception handling, lifespan management, API documentation

### 2. Current Authentication System
**Models**: `models/user.py`
```python
class User(Base):
    id: int (primary key)
    username: str (unique, indexed)
    email: Optional[str] (unique, indexed, nullable) 
    hashed_password: str (required)
    role: str (default="admin")
    is_active: bool (default=True)
    created_at: datetime
    updated_at: Optional[datetime]
```

**Repository**: `repositories/user_repository.py`
- **Pattern**: Repository pattern for data access
- **Methods**: CRUD operations, existence checks, filtering by username/email/id
- **Usage**: Clean separation between data access and business logic

**Authentication Service**: `services/auth_service.py`
- **JWT Configuration**: HS256 algorithm, 24-hour expiration
- **Password Hashing**: bcrypt with salt
- **Token Management**: Create/decode access tokens with username and role
- **User Authentication**: Username/password verification

**Auth Dependencies**: `auth/dependencies.py`
- **get_current_user**: JWT token validation and user retrieval
- **require_admin**: Role-based access control
- **Security**: HTTPBearer token validation

**Schemas**: `auth/schemas.py`
- **UserCreate**: username, email, password, role validation
- **UserLogin**: username, password
- **Token**: access_token, token_type, expires_in, user data
- **UserResponse**: Complete user info without password

### 3. Database Structure
**Connection**: `database/connection.py`
- **Engine**: SQLAlchemy with PostgreSQL
- **Session Management**: SessionLocal with dependency injection
- **Async Support**: databases library for async operations

**Migrations**: `migrations/`
- **Alembic Setup**: Version control for database schema
- **Current Migration**: 612ac7d8f871_create_users_table.py
- **Tables**: Only `users` table exists currently

### 4. API Endpoints and Routing Structure

#### Authentication Endpoints (`controllers/v1/auth_controller.py`)
- **POST /api/v1/auth/login**: User authentication with JWT token
- **POST /api/v1/auth/register**: New user registration
- **GET /api/v1/auth/me**: Current user information
- **GET /api/v1/auth/verify**: Token validation

#### Webhook Endpoints (`controllers/v1/webhook_controller.py`)
- **POST /api/v1/webhooks/zoho/invoice**: Process Zoho invoice data
- **POST /api/v1/webhooks/zoho/credit-note**: Process Zoho credit notes
- **Features**: Dynamic tax calculation, VSDC integration, PDF generation
- **Error Handling**: Comprehensive VSDC error code mapping
- **Response**: Detailed business info, tax summaries, download URLs

#### Utility Endpoints (`controllers/v1/utility_controller.py`)
- **GET /download-pdf/{filename}**: Download generated PDF files
- **GET /api/v1/pdfs/list**: List all generated PDFs
- **GET /health**: System health check
- **GET /**: API information and documentation
- **Test Endpoints**: Payload transformation, PDF generation, QR validation
- **POST /mock/vsdc/api**: Mock VSDC API for testing

### 5. Business Logic Services

#### VSDC Integration Service (`services/vsdc_service.py`)
- **Purpose**: Handle VSDC (EBM) API communication and PDF generation
- **Key Features**:
  - Dynamic business info extraction from Zoho data
  - Advanced PDF generation with QR codes
  - Cloudinary integration for QR code hosting  
  - VSDC API error handling
  - Business-specific formatting
- **Current Limitation**: Uses hardcoded company settings from config

#### Payload Transformer Service (`services/payload_transformer.py`)
- **Purpose**: Transform Zoho Books data to VSDC format
- **Key Features**:
  - Dynamic tax calculation (VAT A: 18%, VAT B: 18%)
  - Tax-inclusive/exclusive price handling
  - Custom field mapping (TIN numbers, business info)
  - Invoice and credit note transformations
- **Current Limitation**: Single business configuration

#### PDF Service (`services/pdf_service.py`)
- **Purpose**: PDF generation and file management
- **Features**: WeasyPrint integration, file serving, metadata extraction

### 6. Configuration (`config/settings.py`)
**Application Settings**:
- **Database**: PostgreSQL connection with Supabase
- **JWT**: Secret key configuration
- **VSDC API**: Endpoint and business credentials
- **Cloudinary**: QR code image hosting
- **Company Information**: Hardcoded business details (KABISA ELECTRIC Ltd)
- **VSDC Configuration**: TIN, BHF_ID, SDC_ID, MRC numbers

## Current Admin Functionality
**Admin Creation**: `create_admin.py`
- Script to create default admin user
- Username: "admin", Password: "password@123"
- Role-based access control ready

**Admin Features**:
- JWT-based authentication
- User management (create, update, verify)
- Access to all system endpoints
- Role-based authorization (admin/user roles)

## Key Limitations for Multi-Tenant Business Requirements

### 1. Single-Tenant Design
- **Current**: Hardcoded company information in settings
- **Needed**: Business-specific configurations per tenant
- **Impact**: Cannot support multiple businesses

### 2. Database Schema
- **Current**: Only `users` table with basic role system
- **Needed**: `businesses` table with business-specific fields
- **Missing Fields**: business_name, location, tin_number, phone_number, vsdc_config

### 3. VSDC Service Architecture
- **Current**: Single VSDC configuration for all operations
- **Needed**: Business-specific VSDC configurations
- **Impact**: All invoices use same company TIN and details

### 4. Authentication Context
- **Current**: User-level authentication without business context
- **Needed**: Business-scoped authentication and authorization
- **Impact**: Cannot isolate business data properly

### 5. Webhook Routing
- **Current**: Single webhook endpoint for all businesses
- **Needed**: Business-specific webhook routing or identification
- **Impact**: Cannot route webhooks to correct business

## Implementation Strategy for Business Management

Based on the current architecture, implementing business management will require:

1. **Database Extension**: Add `businesses` table and foreign key relationship
2. **Model Updates**: Extend User model with business_id relationship
3. **Repository Pattern**: Create BusinessRepository following existing pattern
4. **Service Layer**: Create BusinessService for business management logic
5. **Controller Layer**: Create BusinessController following existing controller pattern
6. **Authentication**: Extend JWT tokens with business context
7. **VSDC Service**: Make VSSDCInvoiceService business-aware
8. **Configuration**: Replace hardcoded settings with business-specific config

The existing clean architecture provides a solid foundation for these extensions.

## Key Architecture Strengths

1. **Clean Architecture**: Well-separated concerns with Repository + Service + Controller pattern
2. **Dependency Injection**: Services properly initialized and injected
3. **Error Handling**: Comprehensive error handling with proper HTTP status codes
4. **Documentation**: OpenAPI/Swagger integration with detailed endpoint documentation
5. **Testing Infrastructure**: Mock endpoints and test utilities available
6. **Security**: JWT authentication with role-based access control
7. **Database Migrations**: Alembic setup for schema version control
8. **Async Support**: FastAPI with async capabilities where needed

## Current Project Files Structure

```
backend/
├── main.py                     # FastAPI app with clean architecture
├── config/settings.py          # Application configuration
├── models/user.py             # User database model
├── repositories/user_repository.py  # User data access layer
├── services/
│   ├── auth_service.py        # Authentication business logic
│   ├── vsdc_service.py        # VSDC integration service
│   ├── payload_transformer.py # Zoho to VSDC transformation
│   └── pdf_service.py         # PDF generation service
├── controllers/v1/
│   ├── auth_controller.py     # Authentication endpoints
│   ├── webhook_controller.py  # Zoho webhook processing
│   └── utility_controller.py  # PDF downloads, health checks
├── auth/
│   ├── dependencies.py        # Auth middleware and dependencies
│   └── schemas.py             # Pydantic schemas for auth
├── database/connection.py     # SQLAlchemy database setup
├── migrations/                # Alembic database migrations
├── templates/                 # HTML templates for PDF generation
├── output/                    # Generated PDF files
└── requirements.txt           # Python dependencies
```

This architecture is well-positioned for extending to support multi-tenant business management while maintaining the existing clean separation of concerns.