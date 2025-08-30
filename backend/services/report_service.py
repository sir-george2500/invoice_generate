from typing import Optional, Dict, Any
from datetime import datetime, date, time
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.transaction import Transaction, DailyReport
from models.business import Business
from models.user import User
from repositories.transaction_repository import TransactionRepository, DailyReportRepository
from repositories.business_repository import BusinessRepository
from schemas.report_schemas import (
    DailyReportSummary, PaymentMethodBreakdown
)

class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.report_repo = DailyReportRepository(db)
        self.business_repo = BusinessRepository(db)
    
    def generate_x_report(self, tin_number: str, user_id: int) -> DailyReportSummary:
        """Generate X Report - shows current day totals without clearing memory"""
        business = self._get_business_by_tin(tin_number)
        today = date.today()
        
        # Check if day is already finalized with Z report
        if self.report_repo.has_z_report_for_date(business.id, today):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Day has been finalized with Z report. Cannot generate X report."
            )
        
        # Get transaction summary for today
        summary = self.transaction_repo.get_daily_summary(tin_number, today)
        
        # Get next report number
        report_number = self.report_repo.get_next_report_number(business.id, "X")
        
        # Create X report record
        report_data = self._create_report_data(
            business=business,
            report_type="X",
            report_number=report_number,
            summary=summary,
            user_id=user_id,
            is_finalized=False
        )
        
        report = self.report_repo.create(report_data)
        
        return self._format_report_response(report, business, summary)
    
    def generate_z_report(self, tin_number: str, user_id: int) -> DailyReportSummary:
        """Generate Z Report - shows daily totals and clears memory (end of day)"""
        business = self._get_business_by_tin(tin_number)
        today = date.today()
        
        # Check if Z report already exists for today
        if self.report_repo.has_z_report_for_date(business.id, today):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Z report already generated for today. Only one Z report per day is allowed."
            )
        
        # Get transaction summary for today
        summary = self.transaction_repo.get_daily_summary(tin_number, today)
        
        # Validate that there are transactions to report
        if summary['total_transactions'] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transactions found for today. Cannot generate Z report."
            )
        
        # Get next report number
        report_number = self.report_repo.get_next_report_number(business.id, "Z")
        
        # Create Z report record
        report_data = self._create_report_data(
            business=business,
            report_type="Z",
            report_number=report_number,
            summary=summary,
            user_id=user_id,
            is_finalized=True
        )
        
        report = self.report_repo.create(report_data)
        
        return self._format_report_response(report, business, summary)
    
    def get_report_history(
        self, 
        tin_number: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        report_type: Optional[str] = None
    ) -> list[DailyReportSummary]:
        """Get historical reports for a business"""
        business = self._get_business_by_tin(tin_number)
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = date.today().replace(day=1)  # First day of current month
        if not end_date:
            end_date = date.today()
        
        reports = self.report_repo.get_period_reports(tin_number, start_date, end_date)
        
        result = []
        for report in reports:
            # Reconstruct summary from stored report data
            summary = {
                'total_transactions': report.total_transactions,
                'total_amount': float(report.total_sales_amount),
                'total_tax': float(report.total_tax_amount),
                'total_net': float(report.total_net_amount),
                'cash_amount': float(report.cash_amount),
                'card_amount': float(report.card_amount),
                'mobile_amount': float(report.mobile_amount),
                'other_amount': float(report.other_amount),
                'voided_transactions': report.voided_transactions,
                'payment_breakdown': {
                    'CASH': float(report.cash_amount),
                    'CARD': float(report.card_amount),
                    'MOBILE': float(report.mobile_amount),
                    'OTHER': float(report.other_amount)
                }
            }
            
            result.append(self._format_report_response(report, business, summary))
        
        return result
    
    def _get_business_by_tin(self, tin_number: str) -> Business:
        """Get business by TIN number"""
        business = self.business_repo.get_by_tin(tin_number)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with TIN {tin_number} not found"
            )
        if not business.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business account is inactive"
            )
        return business
    
    def _create_report_data(
        self, 
        business: Business, 
        report_type: str, 
        report_number: int, 
        summary: Dict[str, Any], 
        user_id: int,
        is_finalized: bool
    ) -> DailyReport:
        """Create report data object"""
        today = date.today()
        period_start = datetime.combine(today, time.min)
        period_end = datetime.combine(today, time.max)
        
        return DailyReport(
            business_id=business.id,
            report_type=report_type,
            report_date=datetime.now(),
            report_number=report_number,
            total_sales_amount=summary['total_amount'],
            total_tax_amount=summary['total_tax'],
            total_net_amount=summary['total_net'],
            total_transactions=summary['total_transactions'],
            voided_transactions=summary['voided_transactions'],
            refunded_transactions=0,  # Add logic if needed
            cash_amount=summary['payment_breakdown'].get('CASH', 0),
            card_amount=summary['payment_breakdown'].get('CARD', 0),
            mobile_amount=summary['payment_breakdown'].get('MOBILE', 0),
            other_amount=summary['payment_breakdown'].get('OTHER', 0),
            period_start=period_start,
            period_end=period_end,
            generated_by=user_id,
            is_finalized=is_finalized
        )
    
    def _format_report_response(
        self, 
        report: DailyReport, 
        business: Business, 
        summary: Dict[str, Any]
    ) -> DailyReportSummary:
        """Format report data for response"""
        payment_methods = PaymentMethodBreakdown(
            cash_amount=summary['payment_breakdown'].get('CASH', 0),
            card_amount=summary['payment_breakdown'].get('CARD', 0),
            mobile_amount=summary['payment_breakdown'].get('MOBILE', 0),
            other_amount=summary['payment_breakdown'].get('OTHER', 0)
        )
        
        # Get user who generated the report
        user = self.db.query(User).filter(User.id == report.generated_by).first()
        generated_by = user.username if user else "Unknown"
        
        return DailyReportSummary(
            report_type=report.report_type,
            report_number=report.report_number,
            report_date=report.created_at,
            business_tin=business.tin_number,
            business_name=business.business_name,
            period_start=report.period_start,
            period_end=report.period_end,
            total_sales_amount=float(report.total_sales_amount),
            total_tax_amount=float(report.total_tax_amount),
            total_net_amount=float(report.total_net_amount),
            total_transactions=report.total_transactions,
            voided_transactions=report.voided_transactions,
            refunded_transactions=report.refunded_transactions,
            payment_methods=payment_methods,
            is_finalized=report.is_finalized,
            generated_by=generated_by
        )