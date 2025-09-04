# Authentication, Business Management & Reporting System Analysis

## System Overview
This is a multi-tenant invoice/EBM system where businesses are created by super admins, and each business gets its own admin users who can manage their business operations and generate EBM reports.

## Key Entities

### User Model (`models/user.py`)
- **Location**: `backend/models/user.py`
- **Key Fields**:
  - `id`: Primary key
  - `username`: Unique across system
  - `email`: Optional, unique if provided
  - `hashed_password`: Bcrypt hashed password
  - `role`: One of "admin", "user", "business_admin", "business_user"
  - `business_id`: Foreign key to Business (nullable for super admins)
  - `is_active`: Boolean flag for account status
- **Relationships**: 
  - `business`: Many-to-one relationship with Business model
  - `password_reset_otps`: One-to-many for password reset functionality

### Business Model (`models/business.py`)
- **Location**: `backend/models/business.py`
- **Key Fields**:
  - `id`: Primary key
  - `business_name`: Business display name
  - `email`: Business contact email (unique)
  - `location`: Optional business address
  - `tin_number`: Tax Identification Number (unique, required for EBM)
  - `phone_number`: Optional contact phone
  - `is_active`: Boolean flag for business status
- **Relationships**: 
  - `users`: One-to-many relationship with User model
  - `transactions`: One-to-many with Transaction model (via backref)
  - `daily_reports`: One-to-many with DailyReport model (via backref)

### Transaction Model (`models/transaction.py`)
- **Location**: `backend/models/transaction.py`
- **Key Fields**:
  - `business_id`: Links to Business
  - `invoice_number`: Invoice identifier
  - `transaction_type`: "SALE", "VOID", "REFUND"
  - `total_amount`, `tax_amount`, `net_amount`: Financial amounts
  - `payment_method`: "CASH", "CARD", "MOBILE", "OTHER"
  - `currency`: Default "RWF"
  - `customer_name`, `customer_tin`: Optional customer info
  - `is_voided`: Boolean flag for voided transactions
  - `vsdc_receipt_id`: Integration with VSDC system

### DailyReport Model (`models/transaction.py`)
- **Location**: `backend/models/transaction.py` 
- **Purpose**: Stores X and Z report data for EBM compliance
- **Key Fields**:
  - `business_id`: Links to Business
  - `report_type`: "X" (current totals) or "Z" (end-of-day finalized)
  - `report_number`: Sequential number per business per report type
  - Financial totals: `total_sales_amount`, `total_tax_amount`, etc.
  - Transaction counts: `total_transactions`, `voided_transactions`
  - Payment breakdown: `cash_amount`, `card_amount`, `mobile_amount`, `other_amount`
  - `is_finalized`: True for Z reports, False for X reports
  - `generated_by`: User who generated the report

## Authentication System

### AuthService (`services/auth_service.py`)
- **Purpose**: Handles JWT token creation/validation and password hashing
- **Key Methods**:
  - `hash_password()`: Bcrypt password hashing
  - `verify_password()`: Password verification
  - `authenticate_user()`: Username/password authentication
  - `create_access_token()`: JWT token generation with user data
  - `decode_access_token()`: JWT token validation and decoding
- **Token Structure**: Contains `sub` (username), `role`, and `business_id` claims
- **Token Expiry**: 24 hours (1440 minutes)

### Authentication Flow
1. User submits credentials via `/api/v1/auth/login`
2. `AuthController.login()` calls `AuthService.authenticate_user()`
3. If valid, creates JWT token with user info including business_id
4. Returns token with user data and expiration info
5. Subsequent requests use `get_current_user` dependency to validate tokens

### Dependencies (`middleware/dependencies.py`)
- **`get_current_user`**: Core dependency that validates JWT and returns User object
- **Usage Pattern**: All protected endpoints use `current_user: User = Depends(get_current_user)`
- **Error Handling**: Returns 401 for invalid/expired tokens or inactive users

## Business Management System

### Multi-Tenant Architecture
- **Super Admin Role**: Can create businesses and manage all system operations
- **Business Admin Role**: Can manage their own business and generate reports
- **Business User Role**: Can perform business operations within their assigned business
- **Business Context**: Users are tied to businesses via `business_id` foreign key

### Business Creation Process (`services/business_service.py`)
1. Super admin creates business via `POST /api/v1/businesses`
2. System validates TIN uniqueness and email uniqueness
3. Auto-generates unique username from business name + TIN suffix
4. Creates secure random password for business admin
5. Creates Business record and associated business_admin User
6. Returns business details with generated admin credentials

### Access Control Patterns
- **Super Admin Access**: `require_super_admin` dependency checks `role == "admin"`
- **Business Context Required**: `require_business_context` checks `business_id` exists
- **Resource Access Control**: 
  - Super admins can access any business data
  - Business users can only access their own business data
  - Validation: `current_user.business_id == business_id`

### Business Operations
- **Create**: Super admin only, auto-generates admin user
- **Read**: Super admin can view all, business users view their own
- **Update**: Super admin can update any, business admin can update their own
- **Deactivate**: Super admin only, also deactivates all business users

## Report Generation System

### Report Types
- **X Report**: Current day totals without clearing memory, can be run multiple times
- **Z Report**: End-of-day finalized report, can only be run once per day, marks day as complete

### Report Generation Flow (`services/report_service.py`)
1. User calls report endpoint with business TIN number
2. System validates business exists and is active
3. For Z reports, checks no Z report exists for the day
4. Queries transaction repository for daily summary
5. Generates sequential report number per business
6. Creates DailyReport record with all financial totals
7. Returns formatted report response

### Report Data Structure
- **Financial Totals**: Total sales, tax, net amounts
- **Transaction Counts**: Total transactions, voided, refunded counts  
- **Payment Breakdown**: Cash, card, mobile, other payment totals
- **Metadata**: Report number, type, generation timestamp, user who generated

### Report Business Rules
- **X Reports**: Can be generated multiple times per day, `is_finalized = False`
- **Z Reports**: Only one per day per business, `is_finalized = True`
- **Sequential Numbering**: Each business maintains separate sequential numbers for X and Z reports
- **Data Validation**: Z reports require at least one transaction for the day

## Relationships and Patterns

### Multi-Tenant Data Isolation
- Users belong to businesses via `business_id` foreign key
- All business data (transactions, reports) is tied to `business_id`
- Access control enforced at controller level using user's business context
- Super admins have system-wide access, business users have business-scoped access

### Authentication & Authorization Flow
```
Request → JWT Token → get_current_user → User Object → Business Context → Resource Access
```

### Report Generation Pattern
```
TIN Number → Business Validation → Transaction Summary → Report Creation → Response Formatting
```

### Error Handling Conventions
- HTTP 401 for authentication failures
- HTTP 403 for authorization/permission denied
- HTTP 400 for business rule violations (e.g., duplicate Z report)
- HTTP 404 for resource not found
- HTTP 500 for system errors with generic messages

## Database Access Patterns

### Repository Pattern
- Each model has dedicated repository class
- Repositories handle all database queries and business logic
- Controllers delegate data operations to services, services use repositories
- Pattern: Controller → Service → Repository → Database

### Common Repository Methods
- `get_by_id()`, `get_by_username()`, `get_by_tin()`: Single record retrieval
- `create()`, `update()`, `delete()`: CRUD operations
- `exists_by_*()`: Existence checks for uniqueness validation
- `get_*_summary()`: Aggregated data queries for reports

## Security Considerations

### Password Security
- Bcrypt hashing with default cost factor
- Secure password generation for auto-created business admins
- Password reset via OTP system with email verification

### Token Security
- JWT tokens with 24-hour expiration
- Tokens include minimal claims (username, role, business_id)
- Bearer token authentication scheme
- Token validation on every request

### Business Data Isolation
- Business context enforced at user level
- Resource access validation in controllers
- TIN-based business identification for reports
- Active status checks for businesses and users