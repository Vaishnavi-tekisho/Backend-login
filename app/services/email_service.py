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
    def send_email_with_template(to_email: str, template_data: dict, template_id: str = None) -> bool:
        """
        Send an email using SendGrid dynamic template.
        
        Args:
            to_email: Recipient email address
            template_data: Dictionary with dynamic data for the template
            template_id: Optional specific template ID (overrides default/fallback)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', None)
            
            # Use specific template_id if provided, else fallback to generic config
            tid = template_id if template_id else getattr(settings, 'SENDGRID_OTP_TEMPLATE_ID', None)

            # DEV MODE: Log email to console instead of sending
            dev_mode = getattr(settings, 'SENDGRID_DEV_MODE', 'false')
            if isinstance(dev_mode, str):
                dev_mode = dev_mode.lower() == 'true'

            if dev_mode:
                print("=" * 50)
                print(f"🔧 DEV MODE - Email (Template: {tid})")
                print(f"📬 To: {to_email}")
                print(f"📄 Template Data: {template_data}")
                print("=" * 50)
                return True

            print(f"\n\n🚨🚨🚨 DEBUG: SENDING EMAIL 🚨🚨🚨", flush=True)
            print(f"🚀 TO: {to_email}", flush=True)
            print(f"🆔 TEMPLATE_ID: {tid}", flush=True)
            print(f"📄 DATA: {template_data}", flush=True)
            print(f"🚨🚨🚨 END DEBUG 🚨🚨🚨\n\n", flush=True)

            if not api_key:
                print(f"❌ ERROR: SENDGRID_API_KEY NOT FOUND!", flush=True)
                return False
            
            if not tid:
                print(f"❌ ERROR: TEMPLATE ID NOT FOUND! (TID={tid})", flush=True)
                return False

            # Create SendGrid message with dynamic template
            message = Mail(
                from_email=from_email,
                to_emails=To(to_email)
            )
            message.template_id = tid
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
        Uses default/generic template ID (Legacy support)
        """
        template_data = {
            "otp": otp,
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year)
        }
        
        return EmailService.send_email_with_template(to_email, template_data)

    @staticmethod
    def send_verification_email(to_email: str, link: str, user_context: dict = {}) -> bool:
        """
        Send email verification link using specific Verification Template.
        
        Args:
            to_email: Recipient email address
            link: The verification link URL
            user_context: Dict containing user info
        """
        template_id = getattr(settings, 'SENDGRID_EMAIL_VERIFICATION_TEMPLATE_ID', None)
        
        template_data = {
            "verify_link": link,
            "verify link": link, 
            "[verify link]": link, # Handlebars bracket notation
            "action_url": link,
            "link": link,
            "url": link,
            "Button": link,      
            "button_url": link,
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year),
            **user_context
        }
        
        return EmailService.send_email_with_template(to_email, template_data, template_id)

    @staticmethod
    def send_login_success_email(to_email: str, user_context: dict = {}) -> bool:
        """
        Send successful login notification using specific Login Template.
        
        Args:
            to_email: Recipient email address
            user_context: Dict containing user info (name, ip, device, etc.)
        """
        template_id = getattr(settings, 'SENDGRID_SUCCESSFUL_LOGIN_TEMPLATE_ID', None)
        
        template_data = {
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year),
            "login_time": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            **user_context
        }
        
        return EmailService.send_email_with_template(to_email, template_data, template_id)
