from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class InvoiceItem:
    code: str
    description: str
    quantity: str
    tax: str
    unit_price: str
    total_price: str

@dataclass
class Company:
    name: str
    address: str
    tel: str
    email: str
    tin: str
    cashier: str
    logo_path: str = "somelogo.png"

@dataclass
class Client:
    name: str
    tin: str

@dataclass
class Invoice:
    company: Company
    client: Client
    invoice_number: str
    invoice_date: str
    invoice_time: str
    sdc_id: str
    receipt_number: str
    mrc: str
    items: List[InvoiceItem]
    total_rwf: str
    total_aex: str
    total_b: str
    total_tax_b: str
    total_tax: str
    rwanda_seal_path: str = "seaRR.png"
    qr_code_path: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for template rendering"""
        return {
            'company_name': self.company.name,
            'company_address': self.company.address,
            'company_tel': self.company.tel,
            'company_email': self.company.email,
            'company_tin': self.company.tin,
            'cashier': self.company.cashier,
            'company_logo_path': self.company.logo_path,
            'client_name': self.client.name,
            'client_tin': self.client.tin,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'invoice_time': self.invoice_time,
            'sdc_id': self.sdc_id,
            'receipt_number': self.receipt_number,
            'mrc': self.mrc,
            'items': [
                {
                    'code': item.code,
                    'description': item.description,
                    'quantity': item.quantity,
                    'tax': item.tax,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                } for item in self.items
            ],
            'total_rwf': self.total_rwf,
            'total_aex': self.total_aex,
            'total_b': self.total_b,
            'total_tax_b': self.total_tax_b,
            'total_tax': self.total_tax,
            'rwanda_seal_path': self.rwanda_seal_path,
            'qr_code_path': self.qr_code_path
        }
