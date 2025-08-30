# ALSM VSDC - Daily X and Z Reports Documentation

## Overview

The ALSM VSDC system implements mandatory daily X and Z reports as required by Rwanda Revenue Authority (RRA) for Electronic Billing Machines (EBM). These reports are essential for tax compliance and business reconciliation.

## Report Types

### X Report (Daily Sales Report)
- **Purpose**: Shows current daily sales totals without clearing the system's memory
- **Frequency**: Can be generated multiple times during the day
- **Use Case**: Check current sales figures for reconciliation without ending the fiscal day
- **Data**: Preserves all transaction data after generation

### Z Report (End of Day Report)
- **Purpose**: Shows final daily sales totals and officially ends the fiscal day
- **Frequency**: Can only be generated once per day
- **Use Case**: Official end-of-day closing with tax compliance
- **Data**: Marks the day as finalized (conceptually clears daily counters)

## API Endpoints

### Authentication
All report endpoints require authentication. Include your JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Generate X Report
```http
POST /api/v1/reports/x-report
Content-Type: application/json

{
  "business_tin": "123456789"
}
```

**Response:**
```json
{
  "report_type": "X",
  "report_number": 15,
  "report_date": "2024-01-15T14:30:00Z",
  "business_tin": "123456789",
  "business_name": "Sample Business Ltd",
  "period_start": "2024-01-15T00:00:00Z",
  "period_end": "2024-01-15T14:30:00Z",
  "total_sales_amount": 45000.00,
  "total_tax_amount": 8100.00,
  "total_net_amount": 36900.00,
  "total_transactions": 12,
  "voided_transactions": 1,
  "refunded_transactions": 0,
  "payment_methods": {
    "cash_amount": 20000.00,
    "card_amount": 15000.00,
    "mobile_amount": 10000.00,
    "other_amount": 0.00
  },
  "is_finalized": false,
  "generated_by": "admin_user"
}
```

### Generate Z Report
```http
POST /api/v1/reports/z-report
Content-Type: application/json

{
  "business_tin": "123456789"
}
```

**Response:** (Same format as X report but with `"is_finalized": true`)

### Get Report History
```http
GET /api/v1/reports/history/123456789?start_date=2024-01-01&end_date=2024-01-15&report_type=Z
```

### Get Specific Report
```http
GET /api/v1/reports/{report_id}
```

### Validate Business Access
```http
GET /api/v1/reports/validate-access/123456789
```

## Business Logic & Rules

### X Report Rules
1. Can be generated multiple times per day
2. Cannot be generated if the day is already finalized with a Z report
3. Shows real-time daily totals
4. Does not affect transaction data or daily counters

### Z Report Rules
1. Can only be generated once per business per day
2. Cannot be generated if no transactions exist for the day
3. Marks the day as finalized (`is_finalized: true`)
4. Sequential report numbering per business
5. Required for RRA tax compliance

### Business Access Control
- **Admin users**: Can generate reports for any business
- **Business users**: Can only generate reports for their assigned business (based on `business_id`)
- Business must be active (`is_active: true`)
- Business must exist and be valid

## Report Content Details

### Financial Summary
- **Total Sales Amount**: Gross sales including tax
- **Total Tax Amount**: VAT and other taxes collected
- **Total Net Amount**: Sales amount excluding tax
- **Payment Methods**: Breakdown by payment type (Cash, Card, Mobile, Other)

### Transaction Summary
- **Total Transactions**: Count of all valid transactions
- **Voided Transactions**: Count of cancelled transactions
- **Refunded Transactions**: Count of refunded transactions

### Period Information
- **Period Start**: Beginning of the reporting period (start of day)
- **Period End**: End of the reporting period (current time for X, end of day for Z)

## Testing the System

### 1. Create Test Transactions
```http
POST /api/v1/transactions/
Content-Type: application/json

{
  "business_tin": "123456789",
  "invoice_number": "INV-001",
  "transaction_type": "SALE",
  "total_amount": 5900.00,
  "tax_amount": 900.00,
  "net_amount": 5000.00,
  "payment_method": "CASH",
  "currency": "RWF",
  "customer_name": "John Doe",
  "receipt_number": "RCP-001"
}
```

### 2. Generate X Report
Generate multiple X reports to see real-time totals.

### 3. Generate Z Report
Generate the final Z report to close the day.

### 4. Try to Generate Another Z Report
This should fail with an error message.

## Error Handling

### Common Error Responses

**Business Not Found (404):**
```json
{
  "detail": "Business with TIN 123456789 not found"
}
```

**Access Denied (403):**
```json
{
  "detail": "You don't have access to this business"
}
```

**Day Already Finalized (400):**
```json
{
  "detail": "Day has been finalized with Z report. Cannot generate X report."
}
```

**Z Report Already Exists (400):**
```json
{
  "detail": "Z report already generated for today. Only one Z report per day is allowed."
}
```

**No Transactions for Z Report (400):**
```json
{
  "detail": "No transactions found for today. Cannot generate Z report."
}
```

## Database Schema

### Transactions Table
- Stores all business transactions
- Links to business via `business_id`
- Includes void status and timestamps
- Payment method and tax information

### Daily Reports Table
- Stores generated X and Z reports
- Sequential report numbering per business
- Financial summaries and totals
- Period information and metadata

## Compliance Notes

### RRA Requirements
- X and Z reports must be available for tax audits
- Z reports are mandatory for daily closing
- Sequential numbering must be maintained
- Reports must include all required tax information
- Business identification via TIN number

### Data Retention
- All reports are stored permanently
- Historical reports accessible via API
- Transaction data maintained for audit trail
- Report generation timestamps recorded

## Sample Usage Workflow

1. **Morning**: Business starts operations
2. **During Day**: Create transactions via API or POS system
3. **Periodic Checks**: Generate X reports for reconciliation
4. **End of Day**: Generate final Z report
5. **Next Day**: New cycle begins (can generate reports again)

## Integration Notes

For integration with existing POS systems or business applications:
1. Authenticate users and get JWT token
2. Identify business by TIN number
3. Create transactions throughout the day
4. Generate reports as needed
5. Handle error responses appropriately
6. Store report data for local records

## Support

For technical support or questions about the VSDC reporting system:
- Check API documentation at `/docs`
- Review error messages for specific guidance
- Ensure proper authentication and business access
- Verify TIN numbers and business status