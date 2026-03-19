from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)


async def send_follow_up_reminder(to_email: str, user_name: str, company: str, position: str):
    """Send a follow-up reminder email for a job application."""
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>📋 Follow-Up Reminder</h2>
        <p>Hi <strong>{user_name}</strong>,</p>
        <p>This is a reminder to follow up on your application for:</p>
        <ul>
            <li><strong>Position:</strong> {position}</li>
            <li><strong>Company:</strong> {company}</li>
        </ul>
        <p>Don't forget to reach out to the hiring team if you haven't heard back yet!</p>
        <br>
        <p>Good luck! 🚀</p>
        <p><em>— Job Application Tracker</em></p>
    </body>
    </html>
    """
    message = MessageSchema(
        subject=f"Follow-Up Reminder: {position} at {company}",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_interview_reminder(to_email: str, user_name: str, company: str, position: str, interview_type: str, scheduled_at: str):
    """Send an interview reminder email."""
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>🗓️ Interview Reminder</h2>
        <p>Hi <strong>{user_name}</strong>,</p>
        <p>You have an upcoming interview scheduled:</p>
        <ul>
            <li><strong>Position:</strong> {position}</li>
            <li><strong>Company:</strong> {company}</li>
            <li><strong>Type:</strong> {interview_type}</li>
            <li><strong>Scheduled At:</strong> {scheduled_at}</li>
        </ul>
        <p>Prepare well and good luck! 💪</p>
        <br>
        <p><em>— Job Application Tracker</em></p>
    </body>
    </html>
    """
    message = MessageSchema(
        subject=f"Interview Reminder: {interview_type} for {position} at {company}",
        recipients=[to_email],
        body=body,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
