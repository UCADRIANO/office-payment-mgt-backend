from pydantic import Field, BaseModel, model_validator
from datetime import datetime
from enum import Enum
from typing import Optional, List
from models.schema import BaseMongoModel

class BankInfo(BaseModel):
    name: str
    sort_code: str

class CreateDBSchema(BaseMongoModel):
    name: str
    short_code: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Personnel(BaseMongoModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    army_number: str
    phone_number: str
    rank: str
    bank: BankInfo
    acct_number: str
    sub_sector: str
    location: Optional[str] = None
    remark: Optional[str] = None
    db_id: str 
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PersonnelBulkUpload(BaseModel):
    personnel: List[Personnel]

    @model_validator(mode="after")
    def ensure_same_db_id(self):
        if not self.personnel:
            raise ValueError("Empty personnel list")

        db_ids = {p.db_id for p in self.personnel}
        if len(db_ids) != 1:
            raise ValueError("All personnel must have the same db_id")

        return self
