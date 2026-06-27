"""Provision Tactile agents for sold accounts missing tactile_agent_id."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import SessionLocal
from app.models import AccountStatus, SocialAccount
from app.tactile.agent_provision import ensure_account_agent
from app.tactile.client import TactileError


def backfill() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        rows = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.status != AccountStatus.available,
                SocialAccount.workspace_id.isnot(None),
                SocialAccount.tactile_agent_id.is_(None),
            )
            .order_by(SocialAccount.id)
            .all()
        )
        if not rows:
            print("No accounts need Tactile agent backfill")
            return
        for account in rows:
            try:
                agent_id = ensure_account_agent(db, settings, account)
                print(f"account {account.id} @{account.handle} -> tactile_agent_id={agent_id}")
            except (ValueError, TactileError) as exc:
                detail = exc.detail if isinstance(exc, TactileError) else str(exc)
                print(f"WARN account {account.id} @{account.handle}: {detail}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
