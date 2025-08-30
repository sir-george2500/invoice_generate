from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from models.transaction import Transaction
from models.business import Business
from schemas.report_schemas import TransactionCreate, TransactionResponse, MessageResponse
from repositories.business_repository import BusinessRepository
from repositories.report_repository import TransactionRepository
from middleware.dependencies import get_current_user

class TransactionController:
    """Controller for managing transactions (for testing purposes)"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])
        self._register_routes()
    
    def _register_routes(self):
        """Register transaction routes"""
        
        self.router.add_api_route(
            "/",
            self.create_transaction,
            methods=["POST"],
            response_model=TransactionResponse,
            summary="Create Transaction",
            description="Create a new transaction for testing reports"
        )
        
        self.router.add_api_route(
            "/{tin_number}",
            self.get_transactions,
            methods=["GET"],
            response_model=List[TransactionResponse],
            summary="Get Transactions",
            description="Get transactions for a business by TIN"
        )
        
        self.router.add_api_route(
            "/void/{transaction_id}",
            self.void_transaction,
            methods=["PUT"],
            response_model=MessageResponse,
            summary="Void Transaction",
            description="Mark a transaction as voided"
        )
    
    async def create_transaction(
        self,
        transaction_data: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Create a new transaction"""
        business_repo = BusinessRepository(db)
        transaction_repo = TransactionRepository(db)
        
        # Get business by TIN
        business = business_repo.get_by_tin(transaction_data.business_tin)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with TIN {transaction_data.business_tin} not found"
            )
        
        # Create transaction
        transaction = Transaction(
            business_id=business.id,
            invoice_number=transaction_data.invoice_number,
            transaction_type=transaction_data.transaction_type,
            total_amount=transaction_data.total_amount,
            tax_amount=transaction_data.tax_amount,
            net_amount=transaction_data.net_amount,
            payment_method=transaction_data.payment_method,
            currency=transaction_data.currency,
            customer_name=transaction_data.customer_name,
            customer_tin=transaction_data.customer_tin,
            receipt_number=transaction_data.receipt_number
        )
        
        created_transaction = transaction_repo.create(transaction)
        return TransactionResponse.model_validate(created_transaction)
    
    async def get_transactions(
        self,
        tin_number: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Get transactions for a business"""
        transaction_repo = TransactionRepository(db)
        transactions = transaction_repo.get_by_business_tin(tin_number)
        return [TransactionResponse.model_validate(t) for t in transactions]
    
    async def void_transaction(
        self,
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """Void a transaction"""
        transaction_repo = TransactionRepository(db)
        transaction = transaction_repo.void_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return MessageResponse(message="Transaction voided successfully")