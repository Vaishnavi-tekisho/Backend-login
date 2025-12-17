"""
OTP Schema
Database schema definition for user_otps table in Supabase.
"""


class OTPSchema:
    """
    OTP table schema definition.
    
    Table: user_otps
    
    Columns:
        - id: UUID (Primary Key, auto-generated)
        - phone: VARCHAR(20)
        - otp: VARCHAR(6)
        - expires_at: TIMESTAMP WITH TIME ZONE
        - is_used: BOOLEAN (default: false)
        - created_at: TIMESTAMP WITH TIME ZONE
    """
    
    __tablename__ = "user_otps"
    
    COLUMNS = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "phone": "VARCHAR(20) NOT NULL",
        "otp": "VARCHAR(6) NOT NULL",
        "expires_at": "TIMESTAMP WITH TIME ZONE NOT NULL",
        "is_used": "BOOLEAN DEFAULT FALSE",
        "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
    }


# SQL to create the table (for reference)
CREATE_OTP_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_otps_phone ON user_otps(phone);
"""
