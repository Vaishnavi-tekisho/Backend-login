"""
Auth Constants
Fixed values and configuration constants for auth module.
"""

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5

# Password Reset
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 15

# Email Verification
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24

# Twilio
TWILIO_SMS_CHANNEL = "sms"
TWILIO_VERIFICATION_APPROVED = "approved"

# OAuth
OAUTH_PROVIDER_EMAIL = "email"
OAUTH_PROVIDER_GOOGLE = "google"

# Database Tables
TABLE_USERS_LOGIN = "users_login"
TABLE_USERS_PROFILE = "users_profile_login"
TABLE_USER_OTPS = "user_otps"
