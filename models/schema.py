from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any
from bson import ObjectId

class BaseMongoModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    @field_validator("id", mode="before")
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = {
        "populate_by_name": True
    }

class Role(str, Enum):
    user = "user"
    admin = "admin"

class LoginSchema(BaseModel):
    army_number: str
    password: str


class CreateUserSchema(BaseMongoModel):
    first_name: str
    last_name: str
    army_number: str
    role: Role = Role.user
    allowed_dbs: list[Any] = Field(default_factory=list) 
    password_hash: Optional[str] = None
    is_generated: Optional[bool] = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CreateAdminSchema(BaseMongoModel):
    first_name: str
    last_name: str
    army_number: str
    role: Role = Role.user
    allowed_dbs: list[str] = []
    access_all_db: Optional[bool] = False
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

class ResetPasswordSchema(BaseModel):
    user_id: str
    new_password: str