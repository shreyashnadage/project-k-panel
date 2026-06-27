"""
SQLAlchemy Database Models for Tally Sync Platform

Schema includes:
- Tenants: Customer accounts
- Ledgers: Chart of accounts
- Vouchers: Transactions
- Heartbeats: Agent status tracking
- Audit logs: For debugging and compliance
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import uuid


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Tenant(Base):
    """Customer/tenant account."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    api_key_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Tenant {self.name}>"


class Ledger(Base):
    """Chart of accounts (ledger master)."""
    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    company_guid = Column(String(255), nullable=False)
    ledger_guid = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    parent = Column(String(500))
    ledger_type = Column(String(100))
    opening_balance = Column(String(30))
    closing_balance = Column(String(30))
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Unique constraint: same ledger not inserted twice per company
    __table_args__ = (
        Index("ix_ledger_dedup", "tenant_id", "company_guid", "ledger_guid", unique=True),
    )

    def __repr__(self):
        return f"<Ledger {self.name}>"


class Voucher(Base):
    """Transactions (sales, purchases, receipts, payments, etc.)."""
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    company_guid = Column(String(255), nullable=False)
    voucher_guid = Column(String(255), nullable=False)
    voucher_type = Column(String(50), nullable=False)  # Sales, Purchase, Receipt, Payment, Journal
    voucher_number = Column(String(100))
    date = Column(String(10), nullable=False)  # ISO 8601 YYYY-MM-DD
    party = Column(String(500))  # Customer/supplier name (may be Unicode)
    narration = Column(Text)  # Voucher notes
    amount = Column(String(30))  # String to preserve precision
    raw_data = Column(Text)  # Raw JSON for future expansion
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    agent_version = Column(String(20))

    # Unique constraint: idempotent deduplication by (tenant, company, voucher_guid)
    __table_args__ = (
        Index("ix_voucher_dedup", "tenant_id", "company_guid", "voucher_guid", unique=True),
        Index("ix_voucher_date", "tenant_id", "date"),  # For range queries
    )

    def __repr__(self):
        return f"<Voucher {self.voucher_number}>"


class AgentHeartbeat(Base):
    """Agent status tracking for fleet monitoring."""
    __tablename__ = "agent_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    agent_version = Column(String(20))
    company_guid = Column(String(255))
    last_sync_completed_at = Column(DateTime(timezone=True))
    last_extraction_count = Column(Integer)  # How many records extracted
    queue_depth = Column(Integer, default=0)  # Records pending transmission
    tally_reachable = Column(Boolean)  # Is Tally HTTP accessible?
    last_error_code = Column(String(50))  # Error code if last sync failed
    last_error_message = Column(Text)  # Error details
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Heartbeat {self.tenant_id}>"


class SyncAuditLog(Base):
    """Detailed audit trail of all data received."""
    __tablename__ = "sync_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    company_guid = Column(String(255))
    record_type = Column(String(20))  # 'voucher' or 'ledger'
    record_guid = Column(String(255))  # voucher_guid or ledger_guid
    action = Column(String(20))  # 'inserted' or 'duplicate'
    transmitted_at = Column(DateTime(timezone=True))
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AuditLog {self.action}>"
