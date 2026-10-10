"""
Finance, Transactions, and Earnings Router for FRAME.
Conforms to Section 18 of the Master Specification.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Profile, Transaction, PayoutRecord
from server.services.finance_service import FinanceService
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/finance", tags=["Finance & Earnings"])

class DemoCheckoutRequest(BaseModel):
    creator_id: str
    project_id: Optional[str] = None
    gross_amount: float
    currency: Optional[str] = "INR"

@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Returns financial transactions for authenticated brand or creator."""
    txs = FinanceService.get_user_transactions(db, current_user.id)
    return {
        "transactions": [
            {
                "id": t.id,
                "project_id": t.project_id,
                "gross_amount": t.gross_amount,
                "platform_fee": t.platform_fee,
                "net_amount": t.net_amount,
                "currency": t.currency,
                "status": t.status,
                "provider_reference": t.provider_reference,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "is_demo": True
            }
            for t in txs
        ]
    }

@router.get("/earnings")
def get_earnings_summary(db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Returns settled payouts and earnings summary for creator."""
    return FinanceService.get_creator_earnings_summary(db, current_user.id)

@router.post("/demo-checkout")
def create_demo_checkout(
    req: DemoCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Executes demo checkout transaction with 10% platform fee."""
    tx = FinanceService.create_project_transaction(
        db=db,
        brand_id=current_user.id,
        creator_id=req.creator_id,
        project_id=req.project_id,
        gross_amount=req.gross_amount,
        currency=req.currency or "INR"
    )
    return {
        "status": "success",
        "is_demo": True,
        "transaction": {
            "id": tx.id,
            "gross": tx.gross_amount,
            "fee": tx.platform_fee,
            "net": tx.net_amount,
            "status": tx.status
        }
    }
