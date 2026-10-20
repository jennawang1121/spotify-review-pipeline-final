"""Persist reservations before dispatch. No network execution in this milestone."""
import sqlite3
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from .costing import number


def nanos(value):
    return int((number(value) * 1000000000).to_integral_value(rounding=ROUND_CEILING))


class BudgetLedger:
    def __init__(self, path, limit_usd):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None)
        self.limit = nanos(limit_usd)
        self.db.execute("""CREATE TABLE IF NOT EXISTS reservations (
            call_id TEXT PRIMARY KEY, reserved_nanos INTEGER NOT NULL,
            charged_nanos INTEGER, outcome TEXT NOT NULL)""")

    def reserve(self, call_id, worst_case_usd):
        amount = nanos(worst_case_usd)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            used = self.db.execute("SELECT COALESCE(SUM(COALESCE(charged_nanos,reserved_nanos)),0) FROM reservations").fetchone()[0]
            if used + amount > self.limit:
                raise ValueError("Budget cap: spent + unresolved reservations + next call exceeds limit.")
            self.db.execute("INSERT INTO reservations VALUES (?,?,NULL,'reserved')", (call_id, amount))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def settle(self, call_id, actual_usd, outcome):
        if outcome not in ("succeeded", "failed"):
            raise ValueError("Settle with succeeded or failed; unresolved calls retain their reservation.")
        # A late bill above reservation must remain visible, even when it exceeds budget.
        updated = self.db.execute("UPDATE reservations SET charged_nanos=?,outcome=? WHERE call_id=? AND charged_nanos IS NULL",
                                  (nanos(actual_usd), outcome, call_id))
        if updated.rowcount != 1:
            raise ValueError("Unknown or already settled attempted call ID.")

    def snapshot(self):
        spent, reserved, unresolved = self.db.execute("""SELECT
            COALESCE(SUM(COALESCE(charged_nanos,0)),0),
            COALESCE(SUM(CASE WHEN charged_nanos IS NULL THEN reserved_nanos ELSE 0 END),0),
            SUM(CASE WHEN charged_nanos IS NULL THEN 1 ELSE 0 END) FROM reservations""").fetchone()
        return {"spent_usd": str(Decimal(spent) / 1000000000),
                "reserved_usd": str(Decimal(reserved) / 1000000000),
                "unresolved_attempts": unresolved or 0, "over_limit": spent + reserved > self.limit}

    def close(self):
        self.db.close()
