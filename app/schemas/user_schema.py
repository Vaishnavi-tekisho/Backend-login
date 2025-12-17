"""
User Schema
Database schema definition for users table in Supabase.
This represents the structure of the users table.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
import uuid


# Note: This is a schema definition for documentation and potential ORM use.
# Supabase is accessed via REST API, so this serves as a reference.

class UserSchema:
    """
    User table schema definition.
    
    Table: users
    
    Columns:
        - id: UUID (Primary Key, auto-generated)
        - email: VARCHAR(255), unique, indexed
        - password: TEXT (hashed, nullable for OAuth users)
        - user_name: TEXT
        - profile_image_url: TEXT
        - phone_number: VARCHAR(20)
        - acc_created_at: TIMESTAMP WITH TIME ZONE
        - acc_updated_at: TIMESTAMP WITH TIME ZONE
        - last_login: TIMESTAMP WITH TIME ZONE
        - is_active: BOOLEAN (default: true)
        - email_verified: BOOLEAN (default: false)
        - phone_verified: BOOLEAN (default: false)
        - oauth_provider: VARCHAR(50) ('google', 'facebook', 'email')
        - oauth_id: VARCHAR(255)
        - account_plan: DATE
        - account_plan_validity: DATE
        - no_of_logins: INTEGER (default: 0)
        - activity_time: TIMESTAMP WITH TIME ZONE
        - ip_address: INET
        - location: VARCHAR(255)
        - reset_otp: VARCHAR(255) (hashed OTP for password reset)
        - reset_otp_expiry: TIMESTAMP WITH TIME ZONE
    """
    
    __tablename__ = "users"
    
    # Column definitions (for reference)
    COLUMNS = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "email": "VARCHAR(255) UNIQUE NOT NULL",
        "password": "TEXT",
        "user_name": "TEXT",
        "profile_image_url": "TEXT",
        "phone_number": "VARCHAR(20)",
        "acc_created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "acc_updated_at": "TIMESTAMP WITH TIME ZONE",
        "last_login": "TIMESTAMP WITH TIME ZONE",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "email_verified": "BOOLEAN DEFAULT FALSE",
        "phone_verified": "BOOLEAN DEFAULT FALSE",
        "oauth_provider": "VARCHAR(50)",
        "oauth_id": "VARCHAR(255)",
        "account_plan": "DATE",
        "account_plan_validity": "DATE",
        "no_of_logins": "INTEGER DEFAULT 0",
        "activity_time": "TIMESTAMP WITH TIME ZONE",
        "ip_address": "INET",
        "location": "VARCHAR(255)",
        "reset_otp": "VARCHAR(255)",
        "reset_otp_expiry": "TIMESTAMP WITH TIME ZONE",
    }


# SQL to create the table (for reference)
CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT,
    user_name TEXT,
    profile_image_url TEXT,
    phone_number VARCHAR(20),
    acc_created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acc_updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    account_plan DATE,
    account_plan_validity DATE,
    no_of_logins INTEGER DEFAULT 0,
    activity_time TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    location VARCHAR(255),
    reset_otp VARCHAR(255),
    reset_otp_expiry TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""
