from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    name: str
    avatar_url: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_demo: bool
    created_at: datetime
    updated_at: datetime
