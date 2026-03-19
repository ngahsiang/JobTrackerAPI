from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.models import JobApplication, Interview, User
from app.services.email_service import send_follow_up_reminder, send_interview_reminder

scheduler = AsyncIOScheduler()


async def check_follow_up_reminders():
    """Check and send follow-up reminders for applications due today."""
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        applications = (
            db.query(JobApplication)
            .filter(
                JobApplication.follow_up_date >= now,
                JobApplication.follow_up_date <= tomorrow,
            )
            .all()
        )
        for app in applications:
            user: User = db.query(User).filter(User.id == app.user_id).first()
            if user and user.email_reminders:
                await send_follow_up_reminder(
                    to_email=user.email,
                    user_name=user.name,
                    company=app.company,
                    position=app.position,
                )
    finally:
        db.close()


async def check_interview_reminders():
    """Check and send reminders for interviews scheduled in the next 24 hours."""
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        in_24h = now + timedelta(hours=24)
        interviews = (
            db.query(Interview)
            .filter(
                Interview.scheduled_at >= now,
                Interview.scheduled_at <= in_24h,
                Interview.completed == False,
            )
            .all()
        )
        for interview in interviews:
            app: JobApplication = db.query(JobApplication).filter(
                JobApplication.id == interview.application_id
            ).first()
            if app:
                user: User = db.query(User).filter(User.id == app.user_id).first()
                if user and user.email_reminders:
                    await send_interview_reminder(
                        to_email=user.email,
                        user_name=user.name,
                        company=app.company,
                        position=app.position,
                        interview_type=interview.interview_type,
                        scheduled_at=interview.scheduled_at.strftime("%Y-%m-%d %H:%M UTC"),
                    )
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(check_follow_up_reminders, "interval", hours=12, id="follow_up_reminders")
    scheduler.add_job(check_interview_reminders, "interval", hours=6, id="interview_reminders")
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
