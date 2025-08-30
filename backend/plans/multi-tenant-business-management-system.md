# Multi-Tenant Business Management System Implementation Plan

## Context

The goal is to implement a comprehensive multi-tenant business management system for a VSDC integration platform. The system will allow:

1. **Admin Management**: Admins can add businesses as users
2. **Business Registration**: Each business gets a dedicated account with their own VSDC configuration
3. **Multi-tenant Architecture**: Businesses are isolated from each other
4. **Zoho Integration**: Each business can install a Zoho Books plugin/widget
5. **Custom VSDC Configuration**: Each business has their own TIN, company details, and VSDC settings

The current system has:
- Basic authentication with admin/user roles (models/user.py, auth/schemas.py)
- VSDC integration service (services/vsdc_service.py) 
- PDF generation with QR codes
- Webhook endpoints for Zoho integration (controllers/v1/webhook_controller.py)
- Repository pattern with clean architecture (repositories/user_repository.py)

Key entities and files:
- **User model** (models/user.py): Current user entity with id, username, email, password, role, status
- **UserRepository** (repositories/user_repository.py): Data access layer for users
- **AuthService** (services/auth_service.py): Authentication logic with JWT tokens
- **VSSDCInvoiceService** (services/vsdc_service.py): VSDC integration with hardcoded company settings
- **WebhookController** (controllers/v1/webhook_controller.py): Handles Zoho webhook processing
- **Settings** (config/settings.py): Application configuration with hardcoded company information
- **Database Connection** (database/connection.py): SQLAlchemy setup

## Implementation

### Phase 1: Database Schema & Models

- [x] Create Business model (models/business.py)
  - [x] Fields: id, business_name, email, location, tin_number, phone_number, status, vsdc_config, created_at, updated_at
  - [x] VSDC config JSON field for storing business-specific VSDC settings
  - [x] Relationships and constraints
- [x] Update User model (models/user.py)
  - [x] Add business_id foreign key field
  - [x] Add relationship to Business model  
  - [x] Update role enum to include 'business_admin', 'business_user' roles
  - [x] Add nullable business_id constraint (admins won't have business)
- [x] Create Alembic migration for new schema
  - [x] Run migration to add new tables and columns
  - [ ] Test migration rollback capabilities
- [x] Update database connection and Base imports
  - [x] Import new models in models/__init__.py
  - [x] Verify database schema is correctly created
- [ ] Iterate until you get no compilation/type errors

### Phase 2: Business Management Schema & Repository

- [x] Create BusinessRepository (repositories/business_repository.py)
  - [x] CRUD operations: create, get_by_id, get_by_tin, get_by_email, update, delete
  - [x] List businesses with pagination
  - [x] Search and filter methods
  - [x] Business existence checks
- [x] Create Business Pydantic schemas (schemas/business_schemas.py)
  - [x] BusinessCreate: business_name, email, location, tin_number, phone_number, admin_username, admin_password
  - [x] BusinessUpdate: Optional fields for updating business info
  - [x] BusinessResponse: Response model with all business details
  - [x] BusinessVSDCConfig: Schema for VSDC configuration
  - [x] BusinessSummary: Minimal business info for listings
- [x] Update UserRepository (repositories/user_repository.py)
  - [x] Add methods to get users by business_id
  - [x] Add business filtering to existing queries
  - [x] Update create/update methods to handle business_id
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 3: Multi-tenant Authentication & Authorization

- [x] Update auth schemas (auth/schemas.py)
  - [x] Add business_id to TokenData
  - [x] Add business info to UserResponse
  - [x] Update role validation patterns
- [x] Update AuthService (services/auth_service.py)
  - [x] Include business_id in JWT tokens
  - [x] Add business context to token validation
  - [x] Update token creation/verification logic
- [ ] Update auth dependencies (auth/dependencies.py) 
  - [ ] Add get_current_business dependency
  - [ ] Add require_business_admin dependency
  - [ ] Add require_super_admin dependency (global admin)
  - [ ] Update role-based access control
- [x] Create BusinessService (services/business_service.py)
  - [x] Business creation and setup logic
  - [x] VSDC configuration management
  - [x] Business admin user creation
  - [x] Business status management (active/inactive)
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 4: Business Management API Endpoints

- [x] Create BusinessController (controllers/v1/business_controller.py)
  - [x] POST /api/v1/businesses - Create new business (super admin only)
  - [x] GET /api/v1/businesses - List businesses (super admin only)
  - [x] GET /api/v1/businesses/{business_id} - Get business details
  - [x] PUT /api/v1/businesses/{business_id} - Update business
  - [x] PUT /api/v1/businesses/{business_id}/deactivate - Delete/deactivate business
  - [x] PUT /api/v1/businesses/me/vsdc-config - Update VSDC config
  - [x] GET /api/v1/businesses/me - Get current business info (for business users)
- [ ] Update AuthController (controllers/v1/auth_controller.py)
  - [ ] Add business context to login response
  - [ ] Add business user registration endpoint
  - [ ] Update user profile endpoints with business info
- [ ] Add business validation to existing endpoints
  - [ ] Ensure users can only access their business data
  - [ ] Add business_id filters to all relevant queries
- [x] Register new routes in main.py
- [ ] Write tests and iterate until tests pass
- [x] Iterate until you get no compilation/type errors

### Phase 5: Multi-tenant VSDC Service

- [ ] Update VSSDCInvoiceService (services/vsdc_service.py)
  - [ ] Add business parameter to constructor
  - [ ] Replace hardcoded company settings with business-specific config
  - [ ] Update extract_business_info_from_zoho method to use business data
  - [ ] Add business context to all VSDC operations
  - [ ] Update PDF generation to use business branding/info
- [ ] Create VSSDCServiceFactory (services/vsdc_service_factory.py)
  - [ ] Factory pattern to create business-specific VSDC service instances
  - [ ] Business configuration validation
  - [ ] Cache management for service instances
- [ ] Update WebhookController (controllers/v1/webhook_controller.py)
  - [ ] Add business identification from webhook data
  - [ ] Route webhooks to correct business VSDC service
  - [ ] Add business_id extraction from webhook headers or payload
  - [ ] Update error handling with business context
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 6: Zoho Integration & Webhook Routing

- [ ] Create webhook routing mechanism
  - [ ] Add business identification strategy for incoming webhooks
  - [ ] Create business-specific webhook URLs or use header-based routing
  - [ ] Add webhook authentication/validation per business
- [ ] Update webhook payload handling
  - [ ] Extract business context from webhook data
  - [ ] Validate webhook belongs to correct business
  - [ ] Route to business-specific service instances
- [ ] Create Zoho plugin configuration endpoint
  - [ ] Generate business-specific webhook URLs
  - [ ] Provide Zoho plugin configuration details
  - [ ] Business-specific API credentials if needed
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 7: Data Isolation & Security

- [ ] Implement row-level security
  - [ ] Add business_id filters to all database queries
  - [ ] Ensure users can only access their business data
  - [ ] Add business context validation to all endpoints
- [ ] Update all existing repositories
  - [ ] Add business_id filters to queries
  - [ ] Update CRUD operations with business context
  - [ ] Ensure data isolation between businesses
- [ ] Add audit logging
  - [ ] Log business-specific actions
  - [ ] Track cross-business access attempts
  - [ ] Add business context to all log entries
- [ ] Security hardening
  - [ ] Validate business ownership on all operations
  - [ ] Prevent business ID manipulation in requests
  - [ ] Add rate limiting per business
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 8: Business Onboarding & Configuration UI Endpoints

- [ ] Create business configuration endpoints
  - [ ] GET /api/v1/businesses/me/config - Get business configuration
  - [ ] PUT /api/v1/businesses/me/config - Update business configuration
  - [ ] GET /api/v1/businesses/me/zoho-config - Get Zoho integration config
  - [ ] POST /api/v1/businesses/me/test-vsdc - Test VSDC connection
- [ ] Create business dashboard endpoints
  - [ ] GET /api/v1/businesses/me/stats - Business statistics
  - [ ] GET /api/v1/businesses/me/recent-invoices - Recent invoice activity
  - [ ] GET /api/v1/businesses/me/vsdc-status - VSDC integration status
- [ ] Add business setup wizard endpoints
  - [ ] POST /api/v1/businesses/me/setup/step1 - Basic business info
  - [ ] POST /api/v1/businesses/me/setup/step2 - VSDC configuration
  - [ ] POST /api/v1/businesses/me/setup/step3 - Zoho integration
  - [ ] GET /api/v1/businesses/me/setup/status - Setup completion status
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 9: Migration & Backwards Compatibility

- [ ] Create data migration scripts
  - [ ] Migrate existing users to business structure
  - [ ] Create default business for existing data
  - [ ] Update existing invoices with business context
- [ ] Add backwards compatibility layer
  - [ ] Support old API endpoints during transition
  - [ ] Gradual migration of existing integrations
  - [ ] Deprecation notices and timeline
- [ ] Update configuration management
  - [ ] Migrate hardcoded settings to business-specific config
  - [ ] Ensure existing functionality continues to work
  - [ ] Add configuration validation and migration tools
- [ ] Write tests and iterate until tests pass
- [ ] Iterate until you get no compilation/type errors

### Phase 10: Testing & Documentation

- [ ] Create comprehensive test suite
  - [ ] Unit tests for all new models and services
  - [ ] Integration tests for multi-tenant scenarios
  - [ ] API endpoint tests with business context
  - [ ] Business isolation and security tests
- [ ] Add load testing for multi-tenant scenarios
  - [ ] Test with multiple businesses active
  - [ ] Concurrent webhook processing
  - [ ] Database performance with business filters
- [ ] Update API documentation
  - [ ] Document new business management endpoints
  - [ ] Update authentication documentation
  - [ ] Add multi-tenant usage examples
  - [ ] Create business onboarding guide
- [ ] Create deployment and monitoring setup
  - [ ] Business-specific monitoring dashboards
  - [ ] Multi-tenant health checks
  - [ ] Resource usage tracking per business
- [ ] Write tests and iterate until tests pass
- [ ] Final integration testing and bug fixes