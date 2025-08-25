from dataclasses import dataclass
from typing import List

@dataclass
class Company:
    name: str
    address: str
    tel: str
    email: str
    tin: str
    cashier: str

@dataclass
class Client:
    name: str
    tin: str

@dataclass
class InvoiceItem:
    code: str
    description: str
    quantity: str
    tax: str
    unit_price: str
    total_price: str

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
    total_tax_a: str
    total_tax_b: str
    total_tax: str
    vsdc_receipt_no: str = ""
    vsdc_total_receipt_no: str = ""
    vsdc_internal_data: str = ""
    vsdc_receipt_signature: str = ""
    vsdc_receipt_date: str = ""
    original_invoice_number: str = ""
    invoice_number_numeric: str = ""
    
    def to_dict(self):
        return {
            'company_name': self.company.name,
            'company_address': self.company.address,
            'company_tel': self.company.tel,
            'company_email': self.company.email,
            'company_tin': self.company.tin,
            'cashier': self.company.cashier,
            'client_name': self.client.name,
            'client_tin': self.client.tin,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'invoice_time': self.invoice_time,
            'sdc_id': self.sdc_id,
            'receipt_number': self.receipt_number,
            'mrc': self.mrc,
            'items': self.items,
            'total_rwf': self.total_rwf,
            'total_aex': self.total_aex,
            'total_b': self.total_b,
            'total_tax_a': self.total_tax_a,
            'total_tax_b': self.total_tax_b,
            'total_tax': self.total_tax,
            'vsdc_receipt_no': self.vsdc_receipt_no,
            'vsdc_total_receipt_no': self.vsdc_total_receipt_no,
            'vsdc_internal_data': self.vsdc_internal_data,
            'vsdc_receipt_signature': self.vsdc_receipt_signature,
            'vsdc_receipt_date': self.vsdc_receipt_date,
            'original_invoice_number': self.original_invoice_number,
            'invoice_number_numeric': self.invoice_number_numeric
        }
