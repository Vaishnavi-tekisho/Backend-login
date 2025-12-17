from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import random, hashlib
from app.database import get_db
from app.utils import send_otp_email
from app.schemas import User
from app.otp_service import store_otp, verify_otp
from app.twilio_client import send_sms

router = APIRouter()

# Models
class OTPRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class PasswordUpdateRequest(BaseModel):
    email: str
    otp: str
    new_password: str

# Generate OTP
@router.post("/generate-otp")
async def generate_otp(request: OTPRequest, db=Depends(get_db)):
    otp = str(random.randint(100000, 999999))
    hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
    expiry = datetime.utcnow() + timedelta(minutes=10)

    # Store OTP in DB
    store_otp(db, request.email, hashed_otp, expiry)

    # Send OTP via email using SendGrid template
    send_otp_email(request.email, otp)

    return {"message": "OTP sent successfully"}

# Verify OTP
@router.post("/verify-otp")
async def verify_otp_endpoint(request: OTPVerifyRequest, db=Depends(get_db)):
    if not verify_otp(db, request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {"message": "OTP verified successfully"}

# Update Password
@router.post("/update-password")
async def update_password(request: PasswordUpdateRequest, db=Depends(get_db)):
    if not verify_otp(db, request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Update password in Supabase Auth
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = request.new_password  # Hash password in production
    db.commit()

    return {"message": "Password updated successfully"}
