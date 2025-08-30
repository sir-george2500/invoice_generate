from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from schemas.report_schemas import (
    DailyReportSummary, XReportRequest, ZReportRequest, 
    MessageResponse, ReportFilters
)
from services.report_service import ReportService
from middleware.dependencies import get_current_user

class ReportController:
    """Controller for X and Z reports generation and management"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/reports", tags=["Daily Reports"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all report routes"""
        
        # X Report endpoint
        self.router.add_api_route(
            "/x-report",
            self.generate_x_report,
            methods=["POST"],
            response_model=DailyReportSummary,
            summary="Generate X Report",
            description="Generate X Report showing current daily totals without clearing memory",
            responses={
                200: {"description": "X Report generated successfully"},
                400: {"description": "Invalid request or day already finalized"},
                401: {"description": "Not authenticated"},
                404: {"description": "Business not found"}
            }
        )
        
        # Z Report endpoint
        self.router.add_api_route(
            "/z-report",
            self.generate_z_report,
            methods=["POST"],
            response_model=DailyReportSummary,
            summary="Generate Z Report (End of Day)",
            description="Generate Z Report showing daily totals and ending the fiscal day",
            responses={
                200: {"description": "Z Report generated successfully"},
                400: {"description": "Invalid request or Z report already exists for today"},
                401: {"description": "Not authenticated"},
                404: {"description": "Business not found"}
            }
        )
        
        # Report history endpoint
        self.router.add_api_route(
            "/history/{tin_number}",
            self.get_report_history,
            methods=["GET"],
            response_model=List[DailyReportSummary],
            summary="Get Report History",
            description="Get historical X and Z reports for a business",
            responses={
                200: {"description": "Reports retrieved successfully"},
                401: {"description": "Not authenticated"},
                404: {"description": "Business not found"}
            }
        )
        
        # Get specific report
        self.router.add_api_route(
            "/{report_id}",
            self.get_report_by_id,
            methods=["GET"],
            response_model=DailyReportSummary,
            summary="Get Report by ID",
            description="Retrieve a specific report by its ID",
            responses={
                200: {"description": "Report retrieved successfully"},
                401: {"description": "Not authenticated"},
                404: {"description": "Report not found"}
            }
        )
        
        # Validate business access endpoint
        self.router.add_api_route(
            "/validate-access/{tin_number}",
            self.validate_business_access,
            methods=["GET"],
            response_model=MessageResponse,
            summary="Validate Business Access",
            description="Check if user has access to generate reports for a business",
            responses={
                200: {"description": "Access validated"},
                401: {"description": "Not authenticated"},
                403: {"description": "Access denied"},
                404: {"description": "Business not found"}
            }
        )
    
    async def generate_x_report(
        self, 
        request: XReportRequest, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Generate X Report for a business"""
        report_service = ReportService(db)
        
        # Validate user has access to this business
        self._validate_user_business_access(current_user, request.business_tin, db)
        
        try:
            report = report_service.generate_x_report(request.business_tin, current_user.id)
            return report
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate X report: {str(e)}"
            )
    
    async def generate_z_report(
        self, 
        request: ZReportRequest, 
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Generate Z Report for a business"""
        report_service = ReportService(db)
        
        # Validate user has access to this business
        self._validate_user_business_access(current_user, request.business_tin, db)
        
        try:
            report = report_service.generate_z_report(request.business_tin, current_user.id)
            return report
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate Z report: {str(e)}"
            )
    
    async def get_report_history(
        self, 
        tin_number: str,
        start_date: Optional[date] = Query(None, description="Start date for report history"),
        end_date: Optional[date] = Query(None, description="End date for report history"),
        report_type: Optional[str] = Query(None, regex="^(X|Z)$", description="Report type filter"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get report history for a business"""
        report_service = ReportService(db)
        
        # Validate user has access to this business
        self._validate_user_business_access(current_user, tin_number, db)
        
        try:
            reports = report_service.get_report_history(
                tin_number=tin_number,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type
            )
            return reports
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve report history: {str(e)}"
            )
    
    async def get_report_by_id(
        self, 
        report_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get a specific report by ID"""
        from repositories.transaction_repository import DailyReportRepository
        from repositories.business_repository import BusinessRepository
        
        report_repo = DailyReportRepository(db)
        business_repo = BusinessRepository(db)
        
        # Get the report
        report = report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get business details
        business = business_repo.get_by_id(report.business_id)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated business not found"
            )
        
        # Validate user has access to this business
        self._validate_user_business_access(current_user, business.tin_number, db)
        
        # Format and return report
        report_service = ReportService(db)
        summary = {
            'total_transactions': report.total_transactions,
            'total_sales': float(report.total_sales_amount),
            'total_tax': float(report.total_tax_amount),
            'total_net': float(report.total_net_amount),
            'cash_amount': float(report.cash_amount),
            'card_amount': float(report.card_amount),
            'mobile_amount': float(report.mobile_amount),
            'other_amount': float(report.other_amount),
            'voided_count': report.voided_transactions,
            'refund_count': report.refunded_transactions
        }
        
        return report_service._format_report_response(report, business, summary)
    
    async def validate_business_access(
        self, 
        tin_number: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Validate if user has access to a business"""
        try:
            self._validate_user_business_access(current_user, tin_number, db)
            return MessageResponse(message="Access granted", data={"tin_number": tin_number})
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate access: {str(e)}"
            )
    
    def _validate_user_business_access(self, user: User, tin_number: str, db: Session):
        """Validate if user has access to reports for a specific business"""
        from repositories.business_repository import BusinessRepository
        
        business_repo = BusinessRepository(db)
        business = business_repo.get_by_tin(tin_number)
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with TIN {tin_number} not found"
            )
        
        # Check if user belongs to this business or is admin
        if user.role == "admin":
            return  # Admin can access all businesses
        
        if user.business_id != business.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this business"
            )
        
        if not business.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business account is inactive"
            )