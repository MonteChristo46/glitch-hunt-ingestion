from uuid import UUID
from pydantic import BaseModel

class AccountBase(BaseModel):
    name: str
    is_active: bool = True

class AccountCreate(AccountBase):
    pass

class AccountRead(AccountBase):
    id: UUID
