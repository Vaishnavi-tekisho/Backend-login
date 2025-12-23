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

class UsersLoginSchema:
    """
    Table: users_login
    Purpose: Authentication & Core Identity
    """
    __tablename__ = "users_login"
    
    COLUMNS = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "email": "VARCHAR(255) UNIQUE NOT NULL",
        "password": "TEXT NOT NULL",
        "first_name": "TEXT",
        "last_name": "TEXT",
        "phone_number": "VARCHAR(20)",
        "phone_verification": "BOOLEAN DEFAULT FALSE",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "email_verified": "BOOLEAN DEFAULT FALSE",
        "remember_me": "BOOLEAN DEFAULT FALSE",
        "remember_token": "VARCHAR(255)",
        "remember_token_expires_at": "TIMESTAMP WITH TIME ZONE",
        "acc_created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "acc_updated_at": "TIMESTAMP WITH TIME ZONE",
        "password_updated_at": "TIMESTAMP WITH TIME ZONE",
        "email_verification_token": "VARCHAR(255)",
        "email_verification_token_expiry": "TIMESTAMP WITH TIME ZONE",
        "email_last_verification_sent_at": "TIMESTAMP WITH TIME ZONE"
    }

class UsersProfileLoginSchema:
    """
    Table: users_profile_login
    Purpose: Session & Activity Data
    """
    __tablename__ = "users_profile_login"
    
    COLUMNS = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "user_id": "UUID REFERENCES users_login(id) UNIQUE",
        "last_login": "TIMESTAMP WITH TIME ZONE",
        "activity_time": "TIMESTAMP WITH TIME ZONE",
        "no_of_logins": "INTEGER DEFAULT 0",
        "oauth_provider": "VARCHAR(50)",
        "oauth_id": "VARCHAR(255)",
        "profile_image_url": "TEXT",
        "ip_address": "VARCHAR(45)",
        "location": "VARCHAR(255)",
        "reset_otp": "VARCHAR(255)",
        "reset_otp_expiry": "TIMESTAMP WITH TIME ZONE",
        "is_anonym": "BOOLEAN DEFAULT FALSE",
        "banned_until": "TIMESTAMP WITH TIME ZONE",
        "deleted_at": "TIMESTAMP WITH TIME ZONE",
        "password_change_attempts": "INTEGER DEFAULT 0",
        "last_password_change_attempt": "TIMESTAMP WITH TIME ZONE"
    }

# SQL to create the tables (for reference)
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone_number VARCHAR(20),
    phone_verification BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    remember_me BOOLEAN DEFAULT FALSE,
    acc_created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acc_updated_at TIMESTAMP WITH TIME ZONE,
    password_updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS users_profile_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users_login(id) UNIQUE,
    last_login TIMESTAMP WITH TIME ZONE,
    activity_time TIMESTAMP WITH TIME ZONE,
    no_of_logins INTEGER DEFAULT 0,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    profile_image_url TEXT,
    ip_address VARCHAR(45),
    location VARCHAR(255),
    reset_otp VARCHAR(255),
    reset_otp_expiry TIMESTAMP WITH TIME ZONE,
    is_anonym BOOLEAN DEFAULT FALSE,
    banned_until TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_login_email ON users_login(email);
CREATE INDEX IF NOT EXISTS idx_users_profile_user_id ON users_profile_login(user_id);
"""
