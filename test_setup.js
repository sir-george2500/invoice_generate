/**
 * Simple test to verify EBM custom field setup functionality
 * Run this in browser console when testing the extension
 */

// Mock the ZFAPPS SDK for testing
if (typeof ZFAPPS === 'undefined') {
  window.ZFAPPS = {
    extension: {
      init: () => Promise.resolve({ success: true })
    },
    get: (resource) => {
      if (resource === 'organization') {
        return Promise.resolve({
          organization: {
            organization_id: 'test_org_123',
            name: 'Test Company Ltd'
          }
        });
      }
      if (resource === 'invoice') {
        return Promise.resolve({
          invoice: {
            invoice_id: 'inv_001',
            invoice_number: 'INV-001',
            currency_code: 'USD',
            total: '1000.00'
          }
        });
      }
      if (resource === 'settings.customfields') {
        return Promise.resolve({
          customfields: []
        });
      }
      return Promise.resolve({});
    },
    invoke: (action, data) => {
      console.log('ZFAPPS.invoke called:', action, data);
      if (action === 'CREATE') {
        return Promise.resolve({ success: true, id: 'cf_' + Date.now() });
      }
      if (action === 'RESIZE') {
        return Promise.resolve({ success: true });
      }
      return Promise.resolve({ success: true });
    },
    request: (config) => {
      console.log('ZFAPPS.request called:', config);
      return Promise.resolve({
        status: 200,
        body: { success: true, message: 'Mock API response' }
      });
    }
  };
}

// Mock CONFIG if not defined
if (typeof CONFIG === 'undefined') {
  window.CONFIG = {
    API_BASE_URL: 'https://mock-api.example.com/api/v1',
    SESSION_STORAGE_KEY: 'ebm_session_id'
  };
}

// Test the BusinessSetupManager
async function testBusinessSetup() {
  console.log('🧪 Testing BusinessSetupManager...');
  
  try {
    // Create mock auth manager
    const mockAuth = {
      makeRequest: async (endpoint, options) => {
        console.log('Mock API call:', endpoint, options);
        if (endpoint.includes('setup-custom-fields')) {
          return {
            success: true,
            message: 'Mock backend setup successful',
            fields: [
              { field_name: 'cf_tin', success: true },
              { field_name: 'cf_customer_tin', success: true },
              { field_name: 'cf_purchase_code', success: true },
              { field_name: 'cf_seller_company_address', success: true },
              { field_name: 'cf_organizationname', success: true },
              { field_name: 'cf_custtin', success: true }
            ]
          };
        }
        throw new Error('Mock backend unavailable');
      }
    };
    
    // Create setup manager
    const setupManager = new BusinessSetupManager(mockAuth);
    
    // Test initialization
    console.log('1. Testing initialization...');
    const initResult = await setupManager.initializeBusinessSetup();
    console.log('✅ Initialization result:', initResult);
    
    // Test setup status check
    console.log('2. Testing setup status check...');
    const statusResult = await setupManager.checkSetupStatus();
    console.log('✅ Setup status:', statusResult);
    
    // Test custom field setup
    console.log('3. Testing custom field setup...');
    const setupResult = await setupManager.setupCustomFields();
    console.log('✅ Setup result:', setupResult);
    
    if (setupResult.success) {
      console.log('🎉 All tests passed! Custom field setup is working correctly.');
    } else {
      console.log('⚠️ Setup completed with issues:', setupResult.message);
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test if this script is executed directly
if (typeof require === 'undefined') {
  // Browser environment
  console.log('Ready to test. Run testBusinessSetup() to begin.');
} else {
  // Node.js environment
  testBusinessSetup();
}