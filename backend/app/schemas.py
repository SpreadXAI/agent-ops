from datetime import datetime, time

from pydantic import BaseModel, Field

from app.models import AccountStatus, AccountTier, TaskStatus


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=255)
    display_name: str = Field(min_length=1, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SocialAccountOut(BaseModel):
    id: int
    platform: str
    handle: str
    display_name: str
    avatar_url: str
    bio: str
    profile_url: str
    tier: AccountTier
    price: float
    followers: int
    status: AccountStatus
    owner_user_id: int | None

    model_config = {"from_attributes": True}


class PromptUpdate(BaseModel):
    persona: str = ""
    prompt_text: str = ""


class PromptOut(BaseModel):
    id: int
    account_id: int
    persona: str
    prompt_text: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    start_time: time
    duration_minutes: int = Field(default=30, ge=1, le=60)
    enabled: bool = True


class ScheduleOut(BaseModel):
    id: int
    account_id: int
    start_time: time
    duration_minutes: int
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchTaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    prompt_text: str = ""
    start_time: time
    duration_minutes: int = Field(default=30, ge=1, le=60)
    account_ids: list[int] = Field(min_length=1)
    enabled: bool = True


class BatchTaskOut(BaseModel):
    id: int
    name: str
    prompt_text: str
    start_time: time
    duration_minutes: int
    enabled: bool
    created_at: datetime
    account_ids: list[int]

    model_config = {"from_attributes": True}


class ExecutionLogOut(BaseModel):
    id: int
    account_id: int
    step: str
    message: str
    screenshot_url: str | None
    status: TaskStatus
    created_at: datetime
    account_handle: str | None = None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_accounts_owned: int
    available_market: int
    active_schedules: int
    batch_tasks: int
    recent_logs: int
