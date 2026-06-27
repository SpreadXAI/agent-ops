"""Provision and sync per-account Tactile agents."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AccountPrompt, SocialAccount
from app.tactile.client import TactileClient, TactileError


def build_agent_instructions(
    account: SocialAccount,
    *,
    persona: str = "",
    prompt_text: str = "",
) -> str:
    parts = [
        f"You are the dedicated Twitter executor for @{account.handle} ({account.display_name}).",
    ]
    if account.bio:
        parts.append(f"Account bio: {account.bio}")
    if persona.strip():
        parts.append(f"Persona:\n{persona.strip()}")
    if prompt_text.strip():
        parts.append(f"Default task guidance:\n{prompt_text.strip()}")
    parts.append(
        "Runtime env provides TWITTER_COOKIE, SPIDER_RADAR_ACCOUNT_ID, and SPIDER_RADAR_HANDLE. "
        "Follow installed skills for Twitter operations and report results via Spider Radar APIs when needed."
    )
    return "\n\n".join(parts)


def _prompt_for_account(db: Session, account: SocialAccount) -> tuple[str, str]:
    prompt = db.query(AccountPrompt).filter(AccountPrompt.account_id == account.id).first()
    if prompt is None:
        return "", ""
    return prompt.persona or "", prompt.prompt_text or ""


def _template_skill_bindings(settings: Settings, client: TactileClient) -> list[dict[str, int]]:
    if settings.tactile_template_agent_id:
        detail = client.get_agent(settings.tactile_template_agent_id)
        bindings = detail.get("bindings") or {}
        skills = bindings.get("skills") or []
        return [{"skill_id": int(s["skill_id"]), "version_id": int(s["version_id"])} for s in skills]
    if settings.tactile_template_skill_id and settings.tactile_template_skill_version_id:
        return [
            {
                "skill_id": settings.tactile_template_skill_id,
                "version_id": settings.tactile_template_skill_version_id,
            }
        ]
    return []


def _default_env_vars(settings: Settings) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if settings.spider_radar_public_api_base:
        items.append(
            {
                "env_key": "SPIDER_RADAR_API_BASE",
                "env_value": settings.spider_radar_public_api_base.rstrip("/"),
                "is_secret": False,
                "enabled": True,
            }
        )
    return items


def ensure_account_agent(db: Session, settings: Settings, account: SocialAccount) -> int:
    """Create a Tactile agent for this account if missing; return agent id."""
    if account.tactile_agent_id:
        return account.tactile_agent_id
    if not settings.tactile_workspace_id:
        raise ValueError("Tactile workspace not configured")

    persona, prompt_text = _prompt_for_account(db, account)
    client = TactileClient(settings)
    skills = _template_skill_bindings(settings, client)
    bindings = {"skills": skills} if skills else None
    env_vars = _default_env_vars(settings)

    body: dict[str, object] = {
        "workspace_id": settings.tactile_workspace_id,
        "name": f"Spider Radar @{account.handle}",
        "description": f"Per-account Twitter executor for @{account.handle}",
        "instructions": build_agent_instructions(account, persona=persona, prompt_text=prompt_text),
        "runtime_type": settings.tactile_default_runtime_type,
    }
    if bindings:
        body["bindings"] = bindings
    if env_vars:
        body["env_vars"] = env_vars

    created = client.create_agent(body)
    agent_id = int(created["id"])
    account.tactile_agent_id = agent_id
    db.commit()
    db.refresh(account)
    return agent_id


def sync_account_agent_instructions(
    settings: Settings,
    account: SocialAccount,
    *,
    persona: str,
    prompt_text: str,
) -> None:
    if not account.tactile_agent_id:
        return
    client = TactileClient(settings)
    instructions = build_agent_instructions(account, persona=persona, prompt_text=prompt_text)
    try:
        client.update_agent(
            account.tactile_agent_id,
            {"instructions": instructions},
        )
    except TactileError:
        # Agent may have been removed in Tactile; caller can re-provision on next run.
        raise
