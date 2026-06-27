from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    AccountPrompt,
    AccountStatus,
    BatchTask,
    BatchTaskMember,
    ExecutionLog,
    ScheduledTask,
    SocialAccount,
    TaskStatus,
    User,
)
from app.schemas import (
    BatchTaskCreate,
    BatchTaskOut,
    DashboardStats,
    ExecutionLogOut,
    PromptOut,
    PromptUpdate,
    ScheduleCreate,
    ScheduleOut,
    SocialAccountOut,
)

router = APIRouter(tags=["app"])

MAX_SCHEDULES_PER_ACCOUNT = 3


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DashboardStats:
    owned = db.query(SocialAccount).filter(SocialAccount.owner_user_id == current_user.id).count()
    market = db.query(SocialAccount).filter(SocialAccount.status == AccountStatus.available).count()
    schedules = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.user_id == current_user.id, ScheduledTask.enabled.is_(True))
        .count()
    )
    batches = db.query(BatchTask).filter(BatchTask.user_id == current_user.id).count()
    logs = (
        db.query(ExecutionLog)
        .join(SocialAccount)
        .filter(SocialAccount.owner_user_id == current_user.id)
        .count()
    )
    return DashboardStats(
        total_accounts_owned=owned,
        available_market=market,
        active_schedules=schedules,
        batch_tasks=batches,
        recent_logs=logs,
    )


@router.get("/market/accounts", response_model=list[SocialAccountOut])
def list_market_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
) -> list[SocialAccountOut]:
    del current_user
    rows = (
        db.query(SocialAccount)
        .filter(SocialAccount.status == AccountStatus.available, SocialAccount.owner_user_id.is_(None))
        .order_by(SocialAccount.id)
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )
    return [SocialAccountOut.model_validate(r) for r in rows]


@router.get("/my/accounts", response_model=list[SocialAccountOut])
def list_my_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SocialAccountOut]:
    rows = (
        db.query(SocialAccount)
        .filter(SocialAccount.owner_user_id == current_user.id)
        .order_by(SocialAccount.id)
        .all()
    )
    return [SocialAccountOut.model_validate(r) for r in rows]


@router.post("/my/accounts/{account_id}/purchase", response_model=SocialAccountOut)
def purchase_account(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SocialAccountOut:
    account = db.get(SocialAccount, account_id)
    if account is None or account.status != AccountStatus.available or account.owner_user_id is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not available")
    account.owner_user_id = current_user.id
    account.status = AccountStatus.sold
    db.commit()
    db.refresh(account)
    return SocialAccountOut.model_validate(account)


@router.get("/my/accounts/{account_id}", response_model=SocialAccountOut)
def get_my_account(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SocialAccountOut:
    account = _owned_account(db, current_user, account_id)
    return SocialAccountOut.model_validate(account)


@router.get("/my/accounts/{account_id}/prompt", response_model=PromptOut | None)
def get_prompt(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PromptOut | None:
    _owned_account(db, current_user, account_id)
    prompt = (
        db.query(AccountPrompt)
        .filter(AccountPrompt.account_id == account_id, AccountPrompt.user_id == current_user.id)
        .first()
    )
    return PromptOut.model_validate(prompt) if prompt else None


@router.put("/my/accounts/{account_id}/prompt", response_model=PromptOut)
def upsert_prompt(
    account_id: int,
    payload: PromptUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PromptOut:
    _owned_account(db, current_user, account_id)
    prompt = (
        db.query(AccountPrompt)
        .filter(AccountPrompt.account_id == account_id, AccountPrompt.user_id == current_user.id)
        .first()
    )
    if prompt is None:
        prompt = AccountPrompt(account_id=account_id, user_id=current_user.id)
        db.add(prompt)
    prompt.persona = payload.persona
    prompt.prompt_text = payload.prompt_text
    db.commit()
    db.refresh(prompt)
    return PromptOut.model_validate(prompt)


@router.get("/my/accounts/{account_id}/schedules", response_model=list[ScheduleOut])
def list_schedules(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ScheduleOut]:
    _owned_account(db, current_user, account_id)
    rows = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.account_id == account_id, ScheduledTask.user_id == current_user.id)
        .order_by(ScheduledTask.start_time)
        .all()
    )
    return [ScheduleOut.model_validate(r) for r in rows]


@router.post("/my/accounts/{account_id}/schedules", response_model=ScheduleOut)
def create_schedule(
    account_id: int,
    payload: ScheduleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ScheduleOut:
    _owned_account(db, current_user, account_id)
    count = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.account_id == account_id, ScheduledTask.user_id == current_user.id)
        .count()
    )
    if count >= MAX_SCHEDULES_PER_ACCOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_SCHEDULES_PER_ACCOUNT} schedules per account",
        )
    task = ScheduledTask(
        account_id=account_id,
        user_id=current_user.id,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        enabled=payload.enabled,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ScheduleOut.model_validate(task)


@router.delete("/my/accounts/{account_id}/schedules/{schedule_id}")
def delete_schedule(
    account_id: int,
    schedule_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    _owned_account(db, current_user, account_id)
    task = (
        db.query(ScheduledTask)
        .filter(
            ScheduledTask.id == schedule_id,
            ScheduledTask.account_id == account_id,
            ScheduledTask.user_id == current_user.id,
        )
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.get("/batch-tasks", response_model=list[BatchTaskOut])
def list_batch_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[BatchTaskOut]:
    rows = (
        db.query(BatchTask)
        .options(joinedload(BatchTask.members))
        .filter(BatchTask.user_id == current_user.id)
        .order_by(BatchTask.id.desc())
        .all()
    )
    return [_batch_out(r) for r in rows]


@router.post("/batch-tasks", response_model=BatchTaskOut)
def create_batch_task(
    payload: BatchTaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BatchTaskOut:
    for aid in payload.account_ids:
        _owned_account(db, current_user, aid)

    batch = BatchTask(
        user_id=current_user.id,
        name=payload.name,
        prompt_text=payload.prompt_text,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        enabled=payload.enabled,
    )
    db.add(batch)
    db.flush()
    for aid in payload.account_ids:
        db.add(BatchTaskMember(batch_task_id=batch.id, account_id=aid))
    db.commit()
    db.refresh(batch)
    batch = (
        db.query(BatchTask)
        .options(joinedload(BatchTask.members))
        .filter(BatchTask.id == batch.id)
        .one()
    )
    return _batch_out(batch)


@router.get("/execution-logs", response_model=list[ExecutionLogOut])
def list_execution_logs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
) -> list[ExecutionLogOut]:
    rows = (
        db.query(ExecutionLog, SocialAccount.handle)
        .join(SocialAccount, ExecutionLog.account_id == SocialAccount.id)
        .filter(SocialAccount.owner_user_id == current_user.id)
        .order_by(ExecutionLog.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    result = []
    for log, handle in rows:
        item = ExecutionLogOut.model_validate(log)
        item.account_handle = handle
        result.append(item)
    return result


def _owned_account(db: Session, user: User, account_id: int) -> SocialAccount:
    account = db.get(SocialAccount, account_id)
    if account is None or account.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


def _batch_out(batch: BatchTask) -> BatchTaskOut:
    return BatchTaskOut(
        id=batch.id,
        name=batch.name,
        prompt_text=batch.prompt_text,
        start_time=batch.start_time,
        duration_minutes=batch.duration_minutes,
        enabled=batch.enabled,
        created_at=batch.created_at,
        account_ids=[m.account_id for m in batch.members],
    )
