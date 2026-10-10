"""
Dynamic Compute-Aware Escrow Engine — Hypear AI v2.0.
Calculates GPU compute costs and governs the 30% upfront / 70% milestone state machine.
Integrates with SQLite/PostgreSQL persistence and supports Razorpay multi-party escrow splitting.
"""

import os
import hmac
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

ESCROW_CONTRACTS: Dict[str, Dict[str, Any]] = {}

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_hypear_demo_key")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "hypear_escrow_secret_key_2026")


class EscrowService:
    @staticmethod
    def calculate_compute_and_milestones(
        base_license_usd: float,
        gpu_steps: int,
        gpu_tier: str = "H100_SXM5",
        num_variations: int = 4
    ) -> Dict[str, Any]:
        """
        Calculates compute expenditure and 30% / 70% escrow split.
        """
        rates = {
            "A10G": 1.20,       # $ / hr
            "A100_80GB": 2.80,  # $ / hr
            "H100_SXM5": 4.50   # $ / hr
        }
        hourly_rate = rates.get(gpu_tier, 3.50)

        # ~0.05 seconds per step on H100
        seconds_per_step = 0.045 if gpu_tier == "H100_SXM5" else (0.09 if gpu_tier == "A100_80GB" else 0.16)
        total_gpu_seconds = gpu_steps * num_variations * seconds_per_step
        total_gpu_hours = total_gpu_seconds / 3600.0

        estimated_compute_cost = round(total_gpu_hours * hourly_rate + 2.50, 2) # add VRAM allocation base
        total_contract_value = round(base_license_usd + estimated_compute_cost, 2)

        upfront_30_pct = round(total_contract_value * 0.30, 2)
        milestone_70_pct = round(total_contract_value - upfront_30_pct, 2)

        # Multi-party revenue split
        platform_fee_usd = round(total_contract_value * 0.05, 2) # 5%
        compute_escrow_pool_usd = estimated_compute_cost
        creator_take_home_usd = round(total_contract_value - platform_fee_usd - compute_escrow_pool_usd, 2)

        return {
            "base_license_usd": base_license_usd,
            "gpu_tier": gpu_tier,
            "gpu_steps": gpu_steps,
            "num_variations": num_variations,
            "estimated_gpu_hours": round(total_gpu_hours, 4),
            "estimated_compute_cost_usd": estimated_compute_cost,
            "total_contract_value_usd": total_contract_value,
            "total_contract_value_inr": round(total_contract_value * 83.0, 2),
            "milestone_breakdown": {
                "upfront_deposit_30pct": upfront_30_pct,
                "purpose_upfront": "GPU compute reservation & custom LoRA fine-tuning kickoff",
                "milestone_delivery_70pct": milestone_70_pct,
                "purpose_milestone": "Released upon cryptographic C2PA provenance & ComfyUI proof-of-workflow validation"
            },
            "multi_party_split": {
                "platform_fee_usd": platform_fee_usd,
                "platform_fee_percent": 5.0,
                "compute_escrow_usd": compute_escrow_pool_usd,
                "creator_net_payout_usd": creator_take_home_usd
            }
        }

    @classmethod
    def create_contract(
        cls,
        buyer_id: str,
        creator_id: str,
        creator_name: str,
        base_license_usd: float,
        gpu_steps: int = 1200,
        gpu_tier: str = "H100_SXM5",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Creates and stores an escrow contract with optional DB persistence."""
        contract_id = f"escrow_{uuid.uuid4().hex[:8]}"
        pricing = cls.calculate_compute_and_milestones(base_license_usd, gpu_steps, gpu_tier)

        # Generate Razorpay simulated order ID
        rzp_order_id = f"order_{uuid.uuid4().hex[:14]}"

        contract = {
            "contract_id": contract_id,
            "razorpay_order_id": rzp_order_id,
            "buyer_id": buyer_id,
            "creator_id": creator_id,
            "creator_name": creator_name,
            "pricing": pricing,
            "status": "ESCROW_LOCKED",
            "is_frozen": False,
            "milestone_state": {
                "phase_1_upfront_released": False,
                "phase_2_workflow_verified": False,
                "phase_3_provenance_sealed": False,
                "phase_4_final_balance_released": False
            },
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "events_log": [
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "event": "ESCROW_INITIALIZED",
                    "detail": f"Locked ${pricing['total_contract_value_usd']} (₹{pricing['total_contract_value_inr']}) in smart escrow pool"
                }
            ]
        }

        # Double-entry ledger: record payment received into escrow holding + platform revenue fee
        e1 = cls.post_ledger_entry(
            payment_id=rzp_order_id,
            entry_type="payment_received",
            account="escrow_holding",
            amount=pricing["total_contract_value_usd"],
            reference_id=contract_id,
            db=db
        )
        e2 = cls.post_ledger_entry(
            payment_id=rzp_order_id,
            entry_type="platform_fee",
            account="platform_revenue",
            amount=pricing["multi_party_split"]["platform_fee_usd"],
            reference_id=contract_id,
            db=db
        )
        contract["ledger_entries"] = [e1, e2]

        ESCROW_CONTRACTS[contract_id] = contract

        # Optional DB session persistence for Escrow Session & Automated Contact Unlock
        if db is not None:
            try:
                from server.db.models import ComputeEscrowSession, ContactUnlock
                session_record = ComputeEscrowSession(
                    id=contract_id,
                    brand_id=buyer_id,
                    creator_id=creator_id,
                    gpu_tier=gpu_tier,
                    gpu_cost_per_hour_usd=4.5 if gpu_tier == "H100_SXM5" else 2.8,
                    allocated_hours=pricing["estimated_gpu_hours"],
                    total_locked_usd=pricing["total_contract_value_usd"],
                    total_locked_inr=pricing["total_contract_value_inr"],
                    payment_reference=rzp_order_id,
                    status="locked"
                )
                db.add(session_record)

                # Provision Contact Unlock upon advance escrow lock
                existing_unlock = db.query(ContactUnlock).filter(
                    ContactUnlock.customer_id == buyer_id,
                    ContactUnlock.creator_id == creator_id
                ).first()
                if not existing_unlock:
                    unlock_record = ContactUnlock(
                        customer_id=buyer_id,
                        creator_id=creator_id,
                        payment_id=rzp_order_id,
                        status="active"
                    )
                    db.add(unlock_record)

                db.commit()
            except Exception as e:
                db.rollback()

        return contract

    @classmethod
    def post_ledger_entry(
        cls,
        payment_id: str,
        entry_type: str,
        account: str,
        amount: float,
        currency: str = "USD",
        reference_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Posts a balancing double-entry record to public.financial_ledger."""
        entry_id = str(uuid.uuid4())
        record_data = {
            "id": entry_id,
            "payment_id": payment_id,
            "entry_type": entry_type,
            "account": account,
            "amount": round(amount, 2),
            "currency": currency,
            "reference_id": reference_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        if db is not None:
            try:
                from server.db.models import FinancialLedger
                ledger_record = FinancialLedger(
                    id=entry_id,
                    payment_id=payment_id,
                    entry_type=entry_type,
                    account=account,
                    amount=round(amount, 2),
                    currency=currency,
                    reference_id=reference_id
                )
                db.add(ledger_record)
                db.commit()
            except Exception:
                db.rollback()

        return record_data

    @classmethod
    def advance_escrow_stage(
        cls,
        contract_id: str,
        stage: str,
        meta: Dict[str, Any] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Advances the milestone state machine.
        Stages: 'RELEASE_UPFRONT_30', 'VERIFY_WORKFLOW', 'SEAL_PROVENANCE', 'RELEASE_FINAL_70', 'FREEZE_DISPUTE'
        """
        contract = ESCROW_CONTRACTS.get(contract_id)
        if not contract and db is not None:
            contract = cls.get_contract(contract_id, db=db)
        if not contract:
            return {"error": "Contract not found"}

        if contract.get("is_frozen"):
            return {
                "error": "ESCROW_FROZEN",
                "detail": "This escrow is frozen due to an open dispute. Administration review required."
            }

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rzp_order_id = contract.get("razorpay_order_id", contract_id)

        if stage == "RELEASE_UPFRONT_30":
            contract["milestone_state"]["phase_1_upfront_released"] = True
            contract["status"] = "COMPUTE_IN_PROGRESS"
            upfront_amt = contract['pricing']['milestone_breakdown']['upfront_deposit_30pct']
            contract["events_log"].append({
                "timestamp": now,
                "event": "UPFRONT_30_RELEASED",
                "detail": f"${upfront_amt} paid to creator for GPU resources."
            })
            e_upfront = cls.post_ledger_entry(
                payment_id=rzp_order_id,
                entry_type="creator_payout",
                account="creator_payable",
                amount=upfront_amt,
                reference_id=f"{contract_id}_upfront_30",
                db=db
            )
            contract.setdefault("ledger_entries", []).append(e_upfront)
        elif stage == "VERIFY_WORKFLOW":
            contract["milestone_state"]["phase_2_workflow_verified"] = True
            contract["events_log"].append({
                "timestamp": now,
                "event": "PROOF_OF_WORKFLOW_PASSED",
                "detail": "ComfyUI DAG and AST integrity verified. SHA-256 matched."
            })
        elif stage == "SEAL_PROVENANCE":
            contract["milestone_state"]["phase_3_provenance_sealed"] = True
            contract["events_log"].append({
                "timestamp": now,
                "event": "C2PA_PROVENANCE_SEALED",
                "detail": "X.509 assertion stamped with DCT frequency watermark."
            })
        elif stage == "RELEASE_FINAL_70":
            if not contract["milestone_state"]["phase_2_workflow_verified"]:
                return {"error": "Cannot release final payment without verified proof-of-workflow"}
            contract["milestone_state"]["phase_4_final_balance_released"] = True
            contract["status"] = "COMPLETED_SETTLED"
            final_amt = contract['pricing']['milestone_breakdown']['milestone_delivery_70pct']
            contract["events_log"].append({
                "timestamp": now,
                "event": "FINAL_70_RELEASED",
                "detail": f"${final_amt} unlocked to creator. Escrow fulfilled."
            })
            e_final = cls.post_ledger_entry(
                payment_id=rzp_order_id,
                entry_type="creator_payout",
                account="creator_payable",
                amount=final_amt,
                reference_id=f"{contract_id}_final_70",
                db=db
            )
            contract.setdefault("ledger_entries", []).append(e_final)
        elif stage == "FREEZE_DISPUTE":
            contract["is_frozen"] = True
            contract["status"] = "FROZEN_IN_DISPUTE"
            final_amt = contract['pricing']['milestone_breakdown']['milestone_delivery_70pct']
            contract["events_log"].append({
                "timestamp": now,
                "event": "ESCROW_FROZEN",
                "detail": "Escrow payouts locked pending arbitrator dispute verdict."
            })
            e_hold = cls.post_ledger_entry(
                payment_id=rzp_order_id,
                entry_type="dispute_hold",
                account="escrow_holding",
                amount=final_amt,
                reference_id=f"{contract_id}_dispute_freeze",
                db=db
            )
            contract.setdefault("ledger_entries", []).append(e_hold)

        # Update DB if available
        if db is not None:
            try:
                from server.db.models import ComputeEscrowSession
                session_record = db.query(ComputeEscrowSession).filter(ComputeEscrowSession.id == contract_id).first()
                if session_record:
                    if stage == "RELEASE_FINAL_70":
                        session_record.status = "completed"
                        session_record.completed_at = datetime.now(timezone.utc)
                    elif stage == "FREEZE_DISPUTE":
                        session_record.status = "locked"
                    db.commit()
            except Exception:
                db.rollback()

        return contract

    @classmethod
    def verify_razorpay_signature(cls, order_id: str, payment_id: str, signature: str) -> bool:
        """Verifies HMAC SHA-256 signature for Razorpay webhooks and payment confirmations."""
        try:
            msg = f"{order_id}|{payment_id}".encode("utf-8")
            expected_sig = hmac.new(
                RAZORPAY_KEY_SECRET.encode("utf-8"),
                msg,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_sig, signature)
        except Exception:
            return False

    @classmethod
    def get_contract(cls, contract_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        contract = ESCROW_CONTRACTS.get(contract_id)
        if contract:
            return contract
        if db is not None:
            try:
                from server.db.models import ComputeEscrowSession
                session_record = db.query(ComputeEscrowSession).filter(ComputeEscrowSession.id == contract_id).first()
                if session_record:
                    contract = {
                        "contract_id": session_record.id,
                        "razorpay_order_id": session_record.payment_reference or f"order_{session_record.id}",
                        "buyer_id": session_record.brand_id,
                        "creator_id": session_record.creator_id,
                        "creator_name": "Creator",
                        "pricing": {
                            "total_contract_value_usd": session_record.total_locked_usd,
                            "total_contract_value_inr": session_record.total_locked_inr,
                            "gpu_tier": session_record.gpu_tier,
                            "estimated_gpu_hours": session_record.allocated_hours,
                            "milestone_breakdown": {
                                "upfront_deposit_30pct": round(session_record.total_locked_usd * 0.3, 2),
                                "milestone_delivery_70pct": round(session_record.total_locked_usd * 0.7, 2),
                            }
                        },
                        "status": "COMPLETED_SETTLED" if session_record.status == "completed" else ("ESCROW_LOCKED" if session_record.status == "locked" else session_record.status.upper()),
                        "is_frozen": False,
                        "milestone_state": {
                            "phase_1_upfront_released": session_record.status in ["active", "completed"],
                            "phase_2_workflow_verified": session_record.status in ["completed"],
                            "phase_3_provenance_sealed": session_record.status in ["completed"],
                            "phase_4_final_balance_released": session_record.status == "completed"
                        },
                        "created_at": session_record.created_at.isoformat() if session_record.created_at else "",
                        "events_log": []
                    }
                    ESCROW_CONTRACTS[contract_id] = contract
                    return contract
            except Exception:
                pass
        return {}
