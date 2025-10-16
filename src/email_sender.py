# src/email_sender.py
"""Email service for sending job recommendations."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from src.logger import get_logger
from src.config import get_settings

logger = get_logger()


class EmailSender:
    """Send job recommendations via email."""
    
    def __init__(self):
        """Initialize email sender with SMTP settings."""
        settings = get_settings()
        
        self.smtp_server = getattr(settings, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.sender_email = getattr(settings, 'google_owner_email', None)
        self.sender_password = getattr(settings, 'sender_password', None)
        
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured")
        else:
            logger.info(f"✅ Email sender initialized ({self.sender_email})")
    
    def send_job_recommendations(
        self,
        recipient_email: str,
        candidate_name: str,
        csv_path: str,
        job_count: int,
        market_readiness: Optional[float] = None
    ) -> bool:
        """
        Send job recommendations email with CSV attachment.
        
        Args:
            recipient_email: Recipient's email address
            candidate_name: Name of the candidate
            csv_path: Path to CSV file to attach
            job_count: Number of jobs in the CSV
            market_readiness: Optional market readiness score
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not configured")
            return False
        
        try:
            logger.info(f"Sending job recommendations to {recipient_email}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Your Job Recommendations - {job_count} Opportunities"
            
            # Email body
            body = self._create_email_body(
                candidate_name, 
                job_count, 
                market_readiness
            )
            
            msg.attach(MIMEText(body, 'html'))
            
            # Attach CSV file
            self._attach_csv(msg, csv_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _create_email_body(
        self, 
        candidate_name: str, 
        job_count: int,
        market_readiness: Optional[float]
    ) -> str:
        """Create HTML email body."""
        
        readiness_html = ""
        if market_readiness is not None:
            readiness_color = "green" if market_readiness >= 70 else "orange" if market_readiness >= 50 else "red"
            readiness_html = f"""
            <p style="font-size: 16px;">
                <strong>Market Readiness:</strong> 
                <span style="color: {readiness_color}; font-weight: bold;">
                    {market_readiness:.1f}%
                </span>
            </p>
            """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c5aa0;">🎯 Your Job Recommendations</h1>
                
                <p>Hi {candidate_name},</p>
                
                <p>Great news! We've found <strong>{job_count} job opportunities</strong> that match your profile.</p>
                
                {readiness_html}
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">📎 Attached File</h3>
                    <p>Your personalized job recommendations are attached as a CSV file. You can:</p>
                    <ul>
                        <li>Open it in Excel or Google Sheets</li>
                        <li>Track your application status</li>
                        <li>Add notes for each job</li>
                    </ul>
                </div>
                
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5aa0;">💡 Next Steps</h3>
                    <ol>
                        <li>Review the job opportunities in the attached file</li>
                        <li>Click on the job URLs to learn more</li>
                        <li>Update the "Status" column as you apply</li>
                        <li>Track your progress and stay organized!</li>
                    </ol>
                </div>
                
                <p style="margin-top: 30px;">
                    Good luck with your job search! 🚀
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    <em>This is an automated email from Ascend Job Recommendation System</em>
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _attach_csv(self, msg: MIMEMultipart, csv_path: str):
        """Attach CSV file to email."""
        
        filename = Path(csv_path).name
        
        with open(csv_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        
        msg.attach(part)
        
        logger.debug(f"Attached file: {filename}")


logger.info("✅ EmailSender module initialized")
