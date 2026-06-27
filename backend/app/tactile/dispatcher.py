"""Dispatch Spider Radar account runs to Tactile."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AccountPrompt, AccountStatus, ExecutionLog, SocialAccount, TaskStatus, User
from app.tactile.agent_provision import ensure_account_agent
from app.tactile.client import TactileClient, TactileError


def build_dispatch_env(account: SocialAccount) -> dict[str, str]:
    """Task-level runtime env passed via Tactile work_item.dispatch_env_json."""
    return {
        "TWITTER_COOKIE": account.session_cookie or "",
        "SPIDER_RADAR_ACCOUNT_ID": str(account.id),
        "SPIDER_RADAR_HANDLE": account.handle,
    }


def build_work_content(*, prompt_text: str) -> str:
    body = prompt_text.strip() or "Browse Twitter timeline and report activity."
    return body


def dispatch_account_run(
    db: Session,
    settings: Settings,
    account: SocialAccount,
    user: User,
    *,
    prompt_override: str | None = None,
) -> ExecutionLog:
    if not account.session_cookie:
        raise ValueError("Session cookie is required before run")
    if not settings.tactile_workspace_id:
        raise ValueError("Tactile workspace not configured")

    prompt = db.query(AccountPrompt).filter(AccountPrompt.account_id == account.id).first()
    prompt_text = prompt_override if prompt_override is not None else (prompt.prompt_text if prompt else "")

    try:
        agent_id = ensure_account_agent(db, settings, account)
    except TactileError as exc:
        log = ExecutionLog(
            account_id=account.id,
            user_id=user.id,
            step="provision",
            message=f"Tactile agent provision failed: {exc.detail}",
            status=TaskStatus.failed,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        raise

    content = build_work_content(prompt_text=prompt_text)
    dispatch_env_json = json.dumps(build_dispatch_env(account), ensure_ascii=False)

    client = TactileClient(settings)
    name = f"Spider Radar @{account.handle}"
    try:
        work = client.create_work(
            workspace_id=settings.tactile_workspace_id,
            agent_id=agent_id,
            name=name,
            content=content,
            dispatch_env_json=dispatch_env_json,
        )
    except TactileError as exc:
        log = ExecutionLog(
            account_id=account.id,
            user_id=user.id,
            step="dispatch",
            message=f"Tactile dispatch failed: {exc.detail}",
            status=TaskStatus.failed,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        raise

    work_id = work.get("id")
    session_id = work.get("session_id")
    account.tactile_last_work_id = work_id
    account.status = AccountStatus.running

    log = ExecutionLog(
        account_id=account.id,
        user_id=user.id,
        step="dispatch",
        message=f"Dispatched to Tactile agent_id={agent_id} work_id={work_id} session_id={session_id}",
        status=TaskStatus.running,
        tactile_work_id=work_id,
        tactile_session_id=session_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
