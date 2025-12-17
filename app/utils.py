from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

# Password Hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if plain password matches hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def send_email_with_template(to_email: str, template_data: dict):
    """
    Send an email using SendGrid dynamic template.
    
    Args:
        to_email: Recipient email address
        template_data: Dictionary with dynamic data for the template
                      (e.g., {'otp': '123456', 'app_name': 'LeadQ'})
    """
    # Dev mode - just log the email
    if settings.SENDGRID_DEV_MODE.lower() == "true":
        print(f"[DEV MODE] Email to: {to_email}")
        print(f"[DEV MODE] Template data: {template_data}")
        return True
    
    try:
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=To(to_email)
        )
        
        # Use SendGrid dynamic template
        message.template_id = settings.SENDGRID_TEMPLATE_ID
        message.dynamic_template_data = template_data
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"Email sent to {to_email}, status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_otp_email(to_email: str, otp: str, app_name: str = "LeadQ"):
    """
    Send OTP email for password reset using SendGrid template.
    
    Args:
        to_email: Recipient email address
        otp: The OTP code
        app_name: Application name (default: LeadQ)
    """
    template_data = {
        "otp": otp,
        "app_name": app_name,
        "year": str(datetime.now().year)
    }
    return send_email_with_template(to_email, template_data)
