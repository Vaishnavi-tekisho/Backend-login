from twilio.rest import Client
from app.config import settings

class TwilioClient:
    """Wrapper for Twilio SMS client"""
    
    def __init__(self):
        self.client = None
        self.from_number = None
    
    def _ensure_initialized(self):
        """Lazy initialization of Twilio client"""
        if self.client is None:
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                raise ValueError("Twilio credentials not configured in .env")
            
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.from_number = settings.TWILIO_PHONE_NUMBER
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS to a phone number
        
        Args:
            to_number: Phone number in E.164 format (e.g., +1234567890)
            message: SMS message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            self._ensure_initialized()
            
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            print(f"SMS sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_otp(self, to_number: str, otp_code: str) -> bool:
        """
        Send OTP code via SMS
        
        Args:
            to_number: Phone number in E.164 format
            otp_code: 6-digit OTP code
            
        Returns:
            bool: True if sent successfully
        """
        message = f"Your LeadQ verification code is: {otp_code}. Valid for 5 minutes."
        return self.send_sms(to_number, message)

# Singleton instance
twilio_client = TwilioClient()

def get_twilio_client() -> TwilioClient:
    """Get Twilio client instance"""
    return twilio_client
