"""
Gmail Email Sender Module
Sends meeting summary PDFs via Gmail SMTP.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EmailConfig:
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    subject_template: str = "Meeting Summary - {date} - {platform}"


class GmailSender:
    """Sends emails with PDF attachments via Gmail SMTP."""

    def __init__(self, config: dict):
        email_config = config.get("email", {})
        
        # Get credentials from environment or config
        self.smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = email_config.get("smtp_port", 587)
        self.sender_email = os.getenv("GMAIL_ADDRESS", email_config.get("sender_email", ""))
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD", email_config.get("sender_password", ""))
        self.subject_template = email_config.get(
            "subject_template", 
            "Meeting Summary - {date} - {platform}"
        )
        
        if not self.sender_email or not self.sender_password:
            logger.warning("Gmail credentials not configured. Email sending will fail.")

    def _validate_credentials(self) -> bool:
        """Validate that email credentials are configured."""
        if not self.sender_email:
            logger.error("GMAIL_ADDRESS not configured")
            return False
        if not self.sender_password:
            logger.error("GMAIL_APP_PASSWORD not configured")
            return False
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_summary(
        self,
        recipient_email: str,
        pdf_path: Path,
        platform: str,
        meeting_date: Optional[datetime] = None,
        additional_message: Optional[str] = None
    ) -> bool:
        """Send meeting summary PDF via email."""
        
        if not self._validate_credentials():
            raise ValueError("Email credentials not configured")
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if meeting_date is None:
            meeting_date = datetime.now()
        
        logger.info(f"Sending email to {recipient_email}")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = self.subject_template.format(
                date=meeting_date.strftime("%Y-%m-%d"),
                platform=platform.replace('_', ' ').title()
            )
            
            # Email body
            body = self._create_email_body(platform, meeting_date, additional_message)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach PDF
            self._attach_pdf(msg, pdf_path)
            
            # Send email
            await self._send_email(msg, recipient_email)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _create_email_body(
        self, 
        platform: str, 
        meeting_date: datetime,
        additional_message: Optional[str] = None
    ) -> str:
        """Create HTML email body."""
        
        additional_section = ""
        if additional_message:
            additional_section = f"""
            <p style="margin-top: 15px; padding: 10px; background-color: #f0f4f8; border-radius: 5px;">
                {additional_message}
            </p>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2d3748;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f7fafc;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #718096;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">☀️ Sunny AI</h1>
                    <p style="margin: 5px 0 0 0;">Meeting Summary Report</p>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>
                        Your meeting summary is ready! Please find the detailed report attached 
                        to this email.
                    </p>
                    <p>
                        <strong>Meeting Details:</strong><br>
                        📅 Date: {meeting_date.strftime("%B %d, %Y at %I:%M %p")}<br>
                        💻 Platform: {platform.replace('_', ' ').title()}
                    </p>
                    {additional_section}
                    <p>
                        The attached PDF contains:
                    </p>
                    <ul>
                        <li>Executive Summary</li>
                        <li>Key Discussion Points</li>
                        <li>Decisions Made</li>
                        <li>Action Items</li>
                    </ul>
                    <p>
                        Thank you for using Sunny AI!
                    </p>
                </div>
                <div class="footer">
                    <p>
                        This email was automatically generated by Sunny AI – Autonomous Meeting Assistant.<br>
                        Please verify important details against the original meeting recording.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _attach_pdf(self, msg: MIMEMultipart, pdf_path: Path) -> None:
        """Attach PDF file to email."""
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{pdf_path.name}"'
        )
        msg.attach(part)

    async def _send_email(self, msg: MIMEMultipart, recipient: str) -> None:
        """Send email via SMTP."""
        import asyncio
        
        def _send():
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send)

    async def send_batch(
        self,
        recipients: List[str],
        pdf_path: Path,
        platform: str,
        meeting_date: Optional[datetime] = None
    ) -> dict:
        """Send summary to multiple recipients."""
        results = {"success": [], "failed": []}
        
        for recipient in recipients:
            try:
                await self.send_summary(recipient, pdf_path, platform, meeting_date)
                results["success"].append(recipient)
            except Exception as e:
                logger.error(f"Failed to send to {recipient}: {e}")
                results["failed"].append({"email": recipient, "error": str(e)})
        
        return results
