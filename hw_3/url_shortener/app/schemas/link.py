from pydantic import BaseModel, HttpUrl, constr
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: HttpUrl
    alias: Optional[constr(min_length=1, max_length=50)] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    alias: Optional[constr(min_length=1, max_length=50)] = None
    expires_at: Optional[datetime] = None

class LinkRead(BaseModel):
    short_code: str
    original_url: HttpUrl
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    last_click_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        orm_mode = True
