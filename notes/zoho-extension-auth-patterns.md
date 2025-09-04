# Zoho Extension Authentication Patterns Research

## Current Plugin Analysis
The ALSM EBM plugin currently has these configurations:
- Service: FINANCE 
- Permissions: ZohoBooks.* (invoices, contacts, settings, customfields, webhooks)
- Widget location: invoice.creation.sidebar
- Whitelisted domains: ngrok domains for development

## Key Entities to Research
1. **ZFAPPS.request()** method for external API calls
2. **Manifest permissions** for external authentication
3. **Connection configurations** in manifest
4. **Official authentication patterns** from Zoho
5. **CSP handling** in Zoho extensions

Let me research each of these systematically.
