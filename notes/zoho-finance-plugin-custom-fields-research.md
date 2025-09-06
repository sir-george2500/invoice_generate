# Zoho Finance Plugin SDK - Custom Fields Research

## Current Plugin Structure Analysis

Based on the existing plugin structure in `als_ebm/`, this is a proper Zoho Finance/Books plugin with:

**Plugin Manifest Structure** (`plugin-manifest.json`):
- Service: "FINANCE" 
- Locale support: ["en"]
- Widget configuration in `modules.widgets`
- CSP domains configuration
- Empty `config` and `usedConnections` arrays

**Widget Implementation**:
- Location: `invoice.creation.sidebar`
- Widget HTML: `/app/widget.html`
- JavaScript: `/app/js/extension.js`
- Translations: `/app/translations/en.json`

## Custom Fields Implementation Analysis

The current plugin already implements custom field creation using:

### 1. ZFAPPS API Methods for Custom Fields

**Current Implementation Uses**:
```javascript
// Get existing custom fields
const invoiceFieldsResponse = await ZFAPPS.get('settings/customfields');
const contactFieldsResponse = await ZFAPPS.get('settings/customfields', { entity_type: 'contact' });

// Create new custom fields  
const response = await ZFAPPS.post('settings/customfields', payload);
const response = await ZFAPPS.post('settings/customfields', payload, { entity_type: 'contact' });
```

**Field Configuration Structure**:
```javascript
{
  api_name: 'cf_tin',
  label: 'Business TIN', 
  data_type: 'text',  // Note: uses 'data_type' not 'field_type'
  default_value: '',
  is_required: true,
  is_active: true,
  description: 'Business Tax Identification Number for EBM integration'
}
```

### 2. Entity Types Supported
- `invoice` - Invoice custom fields (default)
- `contact` - Customer/Contact custom fields

### 3. Field Types Available
- `text` - Single line text box
- Other types likely supported but not documented in current code

## Official Zoho Finance Plugin SDK Research Needed

### 1. Plugin Manifest Custom Field Configurations

**Question**: Are there specific plugin manifest configurations for custom fields?

**Current Finding**: The plugin-manifest.json shows an empty `config: []` array. Research needed on:
- Can custom fields be pre-declared in manifest config section?
- Are there manifest-level field definitions that auto-create on plugin installation?

### 2. ZFAPPS API Methods Documentation

**Question**: What's the correct ZFAPPS API method for creating custom fields?

**Current Implementation**: Uses `ZFAPPS.get('settings/customfields')` and `ZFAPPS.post('settings/customfields', payload)`

**Research Needed**:
- Official documentation on `settings/customfields` endpoint
- Complete list of supported field types (`data_type` values)
- Full payload structure options
- Error handling patterns
- Rate limiting considerations

### 3. Plugin Permissions and Scopes

**Question**: Are there plugin-specific permissions or scopes needed?

**Current Finding**: No specific permissions declared in manifest

**Research Needed**:
- Required permissions for custom field creation/management
- OAuth scopes needed for settings modification
- Plugin capabilities declaration

### 4. Installation vs Runtime Creation

**Question**: Should custom fields be created during plugin installation vs runtime?

**Current Implementation**: Creates fields at runtime via UI button triggers

**Research Needed**:
- Plugin lifecycle hooks for installation-time setup
- Best practices for field creation timing
- Rollback/cleanup procedures

## Key Research Areas

### Official Documentation Sources Needed:
1. **Zoho Finance Plugin SDK Documentation**
   - Plugin manifest schema reference
   - ZFAPPS API reference
   - Custom fields creation guide

2. **Zoho Books API Documentation** 
   - Custom fields REST API endpoints
   - Field type specifications
   - Entity type mapping

3. **Plugin Development Best Practices**
   - Installation lifecycle management
   - Error handling patterns
   - User experience guidelines

### Specific API Questions:
1. Complete list of supported `data_type` values for custom fields
2. Validation rules and constraints for field creation
3. Bulk field creation capabilities
4. Field modification/update procedures
5. Field deletion/cleanup on plugin uninstall

### Integration Questions:
1. How to handle field conflicts with existing fields
2. Field naming conventions and API name restrictions  
3. Multi-organization field management
4. Plugin versioning impact on field schemas

## Current Implementation Issues

**Potential Problems Identified**:
1. Uses fallback to direct fetch() when ZFAPPS.request fails
2. No proper error handling for field creation failures
3. No validation of field names against Zoho restrictions
4. Missing cleanup procedures for plugin uninstall

**Next Steps Required**:
1. Find official Zoho Finance Plugin SDK documentation
2. Verify correct ZFAPPS API usage patterns
3. Research plugin manifest configuration options
4. Document proper permission/scope requirements
5. Establish best practices for field lifecycle management