# Zoho ZFAPPS Storage API Research

## Current Problem
The extension is failing with "Invalid Property (storage) for get action" when trying to use:
```javascript
await ZFAPPS.get('storage', key, value);
await ZFAPPS.set('storage', key, value);
```

## Current Implementation Analysis
From `als_ebm/app/js/extension.js`, the AuthenticationManager class is trying to:
1. Save JWT tokens and user data persistently
2. Load stored data on initialization
3. Clear data on logout

The current implementation uses:
- `ZFAPPS.set('storage', key, value)` - FAILING
- `ZFAPPS.get('storage', key)` - FAILING
- Falls back to localStorage as backup

## Key Entities to Research

**ZFAPPS SDK methods** - Need to understand correct storage API
**Zoho Extensions storage patterns** - How other extensions handle persistence
**Alternative approaches** - If direct storage isn't available
