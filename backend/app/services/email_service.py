import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


def _send_sync(to_email: str, subject: str, html_body: str) -> None:
    if not settings.SMTP_HOST:
        return
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], message.as_string())


async def send_password_reset_email(to_email: str, token: str) -> None:
    subject = f"{settings.PROJECT_NAME} - Password Reset"
    body = f"<p>Use this token to reset your password:</p><p><code>{token}</code></p>"
    await asyncio.get_running_loop().run_in_executor(None, _send_sync, to_email, subject, body)


async def send_notification_email(to_email: str, subject: str, body: str) -> None:
    await asyncio.get_running_loop().run_in_executor(None, _send_sync, to_email, subject, body)
