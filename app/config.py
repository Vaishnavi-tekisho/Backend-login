from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str # Public Anon Key
    SUPABASE_SECRET_KEY: str # Service Role Key (Optional, use carefully)

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None
    TWILIO_VERIFY_SERVICE_SID: str | None = None
    
    # Email Service (SendGrid)
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: str | None = None
    SENDGRID_TEMPLATE_ID: str | None = None  # Generic/Fallback
    SENDGRID_RESET_TEMPLATE_ID: str | None = None
    SENDGRID_EMAIL_VERIFICATION_TEMPLATE_ID: str | None = None
    SENDGRID_SUCCESSFUL_LOGIN_TEMPLATE_ID: str | None = None
    SENDGRID_DEV_MODE: str = "false"  # Set to "true" to log emails instead of sending
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
