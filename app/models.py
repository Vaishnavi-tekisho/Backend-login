from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users" # Assuming table name is 'users', change if different

    # Primary Key (UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    
    # Core Auth
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(Text, nullable=True) # Hashed password (NULL for OAuth)
    
    # Profile Info
    user_name = Column(Text, nullable=True)
    profile_image_url = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Timestamps
    acc_created_at = Column(DateTime(timezone=True), server_default=func.now())
    acc_updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # OAuth
    oauth_provider = Column(String(50), nullable=True) # 'google', 'facebook'
    oauth_id = Column(String(255), nullable=True)
    
    # Subscription/Analytics
    account_plan = Column(Date, nullable=True)
    account_plan_validity = Column(Date, nullable=True)
    no_of_logins = Column(Integer, default=0)
    activity_time = Column(DateTime(timezone=True), nullable=True)
    
    # Location/Security
    ip_address = Column(INET, nullable=True) # or String if INET causes issues
    location = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
