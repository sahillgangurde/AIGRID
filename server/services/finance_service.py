"""
Financial Records, Transactions, and Subscriptions Engine for FRAME.
Conforms to Section 18 of the Master Specification:
- Gross, platform fee, and net calculation
- Explicit demo mode status labels ('demo_completed', 'demo_settled', 'demo_active')
- Strict participant authorization checks
- Server-side state transitions (never trust frontend claims of payment)
"""

import json
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.db.models import Transaction, PayoutRecord, Subscription, Project, Profile, AuditLog

PLATFORM_FEE_PERCENT = 0.10 # 10%

class FinanceService:
    @classmethod
    def create_project_transaction(
        cls,
        db: Session,
        brand_id: str,
        creator_id: str,
        project_id: str,
        gross_amount: float,
        currency: str = "INR",
        provider_ref: Optional[str] = "DEMO_STRIPE_CH_9921"
    ) -> Transaction:
        # Validate participants
        brand = db.query(Profile).filter(Profile.id == brand_id).first()
        creator = db.query(Profile).filter(Profile.id == creator_id).first()
        if not brand or not creator:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand or Creator not found.")

        fee = round(gross_amount * PLATFORM_FEE_PERCENT, 2)
        net = round(gross_amount - fee, 2)

        tx = Transaction(
            project_id=project_id,
            brand_id=brand_id,
            creator_id=creator_id,
            gross_amount=gross_amount,
            platform_fee=fee,
            net_amount=net,
            currency=currency,
            status="demo_completed",
            provider_reference=provider_ref
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        # Automatic demo payout creation
        payout = PayoutRecord(
            creator_id=creator_id,
            transaction_id=tx.id,
            amount=net,
            currency=currency,
            status="demo_settled",
            provider_reference=f"PAYOUT_{provider_ref}"
        )
        db.add(payout)
        db.commit()

        # Audit log
        db.add(AuditLog(
            actor_id=brand_id,
            action="CREATE_DEMO_TRANSACTION",
            resource_type="transaction",
            resource_id=tx.id,
            metadata_json=json.dumps({"gross": gross_amount, "net": net, "fee": fee, "is_demo": True})
        ))
        db.commit()
        return tx

    @classmethod
    def get_user_transactions(cls, db: Session, user_id: str) -> List[Transaction]:
        """Returns transactions where user is either brand or creator."""
        return db.query(Transaction).filter(
            (Transaction.brand_id == user_id) | (Transaction.creator_id == user_id)
        ).order_by(Transaction.created_at.desc()).all()

    @classmethod
    def get_creator_payouts(cls, db: Session, creator_id: str) -> List[PayoutRecord]:
        return db.query(PayoutRecord).filter(
            PayoutRecord.creator_id == creator_id
        ).order_by(PayoutRecord.created_at.desc()).all()

    @classmethod
    def get_creator_earnings_summary(cls, db: Session, creator_id: str) -> Dict[str, Any]:
        payouts = cls.get_creator_payouts(db, creator_id)
        total_earned = sum(p.amount for p in payouts)
        return {
            "creator_id": creator_id,
            "total_earnings_inr": total_earned,
            "settled_payouts_count": len(payouts),
            "currency": "INR",
            "is_demo": True,
            "payouts": payouts
        }

    # ── CreatorGrid Escrow Flow: Markup Pricing & Advance Deposit ──

    @classmethod
    def calculate_brand_quote(cls, creator_quote: float, markup_percent: float = 0.20) -> Dict[str, Any]:
        """
        Markup pricing engine (pitch: creator asks ₹1,00,000 → brand sees ₹1,20,000).
        The markup portion doubles as the advance deposit the brand pays BEFORE
        contact reveal. Creator's quote is never shown to the brand, and the brand's
        payable is never shown to the creator.
        """
        if creator_quote < 0:
            raise ValueError("creator_quote cannot be negative")
        markup_amount = round(creator_quote * markup_percent, 2)
        brand_payable = round(creator_quote + markup_amount, 2)
        return {
            "creator_quote": round(creator_quote, 2),          # INTERNAL — creator only
            "markup_percent": markup_percent,
            "markup_amount": markup_amount,                    # = advance deposit
            "brand_payable": brand_payable,                    # BRAND-FACING
            "platform_margin_estimate": round(brand_payable - creator_quote, 2),
            "advance_deposit": markup_amount,
            "explain": (
                f"Creator settles at {round(creator_quote, 2)}. Brand pays {brand_payable} "
                f"(20% platform margin). The margin ({markup_amount}) is the advance deposit "
                "locked in escrow before contacts unlock."
            )
        }

    @classmethod
    def create_advance_deposit(
        cls,
        db: Session,
        project: Project,
        advance_amount: Optional[float] = None,
        provider_reference: Optional[str] = None
    ) -> Transaction:
        """
        Locks the brand's advance deposit as an escrow Transaction.
        Auth + participant checks are the router's job; this is the ledger engine.
        Sets project.escrow_state → 'advance_locked' (gate for identity reveal).
        """
        if hasattr(project, "escrow_state") and project.escrow_state == "advance_locked":
            raise HTTPException(status_code=409, detail="Advance deposit already locked for this project.")

        amount = round(float(advance_amount if advance_amount is not None else (project.advance_amount or 0.0)), 2)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Advance amount must be greater than zero.")

        # Idempotency: a held/locked advance transaction already exists for this project?
        existing = db.query(Transaction).filter(
            Transaction.project_id == project.id,
            Transaction.status == "held_in_escrow"
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="An escrow deposit is already held for this project.")

        reference = provider_reference or f"ADVANCE_{uuid4().hex[:10].upper()}"
        tx = Transaction(
            project_id=project.id,
            brand_id=project.brand_id,
            creator_id=project.creator_id,
            gross_amount=amount,
            platform_fee=amount,     # advance is pure platform margin under markup pricing
            net_amount=0.0,          # nothing released to creator until milestones settle
            currency=project.currency,
            status="held_in_escrow",
            provider_reference=reference
        )
        db.add(tx)

        project.advance_amount = amount
        project.escrow_state = "advance_locked"
        project.advance_locked_at = datetime.now(timezone.utc)

        db.add(AuditLog(
            actor_id=project.brand_id,
            action="ADVANCE_DEPOSIT_LOCKED",
            resource_type="project",
            resource_id=project.id,
            metadata_json=json.dumps({
                "amount": amount,
                "currency": project.currency,
                "provider_reference": reference,
                "escrow_state": "advance_locked"
            })
        ))
        db.commit()
        db.refresh(tx)
        return tx
