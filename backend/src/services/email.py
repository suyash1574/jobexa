import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging
from typing import List
from src.config import settings

logger = logging.getLogger("jobexa.services.email")

class EmailService:
    @staticmethod
    def send_application_email(
        to_email: str, 
        subject: str, 
        body: str, 
        attachment_paths: List[str] = []
    ) -> bool:
        """
        Sends an email with attachments. Falls back from Gmail API to SMTP.
        Raises exception if delivery fails.
        """
        # If no recruiter email, we cannot send
        if not to_email:
            raise ValueError("No recruiter email address provided.")

        logger.info(f"Preparing to send job application email to {to_email}")

        # Check SMTP settings
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials are not configured. Triggering delivery failure.")
            raise smtplib.SMTPAuthenticationError(535, b"SMTP credentials missing in configuration settings.")

        # Create MIME message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Attach PDFs/documents
        for filepath in attachment_paths:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                try:
                    with open(filepath, "rb") as f:
                        part = MIMEApplication(f.read(), Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)
                except Exception as attach_err:
                    logger.error(f"Failed to attach file {filepath}: {str(attach_err)}")
                    raise attach_err

        # Send via SMTP
        try:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
                return True
        except Exception as e:
            logger.error(f"SMTP delivery failed: {str(e)}")
            raise e
