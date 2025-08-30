# Invoice Service - Zoho Widget

A Zoho Finance extension widget for managing invoices with user authentication.

## Features

- **Secure Login System**: Username/password authentication with remember me functionality
- **Invoice Integration**: Seamlessly connects with Zoho Books invoice data
- **Responsive Design**: Works well in the Zoho Books sidebar
- **Real-time Updates**: Listens for invoice changes and updates automatically
- **Export Functionality**: Ready for integration with your invoice service API

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open https://127.0.0.1:5001 and authorize the SSL certificate

4. Install the widget in Zoho Books using the plugin manifest

## Login Credentials (Demo)

For testing purposes, the current authentication accepts:
- **Username**: Any valid username or email
- **Password**: Minimum 6 characters

*Replace the `authenticateUser()` method in `app/js/extension.js` with your actual API endpoint.*

## File Structure

- `app/widget.html` - Main widget interface
- `app/css/styles.css` - Styling for login and main screens
- `app/js/extension.js` - Login logic and Zoho Finance SDK integration
- `app/translations/en.json` - Internationalization support
- `plugin-manifest.json` - Zoho widget configuration

## Customization

### Authentication API Integration

Replace the mock authentication in `extension.js`:

```javascript
async authenticateUser(username, password) {
    const response = await fetch('your-api-endpoint/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    return await response.json();
}
```

### Invoice Export Integration

Update the `exportInvoice()` method to connect with your invoice service:

```javascript
async exportInvoice() {
    const response = await fetch('your-api-endpoint/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.invoiceData)
    });
    // Handle response
}
```

## Security Notes

- The current implementation stores user data in localStorage for "remember me" functionality
- In production, implement proper token-based authentication
- Add HTTPS enforcement and proper session management
- Validate all inputs on both client and server side

## Zoho Integration

The widget automatically:
- Initializes the Zoho Finance SDK
- Retrieves current invoice data
- Listens for invoice changes
- Provides refresh functionality
- Resizes appropriately for the sidebar

## Development

The widget runs on port 5001 by default. Make sure this port is available or the system will automatically find an alternative port (5002-5009).