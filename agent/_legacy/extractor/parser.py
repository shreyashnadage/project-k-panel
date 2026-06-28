"""
Tally JSON Response Parser

Converts Tally's JSON API responses into normalized Python dictionaries.
Handles special cases: Devanagari/Unicode characters, empty fields, malformed records.
"""

from decimal import Decimal
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_vouchers(response_json: Dict[str, Any]) -> List[Dict]:
    """
    Parse Tally JSON API response into a list of normalized dictionaries.

    Returns empty list if JSON is malformed or contains no vouchers.

    Args:
        response_json: JSON response from Tally API

    Returns:
        List of voucher dictionaries with keys:
        - id: Unique identifier from Tally
        - date: ISO 8601 date string (YYYY-MM-DD)
        - voucher_type: Sales, Purchase, Receipt, Payment, Journal, etc.
        - voucher_number: User-facing voucher number
        - party: Customer/supplier name (may be Unicode)
        - narration: Voucher notes
        - amount: Total amount as string
    """
    vouchers = []

    try:
        # Tally JSON response has a "data" key with list of objects
        data = response_json.get("data", [])
        if not isinstance(data, list):
            logger.error("Invalid Tally response format: data is not a list")
            return []

        for item in data:
            try:
                # Extract basic fields
                voucher = {
                    "id": item.get("id") or item.get("ID"),
                    "date": _parse_tally_date(item.get("date") or item.get("Date")),
                    "voucher_type": item.get("vouchertype") or item.get("VoucherType") or "",
                    "voucher_number": item.get("vouchernumber") or item.get("VoucherNumber") or "",
                    "party": item.get("party") or item.get("Party") or "",
                    "narration": item.get("narration") or item.get("Narration") or "",
                    "amount": item.get("amount") or item.get("Amount"),
                }
                vouchers.append(voucher)

            except Exception as e:
                logger.warning(f"Skipped malformed voucher: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to parse Tally JSON response: {e}")
        return []

    return vouchers


def _parse_int(value: Optional[str], default: int = None) -> Optional[int]:
    """Parse string to integer."""
    if value:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return default


def _parse_tally_date(date_str: str) -> Optional[str]:
    """
    Convert Tally date format (YYYYMMDD) to ISO 8601 (YYYY-MM-DD).

    Args:
        date_str: Date as 8-digit string (e.g., "20260601")

    Returns:
        ISO 8601 date string or None if invalid
    """
    if not date_str or len(date_str) != 8:
        return None
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:])

        # Validate date components
        if not (1 <= month <= 12):
            return None
        if not (1 <= day <= 31):
            return None

        # Create date object to validate actual date (e.g., reject Feb 32)
        from datetime import date as date_class
        date_class(year, month, day)

        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    except (ValueError, TypeError):
        return None




def parse_ledgers(response_json: Dict[str, Any]) -> List[Dict]:
    """
    Parse Tally ledger (account) master data from JSON response.

    Args:
        response_json: JSON response from Tally API

    Returns:
        List of ledger dicts with keys:
        - name: Account name (may be Unicode)
        - parent: Parent ledger
        - opening_balance: Opening balance amount
        - closing_balance: Closing balance amount
    """
    ledgers = []

    try:
        data = response_json.get("data", [])
        if not isinstance(data, list):
            logger.error("Invalid Tally response format: data is not a list")
            return []

        for item in data:
            try:
                ledger = {
                    "name": item.get("Name") or item.get("name") or "",
                    "parent": item.get("Parent") or item.get("parent") or "",
                    "opening_balance": item.get("Opening Balance") or item.get("opening_balance"),
                    "closing_balance": item.get("Closing Balance") or item.get("closing_balance"),
                }
                if ledger["name"]:  # Only add if name exists
                    ledgers.append(ledger)

            except Exception as e:
                logger.warning(f"Skipped malformed ledger: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to parse ledger JSON response: {e}")
        return []

    return ledgers
