import base64
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional

from src.models.user import User
from src.config import settings

logger = logging.getLogger("jobexa")

def send_application_email_via_gmail(
    user: User,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_paths: Optional[List[str]] = None
) -> dict:
    """
    Sends an email using the user's connected Gmail OAuth credentials.
    Falls back to SMTP or simulation mode if OAuth credentials are not linked.
    Returns dict containing status and threadId (if available).
    """
    if user.gmail_access_token and user.gmail_refresh_token:
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(
                token=user.gmail_access_token,
                refresh_token=user.gmail_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )

            service = build('gmail', 'v1', credentials=creds)

            mime_msg = MIMEMultipart()
            mime_msg['to'] = recipient_email
            mime_msg['subject'] = subject
            mime_msg.attach(MIMEText(body_text, 'plain'))

            if attachment_paths:
                for path in attachment_paths:
                    if path and os.path.exists(path):
                        filename = os.path.basename(path)
                        with open(path, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=filename)
                            part['Content-Disposition'] = f'attachment; filename="{filename}"'
                            mime_msg.attach(part)

            raw_bytes = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('utf-8')
            sent_message = service.users().messages().send(userId='me', body={'raw': raw_bytes}).execute()
            
            logger.info(f"Successfully sent email via Gmail API to {recipient_email}. ThreadId: {sent_message.get('threadId')}")
            return {
                "status": "Sent",
                "thread_id": sent_message.get("threadId"),
                "message_id": sent_message.get("id")
            }
        except Exception as e:
            logger.error(f"Gmail API dispatch failed: {e}. Attempting fallback.")

    # Fallback to SMTP or Simulation
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        try:
            import smtplib
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body_text, 'plain'))

            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"Sent email via SMTP to {recipient_email}")
            return {"status": "Sent", "thread_id": None}
        except Exception as e:
            logger.error(f"SMTP dispatch failed: {e}")

    # Simulation mode for local dev/test
    logger.info(f"[SIMULATION] Email sent to {recipient_email} | Subject: {subject}")
    return {"status": "Sent (Simulated)", "thread_id": f"sim_thread_{user.id}"}
