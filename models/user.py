from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Role(str, Enum):
    user = "user"
    admin = "admin"


class User(Document):
    first_name: str
    last_name: str
    army_number: str
    role: Role = Role.user
    allowed_dbs: List[str] = []
    generated_password_hash: Optional[str] = None
    password_hash: Optional[str] = None
    must_change_password: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Settings:
    name = "users"
    indexes = ["army_number"]