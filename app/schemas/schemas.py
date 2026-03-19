from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import ApplicationStatus


# ─── Auth Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    email_reminders: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email_reminders: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# ─── Interview Schemas ─────────────────────────────────────────────────────────

class InterviewCreate(BaseModel):
    interview_type: str = Field(..., min_length=2, max_length=100)
    scheduled_at: datetime
    notes: Optional[str] = None

class InterviewUpdate(BaseModel):
    interview_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None

class InterviewResponse(BaseModel):
    id: int
    application_id: int
    interview_type: str
    scheduled_at: datetime
    notes: Optional[str]
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Job Application Schemas ───────────────────────────────────────────────────

class JobApplicationCreate(BaseModel):
    company: str = Field(..., min_length=1, max_length=150)
    position: str = Field(..., min_length=1, max_length=150)
    location: Optional[str] = None
    job_url: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.APPLIED
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None

class JobApplicationUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1, max_length=150)
    position: Optional[str] = Field(None, min_length=1, max_length=150)
    location: Optional[str] = None
    job_url: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None

class JobApplicationResponse(BaseModel):
    id: int
    company: str
    position: str
    location: Optional[str]
    job_url: Optional[str]
    status: ApplicationStatus
    salary_min: Optional[int]
    salary_max: Optional[int]
    notes: Optional[str]
    applied_date: Optional[datetime]
    follow_up_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    interviews: List[InterviewResponse] = []

    class Config:
        from_attributes = True

class PaginatedApplications(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[JobApplicationResponse]
