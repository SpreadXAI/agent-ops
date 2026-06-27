"""Seed mock marketplace accounts and sample execution logs."""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func

from app.config import get_settings
from app.database import SessionLocal, ensure_schema, engine
from app.models import (
    AccountStatus,
    AccountTier,
    Base,
    ExecutionLog,
    SocialAccount,
    TaskStatus,
)

TIER_PRICES = {
    AccountTier.basic: 9.9,
    AccountTier.standard: 29.9,
    AccountTier.premium: 99.9,
}

BIOS = [
    "Tech enthusiast | AI & automation",
    "Digital marketer | Growth hacker",
    "Crypto curious | Web3 explorer",
    "Content creator | Lifestyle blogger",
    "Startup founder | Product thinker",
    "Fitness coach | Morning runner",
    "Photography lover | Travel addict",
    "Indie hacker | Building in public",
]

FIRST = ["alex", "sam", "jordan", "taylor", "casey", "riley", "morgan", "jamie", "avery", "quinn"]
LAST = ["chen", "wang", "kim", "patel", "garcia", "lee", "brown", "martin", "singh", "nguyen"]


def seed_accounts(count: int = 200) -> None:
    settings = get_settings()
    ensure_schema()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(func.count(SocialAccount.id)).scalar() or 0
        if existing >= count:
            print(f"Skip seed: already have {existing} accounts")
            return

        to_create = count - existing
        tiers = list(AccountTier)
        for i in range(to_create):
            tier = random.choice(tiers)
            first = random.choice(FIRST)
            last = random.choice(LAST)
            num = existing + i + 1
            handle = f"{first}_{last}_{num}"
            display = f"{first.title()} {last.title()}"
            account = SocialAccount(
                platform="twitter",
                handle=handle,
                display_name=display,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={handle}",
                bio=random.choice(BIOS),
                profile_url=f"https://x.com/{handle}",
                tier=tier,
                price=TIER_PRICES[tier],
                followers=random.randint(120, 50000),
                status=AccountStatus.available,
            )
            db.add(account)
        db.commit()
        print(f"Seeded {to_create} accounts (total target {count})")
    finally:
        db.close()


def seed_demo_logs_for_user_accounts() -> None:
    db = SessionLocal()
    try:
        owned = db.query(SocialAccount).filter(SocialAccount.owner_user_id.isnot(None)).limit(5).all()
        if not owned:
            return
        steps = [
            ("login", "账号登录成功", TaskStatus.completed),
            ("browse", "浏览目标主页", TaskStatus.completed),
            ("action", "执行互动操作", TaskStatus.completed),
            ("report", "生成执行报告", TaskStatus.completed),
        ]
        for account in owned:
            if db.query(ExecutionLog).filter(ExecutionLog.account_id == account.id).count() > 0:
                continue
            for step, msg, st in steps:
                db.add(
                    ExecutionLog(
                        account_id=account.id,
                        user_id=account.owner_user_id,
                        step=step,
                        message=msg,
                        screenshot_url=None,
                        status=st,
                    )
                )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed_accounts(n)
    seed_demo_logs_for_user_accounts()
