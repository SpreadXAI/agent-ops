"""Apply incremental schema changes for existing deployments."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.config import get_settings
from app.database import engine, ensure_schema


def migrate() -> None:
    ensure_schema()
    settings = get_settings()
    schema = settings.database_schema

    with engine.begin() as conn:
        def has_column(table: str, column: str) -> bool:
            row = conn.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table AND column_name = :column
                    """
                ),
                {"schema": schema, "table": table, "column": column},
            ).first()
            return row is not None

        def has_table(table: str) -> bool:
            row = conn.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = :schema AND table_name = :table
                    """
                ),
                {"schema": schema, "table": table},
            ).first()
            return row is not None

        if has_table("users"):
            if not has_column("users", "is_admin"):
                conn.execute(text(f'ALTER TABLE "{schema}".users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE'))
                print("Added users.is_admin")
            if not has_column("users", "active_workspace_id"):
                conn.execute(text(f'ALTER TABLE "{schema}".users ADD COLUMN active_workspace_id INTEGER'))
                print("Added users.active_workspace_id")

        if has_table("social_accounts") and not has_column("social_accounts", "workspace_id"):
            conn.execute(text(f'ALTER TABLE "{schema}".social_accounts ADD COLUMN workspace_id INTEGER'))
            print("Added social_accounts.workspace_id")

        if has_table("social_accounts"):
            if not has_column("social_accounts", "session_cookie"):
                conn.execute(text(f'ALTER TABLE "{schema}".social_accounts ADD COLUMN session_cookie TEXT'))
                print("Added social_accounts.session_cookie")
            if not has_column("social_accounts", "tactile_last_work_id"):
                conn.execute(text(f'ALTER TABLE "{schema}".social_accounts ADD COLUMN tactile_last_work_id INTEGER'))
                print("Added social_accounts.tactile_last_work_id")
            if not has_column("social_accounts", "tactile_agent_id"):
                conn.execute(text(f'ALTER TABLE "{schema}".social_accounts ADD COLUMN tactile_agent_id INTEGER'))
                print("Added social_accounts.tactile_agent_id")

        if has_table("execution_logs"):
            if not has_column("execution_logs", "tactile_work_id"):
                conn.execute(text(f'ALTER TABLE "{schema}".execution_logs ADD COLUMN tactile_work_id INTEGER'))
                print("Added execution_logs.tactile_work_id")
            if not has_column("execution_logs", "tactile_session_id"):
                conn.execute(text(f'ALTER TABLE "{schema}".execution_logs ADD COLUMN tactile_session_id VARCHAR(64)'))
                print("Added execution_logs.tactile_session_id")

        if has_table("batch_tasks") and not has_column("batch_tasks", "workspace_id"):
            conn.execute(text(f'ALTER TABLE "{schema}".batch_tasks ADD COLUMN workspace_id INTEGER'))
            print("Added batch_tasks.workspace_id")

        if has_table("account_prompts"):
            old_constraints = conn.execute(
                text(
                    f"""
                    SELECT conname FROM pg_constraint
                    WHERE conrelid = '{schema}.account_prompts'::regclass AND contype = 'u'
                    """
                )
            ).fetchall()
            for (name,) in old_constraints:
                if name != "uq_prompt_account":
                    conn.execute(text(f'ALTER TABLE "{schema}".account_prompts DROP CONSTRAINT IF EXISTS "{name}"'))
                    print(f"Dropped old constraint {name} on account_prompts")
            has_uq = conn.execute(
                text(
                    f"""
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid = '{schema}.account_prompts'::regclass AND conname = 'uq_prompt_account'
                    """
                )
            ).first()
            if not has_uq:
                conn.execute(
                    text(f'ALTER TABLE "{schema}".account_prompts ADD CONSTRAINT uq_prompt_account UNIQUE (account_id)')
                )
                print("Added uq_prompt_account on account_prompts")

    print("Schema migration complete")


if __name__ == "__main__":
    migrate()
