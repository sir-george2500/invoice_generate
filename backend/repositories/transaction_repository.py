from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from models.transaction import Transaction, DailyReport
from models.business import Business

class TransactionRepository:
    """Repository for managing transaction data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_by_invoice_number(self, invoice_number: str) -> Optional[Transaction]:
        """Get transaction by invoice number"""
        return self.db.query(Transaction).filter(Transaction.invoice_number == invoice_number).first()
    
    def get_by_business_tin(self, tin_number: str, limit: int = 100, offset: int = 0) -> List[Transaction]:
        """Get transactions by business TIN"""
        return (self.db.query(Transaction)
                .join(Business, Transaction.business_id == Business.id)
                .filter(Business.tin_number == tin_number)
                .order_by(desc(Transaction.created_at))
                .offset(offset)
                .limit(limit)
                .all())
    
    def get_daily_transactions(self, tin_number: str, target_date: date) -> List[Transaction]:
        """Get all transactions for a specific business and date"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        return (self.db.query(Transaction)
                .join(Business, Transaction.business_id == Business.id)
                .filter(
                    and_(
                        Business.tin_number == tin_number,
                        Transaction.transaction_date >= start_of_day,
                        Transaction.transaction_date <= end_of_day,
                        Transaction.is_voided == False
                    )
                )
                .order_by(Transaction.transaction_date)
                .all())
    
    def get_period_transactions(self, tin_number: str, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions within a date range for a business"""
        return (self.db.query(Transaction)
                .join(Business, Transaction.business_id == Business.id)
                .filter(
                    and_(
                        Business.tin_number == tin_number,
                        Transaction.transaction_date >= start_date,
                        Transaction.transaction_date <= end_date
                    )
                )
                .order_by(Transaction.transaction_date)
                .all())
    
    def get_daily_summary(self, tin_number: str, target_date: date) -> Dict[str, Any]:
        """Get daily transaction summary for a business"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Base query
        base_query = (self.db.query(Transaction)
                     .join(Business, Transaction.business_id == Business.id)
                     .filter(
                         and_(
                             Business.tin_number == tin_number,
                             Transaction.transaction_date >= start_of_day,
                             Transaction.transaction_date <= end_of_day
                         )
                     ))
        
        # Get totals for non-voided transactions
        sales_summary = (base_query
                        .filter(Transaction.is_voided == False)
                        .with_entities(
                            func.count(Transaction.id).label('total_count'),
                            func.sum(Transaction.total_amount).label('total_amount'),
                            func.sum(Transaction.tax_amount).label('total_tax'),
                            func.sum(Transaction.net_amount).label('total_net')
                        )
                        .first())
        
        # Get voided transactions count
        voided_count = (base_query
                       .filter(Transaction.is_voided == True)
                       .count())
        
        # Get payment method breakdown
        payment_breakdown = (base_query
                           .filter(Transaction.is_voided == False)
                           .with_entities(
                               Transaction.payment_method,
                               func.sum(Transaction.total_amount).label('amount')
                           )
                           .group_by(Transaction.payment_method)
                           .all())
        
        return {
            'total_transactions': sales_summary.total_count or 0,
            'total_amount': float(sales_summary.total_amount or 0),
            'total_tax': float(sales_summary.total_tax or 0),
            'total_net': float(sales_summary.total_net or 0),
            'voided_transactions': voided_count,
            'payment_breakdown': {method: float(amount) for method, amount in payment_breakdown}
        }
    
    def void_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Void a transaction"""
        transaction = self.get_by_id(transaction_id)
        if transaction:
            transaction.is_voided = True
            transaction.voided_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(transaction)
        return transaction

class DailyReportRepository:
    """Repository for managing daily reports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, report: DailyReport) -> DailyReport:
        """Create a new daily report"""
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def get_by_id(self, report_id: int) -> Optional[DailyReport]:
        """Get report by ID"""
        return self.db.query(DailyReport).filter(DailyReport.id == report_id).first()
    
    def get_by_business_and_date(self, business_id: int, report_date: date, report_type: str) -> Optional[DailyReport]:
        """Get report by business, date and type"""
        start_of_day = datetime.combine(report_date, datetime.min.time())
        end_of_day = datetime.combine(report_date, datetime.max.time())
        
        return (self.db.query(DailyReport)
                .filter(
                    and_(
                        DailyReport.business_id == business_id,
                        DailyReport.report_date >= start_of_day,
                        DailyReport.report_date <= end_of_day,
                        DailyReport.report_type == report_type
                    )
                )
                .first())
    
    def get_by_tin_and_date(self, tin_number: str, report_date: date, report_type: str) -> Optional[DailyReport]:
        """Get report by TIN, date and type"""
        start_of_day = datetime.combine(report_date, datetime.min.time())
        end_of_day = datetime.combine(report_date, datetime.max.time())
        
        return (self.db.query(DailyReport)
                .join(Business, DailyReport.business_id == Business.id)
                .filter(
                    and_(
                        Business.tin_number == tin_number,
                        DailyReport.report_date >= start_of_day,
                        DailyReport.report_date <= end_of_day,
                        DailyReport.report_type == report_type
                    )
                )
                .first())
    
    def get_reports_by_tin(self, tin_number: str, limit: int = 50, offset: int = 0) -> List[DailyReport]:
        """Get reports by business TIN"""
        return (self.db.query(DailyReport)
                .join(Business, DailyReport.business_id == Business.id)
                .filter(Business.tin_number == tin_number)
                .order_by(desc(DailyReport.created_at))
                .offset(offset)
                .limit(limit)
                .all())
    
    def get_next_report_number(self, business_id: int, report_type: str) -> int:
        """Get the next sequential report number for a business"""
        last_report = (self.db.query(DailyReport)
                      .filter(
                          and_(
                              DailyReport.business_id == business_id,
                              DailyReport.report_type == report_type
                          )
                      )
                      .order_by(desc(DailyReport.report_number))
                      .first())
        
        return (last_report.report_number + 1) if last_report else 1
    
    def has_z_report_for_date(self, business_id: int, report_date: date) -> bool:
        """Check if Z report exists for a specific date"""
        return self.get_by_business_and_date(business_id, report_date, "Z") is not None
    
    def get_period_reports(self, tin_number: str, start_date: date, end_date: date) -> List[DailyReport]:
        """Get reports within a date range"""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        return (self.db.query(DailyReport)
                .join(Business, DailyReport.business_id == Business.id)
                .filter(
                    and_(
                        Business.tin_number == tin_number,
                        DailyReport.report_date >= start_datetime,
                        DailyReport.report_date <= end_datetime
                    )
                )
                .order_by(DailyReport.report_date)
                .all())