"""
Auth Service
Business logic for authentication, password reset, email verification, and OTP operations.
"""
import random
import string
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Tuple

from src.core.config import settings
from src.core.security import create_access_token
from src.modules.auth.utils import hash_password, verify_password, hash_otp, verify_otp
from src.modules.auth.repository import (
    UserRepository,
    UserProfileRepository,
    PasswordResetRepository,
    EmailVerificationRepository,
    OTPRepository
)
from src.modules.auth.constants import (
    OTP_LENGTH,
    OTP_EXPIRY_MINUTES,
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
    EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS,
    OAUTH_PROVIDER_EMAIL,
    OAUTH_PROVIDER_GOOGLE,
    TWILIO_SMS_CHANNEL,
    TWILIO_VERIFICATION_APPROVED
)


# Email Service
class EmailService:
    """Service for email operations."""
    
    APP_NAME = "LeadQ"
    
    @staticmethod
    def send_email_with_template(to_email: str, template_data: dict, template_id: str = None) -> bool:
        """
        Send email using SendGrid dynamic template.
        
        Args:
            to_email: Recipient email
            template_data: Template variables
            template_id: Optional template ID
            
        Returns:
            bool: Success status
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, To
            
            api_key = getattr(settings, 'SENDGRID_API_KEY', None)
            from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', None)
            tid = template_id if template_id else getattr(settings, 'SENDGRID_TEMPLATE_ID', None)
            
            # Dev mode
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
            
            message = Mail(from_email=from_email, to_emails=To(to_email))
            message.template_id = tid
            message.dynamic_template_data = template_data
            
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ SendGrid Error: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Email sending error: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_otp(to_email: str, otp: str) -> bool:
        """Send password reset OTP."""
        template_data = {
            "otp": otp,
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year)
        }
        template_id = getattr(settings, 'SENDGRID_OTP_TEMPLATE_ID', None)
        return EmailService.send_email_with_template(to_email, template_data, template_id)
    
    @staticmethod
    def send_password_reset_link(to_email: str, link: str, user_context: dict = None) -> bool:
        """Send password reset link."""
        if user_context is None:
            user_context = {}
        
        template_id = getattr(settings, 'SENDGRID_RESET_TEMPLATE_ID', None)
        template_data = {
            "reset_link": link,
            "action_url": link,
            "#reset_link": link,
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year),
            **user_context
        }
        return EmailService.send_email_with_template(to_email, template_data, template_id)
    
    @staticmethod
    def send_verification_email(to_email: str, link: str, user_context: dict = None) -> bool:
        """
        Send email verification link using specific Verification Template.
        Supports multiple variable names for SendGrid compatibility.
        """
        if user_context is None:
            user_context = {}
        
        # Use specific verification template ID
        template_id = getattr(settings, 'SENDGRID_EMAIL_VERIFICATION_TEMPLATE_ID', None)
        
        template_data = {
            "verify_link": link,
            "verify link": link, 
            "[verify link]": link, 
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
    def send_login_success_email(to_email: str, user_context: dict = None) -> bool:
        """
        Send successful login notification using specific Login Template.
        """
        if user_context is None:
            user_context = {}
            
        template_id = getattr(settings, 'SENDGRID_SUCCESSFUL_LOGIN_TEMPLATE_ID', None)
        
        template_data = {
            "app_name": EmailService.APP_NAME,
            "year": str(datetime.now().year),
            "login_time": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            **user_context
        }
        
        return EmailService.send_email_with_template(to_email, template_data, template_id)


# Authentication Service
class AuthService:
    """Service for core authentication operations."""
    
    @staticmethod
    def register_user(email: str, password: str, first_name: str = None, 
                      last_name: str = None, phone_number: str = None, 
                      location: str = None, client_host: str = None) -> Tuple[bool, Optional[dict], str]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            first_name: Optional first name
            last_name: Optional last name
            phone_number: Optional phone number
            location: Optional location
            client_host: Client IP address
            
        Returns:
            (success, user_dict, message)
        """
        try:
            # Check if user exists
            if UserRepository.exists(email):
                return False, None, "Email already registered"
            
            # Hash password
            hashed_password = hash_password(password)
            
            # Create user in users_login
            user_data = {
                "email": email,
                "password": hashed_password,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "phone_verification": False,
                "is_active": True,
                "email_verified": False,
                "remember_me": False,
                "remember_token": None,
                "remember_token_expires_at": None,
                "acc_created_at": datetime.utcnow().isoformat(),
                "acc_updated_at": datetime.utcnow().isoformat()
            }
            
            user = UserRepository.create(user_data)
            if not user:
                return False, None, "Failed to create user"
            
            user_id = user["id"]
            
            # Create profile in users_profile_login
            profile_data = {
                "user_id": user_id,
                "location": location,
                "ip_address": client_host,
                "oauth_provider": OAUTH_PROVIDER_EMAIL,
                "last_login": datetime.utcnow().isoformat(),
                "activity_time": datetime.utcnow().isoformat(),
                "no_of_logins": 1
            }
            
            profile = UserProfileRepository.create(profile_data)
            if not profile:
                print(f"Warning: Failed to create profile for user {user_id}")
            
            # Combine response
            combined_user = {**user, **(profile or {})}
            
            return True, combined_user, "User registered successfully"
            
        except Exception as e:
            print(f"Error during registration: {e}")
            return False, None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def login_user(email: str, password: str, remember_me: bool = False,
                   location: str = None, client_host: str = None) -> Tuple[bool, Optional[dict], Optional[str], str]:
        """
        Login user with email and password.
        
        Args:
            email: User email
            password: User password
            remember_me: Enable remember me token
            location: Optional location
            client_host: Client IP
            
        Returns:
            (success, user_dict, access_token, message)
        """
        try:
            # Get user
            user = UserRepository.get_by_email(email)
            if not user or not user.get("password"):
                return False, None, None, "Invalid email or password"
            
            # Verify password
            if not verify_password(password, user["password"]):
                return False, None, None, "Invalid email or password"
            
            # Check email verification
            if not user.get("email_verified"):
                return False, user, None, "Email not verified. Please verify your email before logging in."

            # Update stats in profile
            try:
                profile = UserProfileRepository.get_by_user_id(user["id"])
                current_time = datetime.utcnow().isoformat()
                
                if profile:
                    current_count = profile.get("no_of_logins", 0) or 0
                    update_data = {
                        "last_login": current_time,
                        "activity_time": current_time,
                        "ip_address": client_host,
                        "no_of_logins": current_count + 1
                    }
                    if location:
                        update_data["location"] = location
                    
                    UserProfileRepository.update(user["id"], update_data)
                else:
                    insert_data = {
                        "user_id": user["id"],
                        "last_login": current_time,
                        "activity_time": current_time,
                        "ip_address": client_host,
                        "no_of_logins": 1
                    }
                    if location:
                        insert_data["location"] = location
                    
                    UserProfileRepository.create(insert_data)
            except Exception as e:
                print(f"Warning: Failed to update login stats: {e}")
            
            # Handle remember me
            if remember_me:
                remember_token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(days=30)
                
                try:
                    UserRepository.update(user["id"], {
                        "remember_me": True,
                        "remember_token": remember_token,
                        "remember_token_expires_at": expires_at.isoformat()
                    })
                    user["remember_token"] = remember_token
                    user["remember_token_expires_at"] = expires_at.isoformat()
                except Exception as e:
                    print(f"Warning: Failed to set remember token: {e}")
            
            # Fetch full profile for response
            profile = UserProfileRepository.get_by_user_id(user["id"])
            combined_user = {**user, **(profile or {})}
            
            # Create access token
            access_token = create_access_token(data={"sub": user["email"]})
            
            return True, combined_user, access_token, "Login successful"
            
        except Exception as e:
            print(f"Error during login: {e}")
            return False, None, None, f"Login failed: {str(e)}"


# Password Reset Service
class PasswordResetService:
    """Service for password reset operations."""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit numeric OTP."""
        return ''.join(random.choices(string.digits, k=OTP_LENGTH))
    
    @staticmethod
    def is_expired(expiry_str: str) -> bool:
        """Check if timestamp is expired."""
        try:
            expiry_str_clean = expiry_str.replace('Z', '+00:00')
            if '+' in expiry_str_clean:
                expiry_time = datetime.fromisoformat(expiry_str_clean).replace(tzinfo=None)
            else:
                expiry_time = datetime.fromisoformat(expiry_str_clean)
            return datetime.utcnow() > expiry_time
        except Exception as e:
            print(f"Error parsing expiry time: {e}")
            return True
    
    @staticmethod
    def request_password_reset(email: str) -> dict:
        """
        Request password reset via OTP.
        
        Steps:
        1. Check if user exists
        2. Generate OTP
        3. Hash and store OTP
        4. Send OTP via email
        
        Args:
            email: User email
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            # Check user exists
            user = UserRepository.get_by_email(email)
            if not user:
                return {
                    "success": False,
                    "error": "Account not found. Please create an account first."
                }
            
            # Generate OTP
            otp = PasswordResetService.generate_otp()
            
            # Hash and store
            hashed_otp = hash_otp(otp)
            expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            
            if not PasswordResetRepository.store_reset_otp(email, hashed_otp, expiry):
                return {
                    "success": False,
                    "error": "Failed to process request. Please try again."
                }
            
            # Send email
            if not EmailService.send_password_reset_otp(email, otp):
                return {
                    "success": False,
                    "error": "Failed to send OTP email. Please try again."
                }
            
            return {
                "success": True,
                "message": "OTP has been sent to your email."
            }
        except Exception as e:
            print(f"Error requesting password reset: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def verify_reset_otp(email: str, otp: str) -> dict:
        """
        Verify password reset OTP.
        
        Args:
            email: User email
            otp: OTP code
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            stored_hash, expiry_str = PasswordResetRepository.get_reset_otp(email)
            
            if not stored_hash or not expiry_str:
                return {
                    "success": False,
                    "error": "No OTP request found. Please request a new OTP."
                }
            
            # Check expiry
            if PasswordResetService.is_expired(expiry_str):
                PasswordResetRepository.invalidate_reset_otp(email)
                return {
                    "success": False,
                    "error": "OTP has expired. Please request a new OTP."
                }
            
            # Verify OTP
            if not verify_otp(otp, stored_hash):
                return {
                    "success": False,
                    "error": "Invalid OTP. Please check and try again."
                }
            
            return {
                "success": True,
                "message": "OTP verified successfully."
            }
        except Exception as e:
            print(f"Error verifying OTP: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def reset_password(email: str, otp: str, new_password: str) -> dict:
        """
        Reset password with OTP verification.
        
        Args:
            email: User email
            otp: OTP code
            new_password: New password
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            # Verify OTP first
            verification = PasswordResetService.verify_reset_otp(email, otp)
            if not verification["success"]:
                return verification
            
            # Update password
            if not UserRepository.update_password(email, new_password):
                return {
                    "success": False,
                    "error": "Failed to update password. Please try again."
                }
            
            # Invalidate OTP
            try:
                PasswordResetRepository.invalidate_reset_otp(email)
            except Exception as e:
                print(f"Warning: Failed to invalidate OTP: {e}")
            
            return {
                "success": True,
                "message": "Password reset successfully. You can now login with your new password."
            }
        except Exception as e:
            print(f"Error resetting password: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def request_password_reset_link(email: str, redirect_url: str = "http://localhost:5173/reset-password") -> dict:
        """
        Request password reset via magic link.
        
        Args:
            email: User email
            redirect_url: URL to redirect after clicking link
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            # Check user exists
            user = UserRepository.get_by_email(email)
            if not user:
                return {
                    "success": False,
                    "error": "Account not found. Please create an account first."
                }
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            hashed_token = hash_otp(token)
            expiry = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
            
            # Store token
            if not PasswordResetRepository.store_reset_otp(email, hashed_token, expiry):
                return {
                    "success": False,
                    "error": "Failed to generate reset link. Please try again."
                }
            
            # Construct link
            encoded_token = urllib.parse.quote(token)
            encoded_email = urllib.parse.quote(email)
            separator = "&" if "?" in redirect_url else "?"
            link = f"{redirect_url}{separator}token={encoded_token}&email={encoded_email}"
            
            # Send email
            user_context = {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "name": user.get("first_name", "")
            }
            
            if not EmailService.send_password_reset_link(email, link, user_context):
                return {
                    "success": False,
                    "error": "Failed to send reset link email. Please try again."
                }
            
            return {
                "success": True,
                "message": "Password reset link has been sent to your email."
            }
        except Exception as e:
            print(f"Error sending password reset link: {e}")
            return {"success": False, "error": str(e)}


# Email Verification Service
class VerificationService:
    """Service for email verification operations."""
    
    @staticmethod
    def request_verification_email(email: str, redirect_url: str = "http://localhost:5173/login/verification-success") -> dict:
        """
        Send email verification link.
        
        Args:
            email: User email
            redirect_url: Redirect URL after verification
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            # Get user
            user = UserRepository.get_by_email(email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check if already verified
            if user.get("email_verified"):
                return {"success": False, "error": "Email already verified"}
            
            # Generate token
            token = secrets.token_urlsafe(32)
            hashed_token = hash_otp(token)
            expiry = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS)
            
            # Store token
            if not EmailVerificationRepository.store_verification_token(email, hashed_token, expiry):
                return {"success": False, "error": "Database error"}
            
            # Construct link
            encoded_token = urllib.parse.quote(token)
            encoded_email = urllib.parse.quote(email)
            separator = "&" if "?" in redirect_url else "?"
            link = f"{redirect_url}{separator}token={encoded_token}&email={encoded_email}"
            
            # Send email
            user_context = {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "name": user.get("first_name", "")
            }
            
            if not EmailService.send_verification_email(email, link, user_context):
                return {"success": False, "error": "Failed to send email"}
            
            return {"success": True, "message": "Verification email sent"}
        except Exception as e:
            print(f"Error requesting verification: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def verify_email(email: str, token: str) -> dict:
        """
        Verify email with token.
        
        Args:
            email: User email
            token: Verification token
            
        Returns:
            dict: {success: bool, message: str, error: str}
        """
        try:
            # Check if user already verified
            user = UserRepository.get_by_email(email)
            if not user:
                return {"success": False, "error": "User not found"}
            
            if user.get("email_verified"):
                return {"success": True, "message": "Email verified successfully"}

            # Get stored token
            stored_hash = user.get("email_verification_token")
            expiry_str = user.get("email_verification_token_expiry")
            
            if not stored_hash or not expiry_str:
                return {"success": False, "error": "Invalid verification request"}
            
            # Check expiry
            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if datetime.utcnow() > expiry_date:
                return {"success": False, "error": "Token expired"}
            
            # Verify token
            if not verify_otp(token, stored_hash):
                return {"success": False, "error": "Invalid token"}
            
            # Mark verified
            if not EmailVerificationRepository.mark_email_verified(email):
                return {"success": False, "error": "Failed to update status"}
            
            # Fetch full profile for auto-login
            profile = UserProfileRepository.get_by_user_id(user["id"])
            combined_user = {**user, **(profile or {})}
            combined_user["email_verified"] = True # Ensure reflected in response
            
            # Create access token
            access_token = create_access_token(data={"sub": user["email"]})
            
            return {
                "success": True, 
                "message": "Email verified successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "user": combined_user
            }
        except Exception as e:
            print(f"Error verifying email: {e}")
            return {"success": False, "error": str(e)}


# OTP Service
class OTPService:
    """Service for SMS OTP operations."""
    
    @staticmethod
    def send_otp(phone_number: str) -> dict:
        """
        Send OTP via SMS using Twilio.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            dict: {success: bool, message: str}
        """
        try:
            from twilio.rest import Client as TwilioClient
            
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            if not all([account_sid, auth_token, verify_service_sid]):
                print("Missing Twilio config")
                return {"success": False, "message": "Server config error: Missing Twilio credentials"}
            
            client = TwilioClient(account_sid, auth_token)
            verification = client.verify.v2.services(verify_service_sid).verifications.create(
                to=phone_number,
                channel=TWILIO_SMS_CHANNEL
            )
            
            return {"success": True, "message": "OTP sent successfully"}
        except Exception as e:
            print(f"Error sending OTP: {e}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def verify_otp(phone_number: str, otp_code: str) -> dict:
        """
        Verify SMS OTP using Twilio.
        
        Args:
            phone_number: Phone number in E.164 format
            otp_code: OTP code to verify
            
        Returns:
            dict: {success: bool, message: str}
        """
        try:
            from twilio.rest import Client as TwilioClient
            
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            if not all([account_sid, auth_token, verify_service_sid]):
                return {"success": False, "message": "Server config error"}
            
            client = TwilioClient(account_sid, auth_token)
            verification_check = client.verify.v2.services(verify_service_sid).verification_checks.create(
                to=phone_number,
                code=otp_code
            )
            
            if verification_check.status == TWILIO_VERIFICATION_APPROVED:
                # Update database
                try:
                    OTPRepository.update_phone_verification(phone_number)
                except Exception as e:
                    print(f"Warning: Failed to update phone verification: {e}")
                
                return {"success": True, "message": "OTP verified"}
            else:
                return {"success": False, "message": "Invalid OTP"}
        except Exception as e:
            print(f"Error verifying OTP: {e}")
            return {"success": False, "message": str(e)}
