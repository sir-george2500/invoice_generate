# ALSM EBM Integration Plugin for Zoho Books

This plugin by ALSM Consulting automatically integrates Zoho Books with VSDC (Virtual Sales Device Controller) for EBM (Electronic Billing Machine) invoice generation in Rwanda.

## 📝 Required EBM Fields (Auto-Created)

### Customer Level:
- `cf_customer_tin` - Customer TIN (Required)

### Invoice Level:  
- `cf_tin` - Business TIN (Required)
- `cf_purchase_code` - Purchase Code (Required) 
- `cf_organizationname` - Organization Name
- `cf_seller_company_address` - Seller Company Address (Required)
- `cf_seller_company_email` - Seller Company Email (Required)

## Features

### 🔧 Automatic Setup
- **Custom Field Creation**: Automatically creates all required EBM custom fields
- **Webhook Configuration**: Sets up webhooks to trigger EBM invoice generation
- **Field Validation**: Validates that all required fields are present before generating EBM invoices

### ⚡ Automatic Processing
- EBM invoices are generated automatically when you create/update invoices in Zoho Books
- Credit notes are also supported with automatic EBM processing
- PDF receipts with QR codes are generated and available for download

## Installation & Setup

### 1. Install Plugin
1. Upload the plugin to your Zoho Books account
2. Install it in your Zoho Books organization

### 2. Configure Backend URL
1. Update the webhook URL in the plugin to point to your backend service
2. Default: `https://ed704c2185d9.ngrok-free.app` (change this to your actual backend)

### 3. Run Setup Process
1. Open any invoice in Zoho Books
2. Look for the "ALSM EBM Integration" widget in the sidebar
3. Click "Setup ALSM EBM Integration" 
4. The plugin will:
   - Create all required custom fields
   - Configure webhooks
   - Test the connection# VSDC EBM Integration Plugin for Zoho Books

This plugin automatically integrates Zoho Books with VSDC (Virtual Sales Device Controller) for EBM (Electronic Billing Machine) invoice generation in Rwanda.

## Features

### 🔧 Automatic Setup
- **Custom Field Creation**: Automatically creates all required VSDC custom fields
- **Webhook Configuration**: Sets up webhooks to trigger EBM invoice generation
- **Field Validation**: Validates that all required fields are present before generating EBM invoices

### 📋 Custom Fields Added

#### Customer Fields
- **Customer TIN** (Required): Customer's Tax Identification Number

#### Invoice Fields
- **Business TIN** (Required): Your business Tax Identification Number  
- **Purchase Code** (Required): Purchase order or reference code
- **Organization Name**: Your company name for VSDC receipts
- **Seller Company Address** (Required): Your business address  
- **Seller Company Email** (Required): Your business email

### ⚡ Automatic Processing
- EBM invoices are generated automatically when you create/update invoices in Zoho Books
- Credit notes are also supported with automatic VSDC processing
- PDF receipts with QR codes are generated and available for download

## Installation & Setup

### 1. Install Plugin
1. Upload the plugin to your Zoho Books account
2. Install it in your Zoho Books organization

### 2. Configure Backend URL
1. Update the webhook URL in the plugin to point to your backend service
2. Default: `https://ed704c2185d9.ngrok-free.app` (change this to your actual backend)

### 3. Run Setup Process
1. Open any invoice in Zoho Books
2. Look for the "VSDC EBM Integration" widget in the sidebar
3. Click "Setup VSDC Integration" 
4. The plugin will:
   - Create all required custom fields
   - Configure webhooks
   - Test the connection

### 4. Fill Required Fields
After setup, you need to fill the custom fields in your invoices:

#### For Each Customer:
1. Go to **Sales → Customers**
2. Edit customer details  
3. Fill the **Customer TIN** field

#### For Each Invoice:
1. When creating/editing invoices, fill these custom fields:
   - **Business TIN** (your company's TIN)
   - **Purchase Code** (required for VSDC)
   - **Seller Company Address** (your business address)
   - **Seller Company Email** (your business email)  
   - **Organization Name** (optional, your business name)

## Usage

### Creating EBM Invoices
1. Create an invoice in Zoho Books as usual
2. Ensure all required VSDC fields are filled
3. Save the invoice
4. The EBM invoice will be generated automatically via webhook
5. PDF with QR code will be available for download

### Field Validation
- The plugin shows which fields are configured and which are missing
- Generate EBM Invoice button is disabled until all required fields are filled
- Clear guidance on where to find and fill the custom fields

### Troubleshooting
- Use the "📋 How to Fill VSDC Fields" button for field guidance
- Test connection feature to verify backend connectivity
- Reconfigure webhooks if backend URL changes

## Technical Details

### Webhook Endpoints
- **Invoice Webhook**: `{backend_url}/api/v1/webhooks/zoho/invoice`
- **Credit Note Webhook**: `{backend_url}/api/v1/webhooks/zoho/credit-note`

### Events Triggered
- `invoice.created` - When new invoice is created
- `invoice.updated` - When invoice is modified  
- `creditnote.created` - When credit note is created
- `creditnote.updated` - When credit note is modified

### Required Permissions
- Read/Write access to invoices and customers
- Custom field creation and management
- Webhook creation and management

## Support

For technical issues:
1. Check that all required fields are filled
2. Verify backend service is running
3. Test connection using the plugin's test feature
4. Check webhook configuration in Zoho Books settings

---

**Note**: This plugin requires a running backend service that handles the VSDC integration. The backend processes the webhook data and generates EBM-compliant invoices with QR codes.