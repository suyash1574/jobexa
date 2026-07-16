from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ResumeBase(BaseModel):
    filename: str
    file_url: str
    file_size: int
    role_tag: Optional[str] = None
    is_default: bool = False

class ResumeOut(ResumeBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CertificateBase(BaseModel):
    filename: str
    file_url: str
    file_size: int
    category: Optional[str] = None

class CertificateOut(CertificateBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
