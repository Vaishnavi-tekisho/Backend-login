"""
Email Service
Handles all email sending operations using SendGrid dynamic templates.
"""
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To
from app.core.config import settings


class EmailService:
    """Service for sending emails via SendGrid"""
    
    APP_NAME = "LeadQ"
    
    @staticmethod
    def send_email_with_template(to_email: str, template_data: dict) -> bool:
        """
        Send an email using SendGrid dynamic template.
        
        Args:
            to_email: Recipient email address
            template_data: Dictionary with dynamic data for the template
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', None)
            template_id = getattr(settings, 'SENDGRID_TEMPLATE_ID', None)

            # DEV MODE: Log email to console instead of sending
            dev_mode = getattr(settings, 'SENDGRID_DEV_MODE', 'false')
            if isinstance(dev_mode, str):
                dev_mode = dev_mode.lower() == 'true'
            
            if dev_mode:
                print("=" * 50)
                print("🔧 DEV MODE - Email not actually sent")
                print(f"📬 To: {to_email}")
                print(f"📄 Template Data: {template_data}")
                print("=" * 50)
                return True

            if not api_key or not template_id:
                print("❌ SendGrid API key or Template ID not configured")
                return False

            # Create SendGrid message with dynamic template
            message = Mail(
                from_email=from_email,
                to_emails=To(to_email)
            )
            message.template_id = template_id
            message.dynamic_template_data = template_data
            
            # Send via SendGrid
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ SendGrid Error: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Email Sending Error: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_otp(to_email: str, otp: str) -> bool:
        """
        Send password reset OTP email using SendGrid dynamic template.
        
        Args:
            to_email: Recipient email address
            otp: The 6-digit OTP code
            
        Returns:
            bool: True if email sent successfully
        """
        template_data = {
            "otp": otp,
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year)
        }
        
        return EmailService.send_email_with_template(to_email, template_data)
