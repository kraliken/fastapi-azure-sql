from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class Role(str, Enum):
    admin = "admin"
    member = "member"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=6, max_length=50)
    role: Role = Field(default=Role.member)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str
    role: Role
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None


class TokenWithUser(Token):
    user: UserRead
