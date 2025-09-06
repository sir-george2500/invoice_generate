# EBM Custom Field Setup - Step by Step Guide

## Overview
This implementation provides a one-click setup process for creating the required custom fields in Zoho Books for EBM integration.

## Custom Fields Created

### For Invoices Module:
1. **cf_tin** - Business TIN (50 chars max)
2. **cf_customer_tin** - Customer TIN (50 chars max)  
3. **cf_purchase_code** - Purchase Code (100 chars max)
4. **cf_seller_company_address** - Seller Company Address (255 chars max)
5. **cf_organizationname** - Seller Company Name (100 chars max)

### For Contacts Module:
6. **cf_custtin** - Customer TIN (50 chars max)

## How It Works

### 1. User Login
- User opens the EBM plugin in Zoho Books sidebar
- Logs in with their EBM credentials
- Plugin checks setup status automatically

### 2. Setup Process
- If custom fields are missing, user sees "Setup Custom Fields" button
- Clicking the button triggers the setup process
- Plugin tries two approaches:
  1. **Backend API**: Sends request to backend which handles Zoho API calls
  2. **SDK Fallback**: Direct calls via Zoho Extension SDK

### 3. Field Creation
- Each field is created with proper validation
- Progress is shown to the user
- Errors are handled gracefully
- Existing fields are detected and skipped

### 4. Completion
- Setup status changes to "Setup complete"
- Button is hidden
- User can proceed with normal EBM operations

## Technical Implementation

### Frontend (JavaScript)
- `BusinessSetupManager.setupCustomFields()` - Main setup orchestrator
- `createFieldsViaBackend()` - Calls backend API
- `createFieldsViaSdk()` - Direct SDK calls as fallback
- Progress UI updates in real-time

### Backend (Python FastAPI)
- `POST /api/v1/businesses/setup-custom-fields` - Setup endpoint
- Handles Zoho OAuth and API communication
- Returns structured results for each field

### Error Handling
- Network connectivity issues
- Zoho API authentication problems
- Duplicate field detection
- Partial success scenarios
- User-friendly error messages

## Testing
The implementation includes a test UI that demonstrates:
- Initial state with setup required
- Loading state during setup
- Success state after completion
- Proper button state management

## Future Enhancements
- Zoho OAuth token management
- Field validation and cleanup
- Bulk field operations
- Setup status persistence
- Webhook registration integration