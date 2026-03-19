from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import JobApplication, ApplicationStatus, User
from app.schemas.schemas import (
    JobApplicationCreate,
    JobApplicationUpdate,
    JobApplicationResponse,
    PaginatedApplications,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/applications", tags=["Job Applications"])


@router.post("/", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = JobApplication(**payload.model_dump(), user_id=current_user.id)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=PaginatedApplications)
def list_applications(
    status: Optional[ApplicationStatus] = None,
    company: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(JobApplication).filter(JobApplication.user_id == current_user.id)

    if status:
        query = query.filter(JobApplication.status == status)
    if company:
        query = query.filter(JobApplication.company.ilike(f"%{company}%"))

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedApplications(total=total, page=page, page_size=page_size, results=results)


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a summary count by application status."""
    applications = db.query(JobApplication).filter(JobApplication.user_id == current_user.id).all()
    stats = {status.value: 0 for status in ApplicationStatus}
    for app in applications:
        stats[app.status.value] += 1
    stats["total"] = len(applications)
    return stats


@router.get("/{application_id}", response_model=JobApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=JobApplicationResponse)
def update_application(
    application_id: int,
    payload: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app, field, value)

    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
