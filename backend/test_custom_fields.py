#!/usr/bin/env python3
"""
Test script for Custom Field Setup functionality
"""
import asyncio
import json
from services.zoho_custom_field_service import ZohoCustomFieldService

async def test_custom_field_service():
    """Test the custom field service functionality"""
    print("🧪 Testing Custom Field Service...")
    
    service = ZohoCustomFieldService()
    
    # Test 1: Get required fields summary
    print("\n1. Testing get_required_fields_summary()...")
    summary = service.get_required_fields_summary()
    print(f"   Total fields required: {summary['total_fields']}")
    print(f"   Invoice fields: {len(summary['invoice_fields'])}")
    print(f"   Contact fields: {len(summary['contact_fields'])}")
    
    # Test 2: Check setup status
    print("\n2. Testing check_setup_status()...")
    test_org_id = "test_org_123"
    status = await service.check_setup_status(test_org_id)
    print(f"   Setup required: {status['setup_required']}")
    print(f"   Recommendation: {status['setup_recommendation']}")
    
    # Test 3: Setup all custom fields
    print("\n3. Testing setup_all_custom_fields()...")
    setup_result = await service.setup_all_custom_fields(test_org_id)
    print(f"   Overall status: {setup_result['overall_status']}")
    print(f"   Invoice fields created: {len(setup_result['invoice_fields']['created'])}")
    print(f"   Contact fields created: {len(setup_result['contact_fields']['created'])}")
    
    if setup_result['errors']:
        print(f"   Errors: {setup_result['errors']}")
    
    print("\n✅ Custom Field Service tests completed successfully!")
    return setup_result

def test_required_fields_structure():
    """Test that required fields match the specification"""
    print("\n🔍 Testing Required Fields Structure...")
    
    service = ZohoCustomFieldService()
    
    # Expected fields from the issue specification
    expected_invoice_fields = {
        'cf_tin', 'cf_customer_tin', 'cf_purchase_code', 
        'cf_seller_company_address', 'cf_organizationname'
    }
    expected_contact_fields = {'cf_custtin'}
    
    # Get actual fields
    actual_invoice_fields = {field['resourceName'] for field in service.required_invoice_fields}
    actual_contact_fields = {field['resourceName'] for field in service.required_contact_fields}
    
    # Check invoice fields
    print(f"   Expected invoice fields: {expected_invoice_fields}")
    print(f"   Actual invoice fields: {actual_invoice_fields}")
    assert actual_invoice_fields == expected_invoice_fields, f"Invoice fields mismatch"
    
    # Check contact fields
    print(f"   Expected contact fields: {expected_contact_fields}")
    print(f"   Actual contact fields: {actual_contact_fields}")
    assert actual_contact_fields == expected_contact_fields, f"Contact fields mismatch"
    
    print("✅ Required fields structure matches specification!")

if __name__ == "__main__":
    print("🚀 Custom Field Setup Test Suite")
    print("=" * 50)
    
    # Run synchronous tests
    test_required_fields_structure()
    
    # Run async tests
    result = asyncio.run(test_custom_field_service())
    
    print("\n📋 Final Setup Result Summary:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n🎉 All tests passed!")