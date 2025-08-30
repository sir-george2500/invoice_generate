from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from models.transaction import Transaction, DailyReport
from models.business import Business

class TransactionRepository:
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
    
    def get_by_business_and_date_range(
        self, 
        business_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Transaction]:
        """Get transactions for a business within date range"""
        return self.db.query(Transaction).filter(
            and_(
                Transaction.business_id == business_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.is_voided == False
            )
        ).order_by(Transaction.transaction_date).all()
    
    def get_by_tin_and_date_range(
        self, 
        tin_number: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Transaction]:
        """Get transactions for a business TIN within date range"""
        return self.db.query(Transaction).join(Business).filter(
            and_(
                Business.tin_number == tin_number,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.is_voided == False
            )
        ).order_by(Transaction.transaction_date).all()
    
    def get_voided_by_tin_and_date_range(
        self, 
        tin_number: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Transaction]:
        """Get voided transactions for a business TIN within date range"""
        return self.db.query(Transaction).join(Business).filter(
            and_(
                Business.tin_number == tin_number,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.is_voided == True
            )
        ).order_by(Transaction.transaction_date).all()
    
    def get_daily_summary_by_tin(
        self, 
        tin_number: str, 
        target_date: date
    ) -> dict:
        """Get daily transaction summary for a business by TIN"""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        result = self.db.query(
            func.count(Transaction.id).label('total_transactions'),
            func.coalesce(func.sum(Transaction.total_amount), 0).label('total_sales'),
            func.coalesce(func.sum(Transaction.tax_amount), 0).label('total_tax'),
            func.coalesce(func.sum(Transaction.net_amount), 0).label('total_net'),
            func.sum(
                func.case([(Transaction.payment_method == 'CASH', Transaction.total_amount)], else_=0)
            ).label('cash_amount'),
            func.sum(
                func.case([(Transaction.payment_method == 'CARD', Transaction.total_amount)], else_=0)
            ).label('card_amount'),
            func.sum(
                func.case([(Transaction.payment_method == 'MOBILE', Transaction.total_amount)], else_=0)
            ).label('mobile_amount'),
        ).join(Business).filter(
            and_(
                Business.tin_number == tin_number,
                Transaction.transaction_date >= start_datetime,
                Transaction.transaction_date <= end_datetime,
                Transaction.is_voided == False
            )
        ).first()
        
        voided_count = self.db.query(func.count(Transaction.id)).join(Business).filter(
            and_(
                Business.tin_number == tin_number,
                Transaction.transaction_date >= start_datetime,
                Transaction.transaction_date <= end_datetime,
                Transaction.is_voided == True
            )
        ).scalar()
        
        return {
            'total_transactions': result.total_transactions or 0,
            'total_sales': float(result.total_sales or 0),
            'total_tax': float(result.total_tax or 0),
            'total_net': float(result.total_net or 0),
            'cash_amount': float(result.cash_amount or 0),
            'card_amount': float(result.card_amount or 0),
            'mobile_amount': float(result.mobile_amount or 0),
            'other_amount': 0,  # Calculate if needed
            'voided_count': voided_count or 0,
            'refund_count': 0  # Add logic for refunds if needed
        }

class DailyReportRepository:
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
    
    def get_by_business_and_date(
        self, 
        business_id: int, 
        report_date: date, 
        report_type: str
    ) -> Optional[DailyReport]:
        """Get report by business and date"""
        target_date = datetime.combine(report_date, datetime.min.time())
        return self.db.query(DailyReport).filter(
            and_(
                DailyReport.business_id == business_id,
                func.date(DailyReport.report_date) == report_date,
                DailyReport.report_type == report_type
            )
        ).first()
    
    def get_by_tin_and_date_range(
        self, 
        tin_number: str, 
        start_date: date, 
        end_date: date, 
        report_type: Optional[str] = None
    ) -> List[DailyReport]:
        """Get reports by business TIN and date range"""
        query = self.db.query(DailyReport).join(Business).filter(
            and_(
                Business.tin_number == tin_number,
                func.date(DailyReport.report_date) >= start_date,
                func.date(DailyReport.report_date) <= end_date
            )
        )
        
        if report_type:
            query = query.filter(DailyReport.report_type == report_type)
        
        return query.order_by(desc(DailyReport.report_date)).all()
    
    def get_next_report_number(self, business_id: int, report_type: str) -> int:
        """Get the next sequential report number for a business"""
        last_report = self.db.query(DailyReport).filter(
            and_(
                DailyReport.business_id == business_id,
                DailyReport.report_type == report_type
            )
        ).order_by(desc(DailyReport.report_number)).first()
        
        return (last_report.report_number + 1) if last_report else 1
    
    def has_z_report_for_date(self, business_id: int, target_date: date) -> bool:
        """Check if Z report already exists for the date"""
        return self.db.query(DailyReport).filter(
            and_(
                DailyReport.business_id == business_id,
                func.date(DailyReport.report_date) == target_date,
                DailyReport.report_type == "Z",
                DailyReport.is_finalized == True
            )
        ).first() is not None