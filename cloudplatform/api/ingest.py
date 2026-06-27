"""
Ingest API Endpoints

Receives extracted data from agents and stores in database.
Handles idempotent deduplication and request validation.
"""

import hashlib
import json
import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cloudplatform.db.models import Tenant, Ledger, Voucher, SyncAuditLog
from cloudplatform.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas (Request/Response)
# ────────────────────────────────────────────────────────────────────────────

class LedgerPayload(BaseModel):
    """Single ledger from agent."""
    company_guid: str
    company_name: str
    ledger_guid: str
    name: str
    parent: Optional[str] = None
    ledger_type: Optional[str] = None
    opening_balance: Optional[str] = None
    closing_balance: Optional[str] = None


class VoucherPayload(BaseModel):
    """Single voucher from agent."""
    company_guid: str
    company_name: str
    voucher_guid: str
    voucher_type: str
    voucher_number: Optional[str] = None
    date: str  # YYYY-MM-DD
    party: Optional[str] = None
    narration: Optional[str] = None
    amount: Optional[str] = None
    agent_version: Optional[str] = None

    @field_validator("voucher_type")
    @classmethod
    def validate_voucher_type(cls, v):
        """Validate voucher type is known."""
        allowed = {"Sales", "Purchase", "Receipt", "Payment", "Journal", "Debit Note", "Credit Note"}
        if v not in allowed:
            logger.warning(f"Uncommon voucher type: {v}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Validate date format YYYY-MM-DD."""
        try:
            from datetime import datetime
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
        return v


class LedgerBatch(BaseModel):
    """Batch of ledgers from agent."""
    tenant_id: str
    ledgers: List[LedgerPayload]


class VoucherBatch(BaseModel):
    """Batch of vouchers from agent."""
    tenant_id: str
    vouchers: List[VoucherPayload]


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""
    accepted: int
    duplicates: int
    errors: int
    message: str


# ────────────────────────────────────────────────────────────────────────────
# Authentication
# ────────────────────────────────────────────────────────────────────────────

def verify_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)) -> Tenant:
    """Verify API key and return authenticated tenant."""
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    tenant = db.query(Tenant).filter(
        Tenant.api_key_hash == key_hash,
        Tenant.is_active == True
    ).first()

    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return tenant


# ────────────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.post("/v1/ledgers", response_model=IngestResponse)
def ingest_ledgers(batch: LedgerBatch, tenant: Tenant = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Ingest ledger master data.

    Idempotent: sending the same ledger twice results in 1 accepted, 1 duplicate.
    """
    if tenant.id != batch.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch")

    accepted = duplicates = errors = 0

    for ledger in batch.ledgers:
        try:
            # Use ON CONFLICT DO NOTHING for idempotent insert
            stmt = pg_insert(Ledger).values(
                tenant_id=tenant.id,
                company_guid=ledger.company_guid,
                ledger_guid=ledger.ledger_guid,
                name=ledger.name,
                parent=ledger.parent,
                ledger_type=ledger.ledger_type,
                opening_balance=ledger.opening_balance,
                closing_balance=ledger.closing_balance,
            ).on_conflict_do_nothing(
                index_elements=["tenant_id", "company_guid", "ledger_guid"]
            )

            result = db.execute(stmt)
            if result.rowcount == 1:
                accepted += 1
                # Log successful insert
                db.add(SyncAuditLog(
                    tenant_id=tenant.id,
                    company_guid=ledger.company_guid,
                    record_type="ledger",
                    record_guid=ledger.ledger_guid,
                    action="inserted",
                    transmitted_at=datetime.now(timezone.utc),
                ))
            else:
                duplicates += 1
                # Log duplicate
                db.add(SyncAuditLog(
                    tenant_id=tenant.id,
                    company_guid=ledger.company_guid,
                    record_type="ledger",
                    record_guid=ledger.ledger_guid,
                    action="duplicate",
                    transmitted_at=datetime.now(timezone.utc),
                ))

        except Exception as e:
            errors += 1
            logger.error(f"Error ingesting ledger {ledger.ledger_guid}: {e}")

    db.commit()

    return IngestResponse(
        accepted=accepted,
        duplicates=duplicates,
        errors=errors,
        message=f"Ledgers: {accepted} new, {duplicates} duplicates, {errors} errors"
    )


@router.post("/v1/vouchers", response_model=IngestResponse)
def ingest_vouchers(batch: VoucherBatch, tenant: Tenant = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Ingest voucher (transaction) data.

    Idempotent: sending the same voucher twice results in 1 accepted, 1 duplicate.
    Same voucher_guid from same company = duplicate (no duplicate key errors).
    """
    if tenant.id != batch.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch")

    accepted = duplicates = errors = 0

    for voucher in batch.vouchers:
        try:
            # Prepare raw data JSON
            raw_data = {
                "voucher_type": voucher.voucher_type,
                "party": voucher.party,
                "narration": voucher.narration,
                "amount": voucher.amount,
            }

            # Use ON CONFLICT DO NOTHING for idempotent insert
            stmt = pg_insert(Voucher).values(
                tenant_id=tenant.id,
                company_guid=voucher.company_guid,
                voucher_guid=voucher.voucher_guid,
                voucher_type=voucher.voucher_type,
                voucher_number=voucher.voucher_number,
                date=voucher.date,
                party=voucher.party,
                narration=voucher.narration,
                amount=voucher.amount,
                raw_data=json.dumps(raw_data, ensure_ascii=False),
                agent_version=voucher.agent_version,
            ).on_conflict_do_nothing(
                index_elements=["tenant_id", "company_guid", "voucher_guid"]
            )

            result = db.execute(stmt)
            if result.rowcount == 1:
                accepted += 1
                # Log successful insert
                db.add(SyncAuditLog(
                    tenant_id=tenant.id,
                    company_guid=voucher.company_guid,
                    record_type="voucher",
                    record_guid=voucher.voucher_guid,
                    action="inserted",
                    transmitted_at=datetime.now(timezone.utc),
                ))
            else:
                duplicates += 1
                # Log duplicate
                db.add(SyncAuditLog(
                    tenant_id=tenant.id,
                    company_guid=voucher.company_guid,
                    record_type="voucher",
                    record_guid=voucher.voucher_guid,
                    action="duplicate",
                    transmitted_at=datetime.now(timezone.utc),
                ))

        except Exception as e:
            errors += 1
            logger.error(f"Error ingesting voucher {voucher.voucher_guid}: {e}")

    db.commit()

    return IngestResponse(
        accepted=accepted,
        duplicates=duplicates,
        errors=errors,
        message=f"Vouchers: {accepted} new, {duplicates} duplicates, {errors} errors"
    )


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "tally-sync-ingest"}


@router.get("/v1/stats")
def get_stats(tenant: Tenant = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get ingest statistics for tenant."""
    voucher_count = db.query(Voucher).filter(Tenant.id == tenant.id).count()
    ledger_count = db.query(Ledger).filter(Tenant.id == tenant.id).count()

    return {
        "tenant_id": tenant.id,
        "total_vouchers": voucher_count,
        "total_ledgers": ledger_count,
    }
