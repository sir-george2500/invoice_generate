# Invoice Generation System

A comprehensive FastAPI-based invoice generation system that integrates Zoho CRM with Rwanda's VSDC (Virtual Sales Device Controller) system for tax-compliant invoice processing.

## 🚀 Features

- **Zoho to VSDC Integration**: Seamlessly transforms Zoho invoice data to VSDC-compliant format
- **Dynamic Tax Calculation**: Supports multiple tax rates (0%, 18%, and custom rates) with automatic categorization
- **PDF Generation**: Creates professional invoices and credit notes with QR codes
- **QR Code Integration**: Cloudinary-powered QR code generation with RRA verification URLs
- **Credit Note Support**: Full support for refund processing and credit note generation  
- **Error Handling**: Comprehensive error handling with detailed logging
- **Real-time Processing**: Webhook-based real-time invoice processing
- **Multiple Output Formats**: Generates both PDF and HTML versions

## 🏗️ Architecture

### Core Components

```
invoice_generate/
├── main.py                     # FastAPI application with webhook endpoints
├── config/
│   └── settings.py            # Application configuration and settings
├── services/                  # Business logic services
│   ├── vsdc_service.py       # VSDC integration and invoice processing
│   ├── payload_transformer.py # Zoho to VSDC payload transformation
│   └── pdf_service.py        # PDF file management
├── src/                       # Core invoice processing
│   ├── invoice_generator.py   # PDF and HTML generation
│   ├── invoice_qrcode.py     # QR code generation with Cloudinary
│   └── models.py             # Data models and structures  
├── utils/
│   └── tax_calculator.py     # Tax calculation utilities
├── templates/                 # HTML templates for PDF generation
│   ├── invoice_template.html
│   └── credit_note_template.html
├── exceptions/
│   └── custom_exceptions.py  # Custom exception classes
└── output/                    # Generated files
    ├── pdf/                  # Generated PDF invoices
    └── html/                 # Generated HTML versions
```

## 📋 Requirements

### Python Dependencies
```
fastapi==0.115.12
uvicorn==0.34.3
httpx==0.28.1
jinja2==3.1.6
weasyprint==65.1
cloudinary==1.44.1
qrcode==8.2
pillow==11.2.1
reportlab==4.4.2
```

### External Services
- **Cloudinary Account**: For QR code image generation and hosting
- **VSDC API Access**: Rwanda Revenue Authority VSDC system integration
- **Zoho CRM**: Source system for invoice data

## 🔧 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd invoice_generate
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Create .env file with:
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

5. **Create output directories**
```bash
mkdir -p output/pdf output/html
```

## ⚙️ Configuration

### Application Settings (`config/settings.py`)

```python
# VSDC API Configuration
VSDC_API_URL = "http://localhost:8080/vsdc/trnsSales/saveSales"

# Company Information (fallback defaults)
COMPANY_NAME = "KABISA ELECTRIC Ltd"
COMPANY_ADDRESS = "KIGALI CITY NYARUGENGE NYARUGENGE Nyarugenge"
COMPANY_TIN = "120732779"

# VSDC Device Configuration
VSDC_SDC_ID = "SDC010053151"
VSDC_MRC = "WIS00058003"

# QR Code Configuration
QR_CODE_TYPE = "text"  # 'url' for RRA verification, 'text' for content
```

## 🚀 Usage

### Starting the Application

```bash
# Development mode
python main.py

# Production mode with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Main Webhook Endpoints
- `POST /webhooks/zoho/invoice` - Process Zoho invoice webhooks
- `POST /webhooks/zoho/credit-note` - Process Zoho credit note webhooks

#### File Management
- `GET /download-pdf/{filename}` - Download generated PDF files
- `GET /list-pdfs` - List all generated PDF files

#### Testing Endpoints
- `POST /test/transform-payload` - Test payload transformation
- `POST /test/generate-pdf` - Test PDF generation
- `POST /test/validate-qr` - Test QR code generation
- `GET /health` - Health check

### Zoho Webhook Configuration

Configure your Zoho CRM to send webhooks to:
```
https://your-domain.com/webhooks/zoho/invoice
https://your-domain.com/webhooks/zoho/credit-note
```

### Required Zoho Custom Fields

The system expects these custom fields in your Zoho invoices:

```json
{
  "custom_field_hash": {
    "cf_organizationname": "Your Company Name",
    "cf_seller_company_address": "Your Company Address", 
    "cf_seller_company_email": "company@email.com",
    "cf_tin": "Your Business TIN",
    "cf_customer_tin": "Customer TIN",
    "cf_purchase_code": "Purchase Order Code"
  }
}
```

## 🧮 Tax Calculation System

The system supports Rwanda's tax categories:

- **Category A (0%)**: VAT-exempt items
- **Category B (18%)**: Standard VAT rate
- **Category C**: Custom tax rates  
- **Category D**: Special tax categories

### Tax Calculation Logic

```python
# VAT from inclusive price
vat = price * vat_rate / (100 + vat_rate)

# VAT from exclusive price  
vat = price * vat_rate / 100

# Tax category mapping
def get_tax_category(vat_rate):
    if vat_rate == 0: return 'A'
    elif vat_rate == 18: return 'B' 
    else: return 'C'
```

## 📄 Invoice Processing Flow

1. **Webhook Received**: Zoho sends invoice data via webhook
2. **Payload Transformation**: Convert Zoho format to VSDC format
3. **Tax Calculation**: Calculate taxes by category (A, B, C, D)
4. **VSDC Submission**: Send to Rwanda's VSDC API
5. **Response Processing**: Handle VSDC response and extract receipt data
6. **PDF Generation**: Generate invoice PDF with QR code
7. **File Storage**: Store generated files in output directories

## 🔍 QR Code Integration

### Cloudinary Setup
```python
cloudinary_config = {
    'cloud_name': 'your_cloud_name',
    'api_key': 'your_api_key', 
    'api_secret': 'your_api_secret'
}
```

### QR Code Types
- **Text QR**: Contains invoice data as text
- **URL QR**: Links to RRA verification system (production only)

### QR Code Content
```
Invoice: {invoice_number}
Date: {date} {time}  
SDC: {sdc_id}
Receipt: {receipt_number}
Internal: {internal_data}
Signature: {receipt_signature}
Company: {company_name}
Total: {total_amount} RWF
```

## 🛠️ Error Handling

### VSDC API Error Codes
- `000`: Success
- `881`: Purchase code mandatory
- `884`: Invalid customer TIN  
- `901`: Invalid device
- `910`: Request parameter error
- `994`: Duplicate data

### Custom Exceptions
```python
class TaxCalculationError(Exception):
    """Raised when tax calculation fails"""

class PDFGenerationError(Exception):
    """Raised when PDF generation fails"""
```

## 📊 Generated Invoice Features

### PDF Invoice Contents
- Company header with logos
- Invoice and customer details
- Itemized list with tax categories
- Tax breakdown by category
- VSDC compliance information
- QR code for verification
- Receipt numbers and signatures

### Data Fields
- **Company Info**: Name, address, TIN, contact details
- **Customer Info**: Name, TIN, phone number
- **Invoice Details**: Number, date, time, items
- **VSDC Data**: Receipt number, SDC ID, MRC, signatures
- **Tax Summary**: Breakdown by categories A, B, C, D

## 🧪 Testing

### Unit Tests
```bash
# Test payload transformation
curl -X POST http://localhost:8000/test/transform-payload

# Test PDF generation  
curl -X POST http://localhost:8000/test/generate-pdf

# Test QR code validation
curl -X POST http://localhost:8000/test/validate-qr
```

### Mock VSDC API
The system includes a mock VSDC endpoint for testing:
```bash
curl -X POST http://localhost:8000/mock/vsdc/api \
  -H "Content-Type: application/json" \
  -d '{"invcNo": 123, "custNm": "Test Customer"}'
```

## 🔐 Security Considerations

- Validate all input data from Zoho webhooks
- Sanitize customer and business information
- Secure storage of TIN numbers and sensitive data
- Rate limiting on webhook endpoints
- HTTPS required for production deployment

## 📈 Performance Optimization

- Async processing with FastAPI
- Efficient PDF generation with WeasyPrint
- Cloudinary CDN for QR code delivery
- Proper error handling prevents system crashes
- Logging for debugging and monitoring

## 🔧 Deployment

### Production Deployment
```bash
# Using Uvicorn with workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Docker
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```env
CLOUDINARY_CLOUD_NAME=production_cloud_name
CLOUDINARY_API_KEY=production_api_key  
CLOUDINARY_API_SECRET=production_api_secret
VSDC_API_URL=https://production-vsdc-api.rra.gov.rw/api
```

## 📝 Logging

The system provides comprehensive logging:
- Request/response logging for VSDC API calls
- Tax calculation debugging
- PDF generation status
- QR code generation logs  
- Error tracking and troubleshooting

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`) 
5. Create Pull Request

## 📞 Support

For technical support or questions:
- Check the logs in the application output
- Review VSDC API documentation  
- Verify Zoho webhook configuration
- Ensure Cloudinary credentials are correct

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This system is designed for Rwanda's tax compliance requirements. Ensure you have proper authorization to integrate with VSDC systems and comply with Rwanda Revenue Authority regulations.