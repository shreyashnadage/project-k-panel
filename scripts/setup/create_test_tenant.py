#!/usr/bin/env python3
"""
Create test tenant for Phase 2 API testing.

Run this once before testing the API.
Creates a test tenant and prints the API key.
"""

import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloudplatform.db.models import Base, Tenant

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tally_sync_test.db")

print("=" * 70)
print("CREATE TEST TENANT FOR PHASE 2 API")
print("=" * 70)
print()
print(f"Database: {DATABASE_URL}")
print()

# Create engine and tables
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
print("✓ Database tables created")

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Check if tenant already exists
existing = session.query(Tenant).filter_by(id="test-tenant-001").first()
if existing:
    print("✓ Test tenant already exists (test-tenant-001)")
    print()
    print("API Key: test-api-key-12345")
    session.close()
    exit(0)

# Create test tenant
api_key = "test-api-key-12345"
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

tenant = Tenant(
    id="test-tenant-001",
    name="Bhrama Enterprises",
    api_key_hash=api_key_hash,
    is_active=True
)

session.add(tenant)
session.commit()

print("✓ Tenant created successfully")
print()
print("Tenant Details:")
print(f"  ID: test-tenant-001")
print(f"  Name: Bhrama Enterprises")
print(f"  API Key: {api_key}")
print()

print("=" * 70)
print("Ready to test! Use these values:")
print(f"  x-api-key: {api_key}")
print(f"  tenant_id: test-tenant-001")
print("=" * 70)

session.close()
