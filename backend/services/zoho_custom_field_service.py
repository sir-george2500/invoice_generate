"""
Zoho Custom Field Service
Handles creation and management of custom fields in Zoho Books
"""
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ZohoCustomFieldService:
    """Service to handle Zoho custom field creation and management"""
    
    def __init__(self):
        self.required_invoice_fields = [
            {
                "resourceName": "cf_tin",
                "module": "invoices",
                "displayLabel": "Business TIN",
                "type": "Text",
                "maxLength": "50",
                "isRequired": False
            },
            {
                "resourceName": "cf_customer_tin",
                "module": "invoices", 
                "displayLabel": "Customer TIN",
                "type": "Text",
                "maxLength": "50",
                "isRequired": False
            },
            {
                "resourceName": "cf_purchase_code",
                "module": "invoices",
                "displayLabel": "Purchase Code", 
                "type": "Text",
                "maxLength": "100",
                "isRequired": False
            },
            {
                "resourceName": "cf_seller_company_address",
                "module": "invoices",
                "displayLabel": "Seller Company Address",
                "type": "Text", 
                "maxLength": "255",
                "isRequired": False
            },
            {
                "resourceName": "cf_organizationname",
                "module": "invoices",
                "displayLabel": "Seller Company Name",
                "type": "Text",
                "maxLength": "100", 
                "isRequired": False
            }
        ]
        
        self.required_contact_fields = [
            {
                "resourceName": "cf_custtin",
                "module": "contacts",
                "displayLabel": "Customer TIN",
                "type": "Text",
                "maxLength": "50",
                "isRequired": False
            }
        ]
    
    async def setup_all_custom_fields(self, zoho_org_id: str) -> Dict[str, Any]:
        """
        Set up all required custom fields for a Zoho organization
        This is the main entry point for custom field setup
        """
        logger.info(f"Starting custom field setup for Zoho org: {zoho_org_id}")
        
        results = {
            "zoho_organization_id": zoho_org_id,
            "setup_timestamp": datetime.utcnow().isoformat(),
            "invoice_fields": {
                "created": [],
                "existing": [],
                "failed": []
            },
            "contact_fields": {
                "created": [],
                "existing": [],
                "failed": []
            },
            "overall_status": "success",
            "errors": []
        }
        
        try:
            # Setup invoice fields
            logger.info("Setting up invoice custom fields...")
            invoice_results = await self._setup_module_fields(
                zoho_org_id, "invoices", self.required_invoice_fields
            )
            results["invoice_fields"] = invoice_results
            
            # Setup contact fields
            logger.info("Setting up contact custom fields...")
            contact_results = await self._setup_module_fields(
                zoho_org_id, "contacts", self.required_contact_fields
            )
            results["contact_fields"] = contact_results
            
            # Determine overall status
            total_failed = len(invoice_results["failed"]) + len(contact_results["failed"])
            if total_failed > 0:
                results["overall_status"] = "partial_success" if total_failed < len(self.required_invoice_fields) + len(self.required_contact_fields) else "failed"
                results["errors"].append(f"{total_failed} custom fields failed to create")
            
            logger.info(f"Custom field setup completed. Status: {results['overall_status']}")
            return results
            
        except Exception as e:
            logger.error(f"Custom field setup failed: {str(e)}")
            results["overall_status"] = "failed"
            results["errors"].append(f"Setup failed: {str(e)}")
            return results
    
    async def _setup_module_fields(self, zoho_org_id: str, module: str, fields: List[Dict]) -> Dict[str, List]:
        """Setup custom fields for a specific module (invoices or contacts)"""
        results = {
            "created": [],
            "existing": [],
            "failed": []
        }
        
        for field_config in fields:
            try:
                # For now, simulate the creation process
                # In a real implementation, this would call Zoho's Custom Field API
                field_name = field_config["resourceName"]
                
                # Simulate checking if field exists
                field_exists = await self._check_field_exists(zoho_org_id, module, field_name)
                
                if field_exists:
                    logger.info(f"Custom field {field_name} already exists in {module}")
                    results["existing"].append({
                        "field_name": field_name,
                        "display_label": field_config["displayLabel"],
                        "status": "already_exists"
                    })
                else:
                    # Simulate field creation
                    logger.info(f"Creating custom field {field_name} in {module}")
                    created_field = await self._create_custom_field(zoho_org_id, module, field_config)
                    
                    if created_field:
                        results["created"].append({
                            "field_name": field_name,
                            "display_label": field_config["displayLabel"],
                            "field_id": created_field.get("field_id"),
                            "status": "created"
                        })
                    else:
                        results["failed"].append({
                            "field_name": field_name,
                            "display_label": field_config["displayLabel"],
                            "error": "Creation failed"
                        })
                        
            except Exception as e:
                logger.error(f"Failed to setup field {field_config['resourceName']}: {str(e)}")
                results["failed"].append({
                    "field_name": field_config["resourceName"],
                    "display_label": field_config["displayLabel"],
                    "error": str(e)
                })
        
        return results
    
    async def _check_field_exists(self, zoho_org_id: str, module: str, field_name: str) -> bool:
        """
        Check if a custom field already exists
        TODO: Implement actual Zoho API call to check field existence
        """
        # For now, simulate that fields don't exist (so they get created)
        # In real implementation, this would call:
        # GET https://books.zoho.com/api/v3/settings/preferences/customfields/{module}
        logger.debug(f"Checking if field {field_name} exists in {module} for org {zoho_org_id}")
        return False
    
    async def _create_custom_field(self, zoho_org_id: str, module: str, field_config: Dict) -> Optional[Dict]:
        """
        Create a custom field in Zoho
        TODO: Implement actual Zoho API call to create custom field
        """
        try:
            # For now, simulate successful creation
            # In real implementation, this would call:
            # POST https://books.zoho.com/api/v3/settings/preferences/customfields/{module}
            
            logger.info(f"Creating field {field_config['resourceName']} in {module}")
            
            # Simulate API call payload
            api_payload = {
                "field_name": field_config["resourceName"],
                "label": field_config["displayLabel"],
                "data_type": field_config["type"].lower(),
                "max_length": int(field_config["maxLength"]),
                "is_required": field_config["isRequired"],
                "module": module
            }
            
            logger.debug(f"API payload: {json.dumps(api_payload, indent=2)}")
            
            # Simulate successful response
            return {
                "field_id": f"field_{field_config['resourceName']}_{zoho_org_id}",
                "field_name": field_config["resourceName"],
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create custom field {field_config['resourceName']}: {str(e)}")
            return None
    
    def get_required_fields_summary(self) -> Dict[str, Any]:
        """Get a summary of all required custom fields"""
        return {
            "invoice_fields": [
                {
                    "name": field["resourceName"],
                    "label": field["displayLabel"],
                    "type": field["type"],
                    "module": field["module"]
                }
                for field in self.required_invoice_fields
            ],
            "contact_fields": [
                {
                    "name": field["resourceName"],
                    "label": field["displayLabel"],
                    "type": field["type"],
                    "module": field["module"]
                }
                for field in self.required_contact_fields
            ],
            "total_fields": len(self.required_invoice_fields) + len(self.required_contact_fields)
        }
    
    async def check_setup_status(self, zoho_org_id: str) -> Dict[str, Any]:
        """
        Check the setup status of custom fields for a Zoho organization
        """
        logger.info(f"Checking custom field setup status for org: {zoho_org_id}")
        
        status = {
            "zoho_organization_id": zoho_org_id,
            "setup_required": True,
            "invoice_fields_status": {},
            "contact_fields_status": {},
            "setup_recommendation": "full_setup_needed"
        }
        
        try:
            # Check invoice fields
            for field in self.required_invoice_fields:
                exists = await self._check_field_exists(zoho_org_id, "invoices", field["resourceName"])
                status["invoice_fields_status"][field["resourceName"]] = {
                    "exists": exists,
                    "label": field["displayLabel"]
                }
            
            # Check contact fields
            for field in self.required_contact_fields:
                exists = await self._check_field_exists(zoho_org_id, "contacts", field["resourceName"])
                status["contact_fields_status"][field["resourceName"]] = {
                    "exists": exists,
                    "label": field["displayLabel"]
                }
            
            # Determine overall status
            all_invoice_exist = all(
                field["exists"] for field in status["invoice_fields_status"].values()
            )
            all_contact_exist = all(
                field["exists"] for field in status["contact_fields_status"].values()
            )
            
            if all_invoice_exist and all_contact_exist:
                status["setup_required"] = False
                status["setup_recommendation"] = "no_setup_needed"
            elif all_invoice_exist or all_contact_exist:
                status["setup_recommendation"] = "partial_setup_needed"
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to check setup status: {str(e)}")
            status["error"] = str(e)
            return status