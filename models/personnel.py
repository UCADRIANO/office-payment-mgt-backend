from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum
from typing import Optional

class DB(Document):
    name: str
    short_code: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Personnel(Document):
    first_name: str
    last_name: str
    middle_name: str
    army_number: str
    phone_number: str
    rank: str
    bank: str
    acct_number: str
    sub_sector: str
    location: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

