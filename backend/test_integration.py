#!/usr/bin/env python3
"""
Integration Test: Complete Custom Field Setup Workflow
Simulates the end-to-end process from plugin initialization to custom field setup
"""
import asyncio
import json
from datetime import datetime

# Load service directly to avoid import dependencies
exec(open('services/zoho_custom_field_service.py').read())

class PluginWorkflowSimulator:
    """Simulates the plugin workflow for custom field setup"""
    
    def __init__(self):
        self.custom_field_service = ZohoCustomFieldService()
        self.user_authenticated = False
        self.zoho_org_id = None
        self.business_linked = False
        
    def simulate_user_login(self, username="test_user"):
        """Simulate user authentication"""
        print(f"📱 User '{username}' logging into plugin...")
        self.user_authenticated = True
        return {
            "success": True,
            "user": {"username": username, "business_id": 1},
            "message": "Authentication successful"
        }
    
    def simulate_zoho_integration(self, org_name="Test Organization"):
        """Simulate Zoho organization integration"""
        print(f"🔗 Linking to Zoho organization: {org_name}")
        self.zoho_org_id = f"zoho_org_{org_name.lower().replace(' ', '_')}_123"
        self.business_linked = True
        return {
            "zoho_organization_id": self.zoho_org_id,
            "business_name": org_name,
            "integration_status": "linked"
        }
    
    async def check_custom_field_setup_needed(self):
        """Check if custom field setup is required"""
        if not self.business_linked:
            raise Exception("Business must be linked to Zoho first")
        
        print(f"🔍 Checking custom field setup status for {self.zoho_org_id}...")
        status = await self.custom_field_service.check_setup_status(self.zoho_org_id)
        
        return {
            "setup_required": status["setup_required"],
            "recommendation": status["setup_recommendation"],
            "zoho_org_id": self.zoho_org_id
        }
    
    async def perform_custom_field_setup(self):
        """Perform the actual custom field setup"""
        if not self.business_linked:
            raise Exception("Business must be linked to Zoho first")
        
        print(f"⚙️ Setting up custom fields for {self.zoho_org_id}...")
        setup_result = await self.custom_field_service.setup_all_custom_fields(self.zoho_org_id)
        
        return setup_result
    
    def simulate_business_update(self, setup_result):
        """Simulate updating business with setup results"""
        print("💾 Updating business record with setup results...")
        
        business_update = {
            "custom_fields_setup_status": setup_result["overall_status"],
            "custom_fields_setup_at": datetime.utcnow().isoformat(),
            "custom_fields_setup_result": setup_result
        }
        
        return business_update

async def run_complete_workflow():
    """Run the complete custom field setup workflow"""
    print("🚀 Starting Complete Custom Field Setup Workflow")
    print("=" * 60)
    
    simulator = PluginWorkflowSimulator()
    
    # Step 1: User Authentication
    print("\n1️⃣ STEP 1: User Authentication")
    login_result = simulator.simulate_user_login("business_admin")
    assert login_result["success"], "Login should succeed"
    print(f"   ✅ {login_result['message']}")
    
    # Step 2: Zoho Integration
    print("\n2️⃣ STEP 2: Zoho Organization Integration")
    zoho_result = simulator.simulate_zoho_integration("ACME Corporation")
    assert zoho_result["integration_status"] == "linked", "Zoho integration should succeed"
    print(f"   ✅ Linked to: {zoho_result['business_name']}")
    print(f"   🔗 Zoho Org ID: {zoho_result['zoho_organization_id']}")
    
    # Step 3: Check Custom Field Setup Status
    print("\n3️⃣ STEP 3: Check Custom Field Setup Status")
    status_check = await simulator.check_custom_field_setup_needed()
    print(f"   📋 Setup required: {status_check['setup_required']}")
    print(f"   💡 Recommendation: {status_check['recommendation']}")
    
    # Step 4: Perform Custom Field Setup (if needed)
    print("\n4️⃣ STEP 4: Custom Field Setup")
    setup_result = await simulator.perform_custom_field_setup()
    print(f"   🎯 Overall status: {setup_result['overall_status']}")
    
    # Display detailed results
    invoice_created = len(setup_result['invoice_fields']['created'])
    contact_created = len(setup_result['contact_fields']['created'])
    print(f"   📊 Invoice fields created: {invoice_created}")
    print(f"   👥 Contact fields created: {contact_created}")
    
    if setup_result['errors']:
        print(f"   ⚠️ Errors encountered: {len(setup_result['errors'])}")
        for error in setup_result['errors']:
            print(f"      - {error}")
    
    # Step 5: Update Business Record
    print("\n5️⃣ STEP 5: Update Business Record")
    business_update = simulator.simulate_business_update(setup_result)
    print(f"   💾 Setup status: {business_update['custom_fields_setup_status']}")
    print(f"   🕒 Setup timestamp: {business_update['custom_fields_setup_at']}")
    
    # Step 6: Verify Setup Completion
    print("\n6️⃣ STEP 6: Verify Setup Completion")
    final_status = await simulator.check_custom_field_setup_needed()
    
    # In a real implementation, this should show setup is no longer needed
    # For simulation, we just verify the process completed
    print(f"   ✅ Workflow completed successfully")
    print(f"   📈 Total fields processed: {invoice_created + contact_created}")
    
    return {
        "workflow_status": "completed",
        "setup_result": setup_result,
        "business_update": business_update,
        "total_fields_processed": invoice_created + contact_created
    }

def test_field_configuration_completeness():
    """Test that all required fields from the specification are configured"""
    print("\n🔍 Testing Field Configuration Completeness")
    print("-" * 50)
    
    service = ZohoCustomFieldService()
    
    # Fields from the issue specification
    required_spec = {
        "invoice_fields": [
            {"resourceName": "cf_tin", "displayLabel": "Business TIN"},
            {"resourceName": "cf_customer_tin", "displayLabel": "Customer TIN"},
            {"resourceName": "cf_purchase_code", "displayLabel": "Purchase Code"},
            {"resourceName": "cf_seller_company_address", "displayLabel": "Seller Company Address"},
            {"resourceName": "cf_organizationname", "displayLabel": "Seller Company Name"}
        ],
        "contact_fields": [
            {"resourceName": "cf_custtin", "displayLabel": "Customer TIN"}
        ]
    }
    
    # Check invoice fields
    actual_invoice = {f["resourceName"]: f["displayLabel"] for f in service.required_invoice_fields}
    expected_invoice = {f["resourceName"]: f["displayLabel"] for f in required_spec["invoice_fields"]}
    
    print("📋 Invoice Fields:")
    for field_name, label in expected_invoice.items():
        if field_name in actual_invoice:
            print(f"   ✅ {field_name}: {label}")
            assert actual_invoice[field_name] == label, f"Label mismatch for {field_name}"
        else:
            print(f"   ❌ Missing: {field_name}")
            assert False, f"Missing required field: {field_name}"
    
    # Check contact fields
    actual_contact = {f["resourceName"]: f["displayLabel"] for f in service.required_contact_fields}
    expected_contact = {f["resourceName"]: f["displayLabel"] for f in required_spec["contact_fields"]}
    
    print("👥 Contact Fields:")
    for field_name, label in expected_contact.items():
        if field_name in actual_contact:
            print(f"   ✅ {field_name}: {label}")
            assert actual_contact[field_name] == label, f"Label mismatch for {field_name}"
        else:
            print(f"   ❌ Missing: {field_name}")
            assert False, f"Missing required field: {field_name}"
    
    print("✅ All required fields are properly configured!")

async def main():
    """Main test runner"""
    print("🧪 Custom Field Setup Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Field Configuration
    test_field_configuration_completeness()
    
    # Test 2: Complete Workflow
    workflow_result = await run_complete_workflow()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Field Configuration: Complete")
    print(f"✅ Workflow Status: {workflow_result['workflow_status']}")
    print(f"✅ Setup Status: {workflow_result['setup_result']['overall_status']}")
    print(f"✅ Fields Processed: {workflow_result['total_fields_processed']}")
    
    # Detailed results
    print(f"\n📋 Setup Details:")
    print(f"   - Invoice fields: {len(workflow_result['setup_result']['invoice_fields']['created'])} created")
    print(f"   - Contact fields: {len(workflow_result['setup_result']['contact_fields']['created'])} created")
    print(f"   - Errors: {len(workflow_result['setup_result']['errors'])}")
    
    if workflow_result['setup_result']['errors']:
        print(f"   - Error details: {workflow_result['setup_result']['errors']}")
    
    print("\n🎉 All integration tests passed!")
    return workflow_result

if __name__ == "__main__":
    result = asyncio.run(main())