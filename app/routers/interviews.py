from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Interview, JobApplication, User
from app.schemas.schemas import InterviewCreate, InterviewUpdate, InterviewResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/applications/{application_id}/interviews", tags=["Interviews"])


def get_application_or_404(application_id: int, user_id: int, db: Session) -> JobApplication:
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == user_id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    application_id: int,
    payload: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_application_or_404(application_id, current_user.id, db)
    interview = Interview(**payload.model_dump(), application_id=application_id)
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/", response_model=list[InterviewResponse])
def list_interviews(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_application_or_404(application_id, current_user.id, db)
    return db.query(Interview).filter(Interview.application_id == application_id).all()


@router.patch("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    application_id: int,
    interview_id: int,
    payload: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_application_or_404(application_id, current_user.id, db)
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.application_id == application_id,
    ).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    application_id: int,
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_application_or_404(application_id, current_user.id, db)
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.application_id == application_id,
    ).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    db.delete(interview)
    db.commit()
