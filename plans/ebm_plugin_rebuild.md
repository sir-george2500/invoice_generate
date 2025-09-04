# ALSM EBM Plugin Rebuild Plan
## Correct Flow: Business Profile + Auto EBM Generation

### Context
The correct flow is:
1. **Business registers** with our backend system
2. **Business installs plugin** in Zoho Books  
3. **Business logs in and enables plugin** (one-time setup)
4. **Invoices created naturally** in Zoho Books
5. **Our webhook auto-generates EBM** via VSDC
6. **EBM shown as button or attached to invoice**

#### Key Objectives:
1. **Link Plugin to Backend**: Connect Zoho plugin to our business database
2. **Auto-Populate Business Fields**: Only fields we have (TIN, Address, Email, Org Name)
3. **User Enters Customer Data**: Customer TIN and Purchase Code (we don't have customers)
4. **Automatic EBM Generation**: Webhook handles everything else
5. **Seamless Integration**: EBM button or attachment in Zoho invoice

#### Relevant Files:
- Backend: `backend/models/business.py`, `backend/controllers/v1/business_controller.py`
- Plugin: `alsm_ebm/app/js/extension.js`, `alsm_ebm/app/widget.html`
- Webhooks: `backend/controllers/v1/webhook_controller.py`

---

## Implementation Plan

### Phase 1: Backend Authentication & Business Profile Lookup

- [x] 1.1: Extend Business model with Zoho integration fields  
  - Add `zoho_organization_id` field to link Business to Zoho organization
  - Add `setup_completed_at` timestamp to track plugin setup completion
  - Add `webhook_config` for storing webhook setup details

- [x] 1.2: Create business profile lookup API for plugin
  - Add `/api/v1/businesses/zoho/lookup/{zoho_org_id}` endpoint  
  - Return business profile data for auto-population
  - Add business authentication/validation

- [x] 1.3: Create business field auto-population service
  - Service to return business fields AND auto-generated purchase code
  - Only Customer TIN needs to be entered by user
  - Add field validation and formatting

### Phase 2: Plugin Authentication & Business Linking

- [ ] 2.1: Replace setup flow with business authentication
  - Remove complex webhook configuration UI
  - Create simple login form for our backend system  
  - Auto-detect Zoho organization ID from current context

- [ ] 2.2: Implement business account linking
  - Login authenticates against our backend user/business system
  - Link logged-in business to current Zoho organization ID
  - Store authentication token and business profile locally

- [ ] 2.3: Create business profile validation
  - Verify business has all required EBM fields (TIN, Address, Email)
  - Show business profile preview and field mapping
  - Allow profile updates if needed

### Phase 3: Smart Auto-Population (Business Fields Only)

- [x] 3.1: Implement business field auto-population
  - Auto-populate Business TIN from our backend business profile
  - Auto-populate Company Address from our backend business profile  
  - Auto-populate Company Email from our backend business profile
  - Auto-populate Organization Name from our backend business profile

- [x] 3.2: Manual field guidance (Customer TIN + Purchase Code)
  - Clear guidance that Customer TIN must be entered manually per customer
  - Clear guidance that Purchase Code is like OTP - get from RRA website per invoice
  - Add field validation and error feedback for required manual fields

- [x] 3.3: Real-time invoice field monitoring
  - Hook into Zoho's invoice load/change events
  - Auto-populate business fields immediately when invoice loads
  - Leave manual fields (Customer TIN, Purchase Code) empty for user to fill

### Phase 4: Smart Webhook Management

- [ ] 4.1: Implement automatic webhook registration
  - Auto-register webhooks during business profile setup
  - Use backend service URL auto-discovery (check common ports/endpoints)
  - Add webhook health monitoring and auto-recovery

- [ ] 4.2: Add webhook configuration validation
  - Test webhook connectivity during setup
  - Validate webhook payload structure
  - Add fallback webhook registration for different deployment scenarios

- [ ] 4.3: Implement webhook status monitoring in plugin
  - Show real-time webhook status in plugin UI
  - Alert users to webhook issues with fix suggestions
  - Add manual webhook reconfiguration option

### Phase 5: Enhanced User Experience

- [ ] 5.1: Create new plugin main interface
  - Replace login system with business profile dashboard
  - Show recent EBM generations and status
  - Add quick business profile edit functionality

- [ ] 5.2: Implement proactive invoice validation
  - Scan invoices for missing customer TINs and warn users
  - Validate invoice data before EBM generation
  - Show EBM preview before invoice finalization

- [ ] 5.3: Add intelligent error handling and recovery
  - Detect and fix common field issues automatically
  - Provide clear error messages with fix suggestions
  - Add retry mechanisms for failed EBM generations

### Phase 6: Advanced Automation Features

- [ ] 6.1: Implement customer TIN management
  - Auto-store and suggest customer TINs from previous invoices
  - Add customer TIN validation and lookup
  - Create customer profile system for recurring TIN assignment

- [ ] 6.2: Create purchase code template system
  - Allow customizable purchase code templates
  - Support dynamic variables: {invoice_number}, {date}, {customer_name}
  - Add purchase code uniqueness validation

- [ ] 6.3: Add bulk invoice processing
  - Support for processing multiple invoices at once
  - Add batch EBM generation for historical invoices
  - Implement progress tracking for bulk operations

### Phase 7: Monitoring and Analytics

- [ ] 7.1: Create EBM generation dashboard
  - Show success/failure rates for EBM generation
  - Display recent EBM generations with status
  - Add export functionality for EBM records

- [ ] 7.2: Implement real-time notifications
  - Show toast notifications for successful EBM generations
  - Alert users to failed EBM attempts with fix suggestions
  - Add email notifications for critical errors

- [ ] 7.3: Add performance monitoring
  - Track plugin setup completion rates
  - Monitor field auto-population success rates
  - Add analytics for user satisfaction and pain points

### Phase 8: Testing and Validation

- [ ] 8.1: Create comprehensive test suite for business profile system
  - Unit tests for business profile creation and validation
  - Integration tests for Zoho organization linking
  - API endpoint testing for plugin integration

- [ ] 8.2: Test auto-field population scenarios
  - Test field population for various invoice types
  - Validate purchase code generation templates
  - Test customer TIN handling and suggestions

- [ ] 8.3: End-to-end testing of complete workflow
  - Test full setup flow from plugin installation to EBM generation
  - Validate webhook registration and health monitoring
  - Test error scenarios and recovery mechanisms

### Phase 9: Documentation and Support

- [ ] 9.1: Create user documentation
  - Step-by-step setup guide with screenshots
  - Troubleshooting guide for common issues
  - Business profile configuration best practices

- [ ] 9.2: Create technical documentation
  - API documentation for business profile endpoints
  - Plugin architecture and extension points
  - Webhook configuration and deployment guide

- [ ] 9.3: Add in-plugin help and guidance
  - Interactive setup wizard with tooltips
  - Contextual help for business profile fields
  - Link to support resources and documentation

---

## Success Criteria

### User Experience Goals:
- ✅ Setup time reduced from 15+ minutes to under 3 minutes
- ✅ Zero manual field entry required after initial setup
- ✅ 95%+ automatic EBM generation success rate
- ✅ Clear error messages and recovery suggestions
- ✅ Business users can set up without technical knowledge

### Technical Goals:
- ✅ All invoices automatically have EBM fields populated
- ✅ Webhook registration and management is fully automated
- ✅ Business profile system integrated with existing backend
- ✅ Real-time field validation and error feedback
- ✅ Robust error handling and recovery mechanisms

### Business Goals:
- ✅ Eliminate user frustration with manual field entry
- ✅ Reduce support requests by 80%+
- ✅ Enable self-service business profile management
- ✅ Support multiple business profiles per user
- ✅ Maintain compliance with EBM requirements

---

## Notes
This plan builds on the existing solid backend architecture (Business model, controllers, authentication) while adding the intelligence and automation needed for seamless user experience. Each step is designed to keep the system functional and can be implemented incrementally.