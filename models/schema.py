from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class Role(str, Enum):
    user = "user"
    admin = "admin"

class LoginSchema(BaseModel):
    army_number: str
    password: str

class CreateUserSchema(BaseModel):
    first_name: str
    last_name: str
    army_number: str
    role: Role = Role.user
    allowed_dbs: List[str] = []
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CreateAdminSchema(BaseModel):
    first_name: str
    last_name: str
    army_number: str
    role: Role = Role.user
    allowed_dbs: List[str] = []
    access_all_db: Optional[bool] = False
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str
