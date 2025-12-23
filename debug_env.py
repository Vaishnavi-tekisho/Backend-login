from src.core.config import settings
import os

print("\n--- Environment Diagnostics ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Looking for .env in: {os.path.join(os.getcwd(), '.env')}")
print(f".env exists: {os.path.exists('.env')}")

print("\n--- Loaded Settings (Pydantic) ---")
print(f"SENDGRID_API_KEY: {'[FOUND]' if settings.SENDGRID_API_KEY else '[MISSING]'}")
print(f"SENDGRID_OTP_TEMPLATE_ID: {settings.SENDGRID_OTP_TEMPLATE_ID}")
print(f"SENDGRID_RESET_TEMPLATE_ID: {settings.SENDGRID_RESET_TEMPLATE_ID}")
print(f"SENDGRID_EMAIL_VERIFICATION_TEMPLATE_ID: {settings.SENDGRID_EMAIL_VERIFICATION_TEMPLATE_ID}")
print(f"SENDGRID_SUCCESSFUL_LOGIN_TEMPLATE_ID: {settings.SENDGRID_SUCCESSFUL_LOGIN_TEMPLATE_ID}")

print("\n--- Raw OS Environment (Check for typos) ---")
for key in os.environ:
    if "SENDGRID" in key:
        print(f"{key}: {os.environ[key]}")
print("-------------------------------\n")
