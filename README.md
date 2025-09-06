# Invoice Generation System with EBM Integration

A comprehensive system for generating invoices with Electronic Billing Machine (EBM) integration for Rwanda's tax compliance requirements. The system consists of a backend API, admin dashboard, and Zoho Books plugin.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Zoho Books    │◄──►│   EBM Plugin     │◄──►│  Backend API    │
│   (Invoice)     │    │  (als_ebm)       │    │ (FastAPI)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │     VSDC API     │    │ Admin Dashboard │
                       │   (Rwanda EBM)   │    │   (Next.js)     │
                       └──────────────────┘    └─────────────────┘
```

## 📂 Repository Structure

```
invoice_generate/
├── admin-dashboard/          # Next.js admin interface
├── backend/                  # FastAPI backend service
├── als_ebm/                 # Zoho Books plugin
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** database
- **Zoho Books** account
- **ZET CLI** (Zoho Extension Toolkit)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup database
python create_admin.py

# Run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Admin Dashboard Setup

```bash
cd admin-dashboard
npm install
npm run dev
```

Access at: `http://localhost:3000`

### 3. Zoho Books Plugin Setup

```bash
cd als_ebm
npm install

# Run plugin in development mode
zet run --zoho-service "Zoho Books" --project-name alsm_ebm
```

## 🔧 Plugin Development

### Running the EBM Plugin

The Zoho Books plugin is built using the Zoho Extension Toolkit (ZET):

```bash
# Navigate to plugin directory
cd als_ebm

# Install dependencies
npm install

# Run in development mode
zet run --zoho-service "Zoho Books" --project-name alsm_ebm
```

### Plugin Features

- **🔐 Authentication**: Secure login to EBM backend
- **⚙️ Auto Setup**: Automatic custom field creation via `resources.json`
- **📋 Invoice Integration**: Real-time invoice processing with VSDC API
- **📊 Status Monitoring**: Live EBM integration status
- **🔍 Debug Tools**: Development and troubleshooting utilities

### Custom Fields Created

The plugin automatically creates these custom fields in Zoho Books:

| Field Name | API Name | Module | Type | Required |
|------------|----------|---------|------|----------|
| Business TIN | `cf_tin` | Invoice | Text | No |
| Customer TIN | `cf_customer_tin` | Invoice | Text | No |
| Purchase Code | `cf_purchase_code` | Invoice | Text | No |
| Seller Company Address | `cf_seller_company_address` | Invoice | Text | No |
| Seller Company Name | `cf_organizationname` | Invoice | Text | No |
| Customer TIN | `cf_custtin` | Contact | Text | No |

## 🔧 Configuration

### Backend Configuration

Create `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
VSDC_API_URL=https://vsdc-api-endpoint
COMPANY_NAME=Your Company Name
```

### Plugin Configuration

Update `plugin-manifest.json` for your environment:

```json
{
  "whiteListedDomains": [
    "your-backend-domain.com"
  ],
  "cspDomains": {
    "connect-src": [
      "https://your-backend-domain.com"
    ]
  }
}
```

### Admin Dashboard Configuration

Create `.env.local` in `admin-dashboard/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your-nextauth-secret
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/verify` - Verify session

### Webhooks
- `POST /api/v1/webhooks/zoho/invoice` - Process Zoho invoice
- `POST /api/v1/webhooks/zoho/credit-note` - Process credit note

### Business Management
- `GET /api/v1/businesses` - List businesses
- `POST /api/v1/businesses` - Create business
- `PUT /api/v1/businesses/{id}` - Update business

### Reports
- `GET /api/v1/reports/x/{tin}` - Generate X report
- `GET /api/v1/reports/z/{tin}` - Generate Z report

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Plugin Testing
```bash
cd als_ebm
npm test
```

### Admin Dashboard Tests
```bash
cd admin-dashboard
npm test
```

## 📦 Deployment

### Backend Deployment
```bash
cd backend
docker build -t ebm-backend .
docker run -p 8000:8000 ebm-backend
```

### Admin Dashboard Deployment
```bash
cd admin-dashboard
npm run build
npm start
```

### Plugin Publishing
```bash
cd als_ebm
zet pack
zet publish
```

## 🔍 Troubleshooting

### Common Plugin Issues

1. **Login Stuck**: Check API connectivity and CORS settings
2. **Custom Fields Missing**: Verify `resources.json` and reinstall plugin
3. **API Errors**: Check backend URL in `CONFIG.API_BASE_URL`

### Debug Commands

```bash
# Check plugin logs
zet logs

# Validate plugin manifest
zet validate

# Clear plugin cache
zet clear-cache
```

## 📚 Documentation

- [Zoho Books API](https://www.zoho.com/books/api/v3/)
- [Zoho Extension Toolkit](https://help.zoho.com/portal/en/community/topic/zet-zoho-extension-toolkit)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in this repository
- Contact the development team
- Check the troubleshooting section above

## 🔄 Version History

- **v1.0.0** - Initial release with basic EBM integration
- **v1.1.0** - Added admin dashboard and enhanced error handling
- **v1.2.0** - Improved plugin setup with automatic custom field creation

---

**Built with ❤️ for Rwanda's digital tax compliance**