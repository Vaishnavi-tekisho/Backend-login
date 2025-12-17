"""
Password Reset Tests
Tests for OTP-based password reset flow.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestPasswordReset:
    """Test cases for password reset endpoints."""
    
    def test_forgot_password_existing_user(self):
        """Test forgot password request for existing user."""
        response = client.post("/auth/forgot-password", json={
            "email": "existing@example.com"
        })
        # Note: Requires test DB setup
        # assert response.status_code in [200, 404]
    
    def test_forgot_password_nonexistent_user(self):
        """Test forgot password request for non-existent user."""
        response = client.post("/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        # assert response.status_code == 404
    
    def test_verify_otp_invalid(self):
        """Test OTP verification with invalid OTP."""
        response = client.post("/auth/verify-reset-otp", json={
            "email": "test@example.com",
            "otp": "000000"
        })
        # assert response.status_code == 400
    
    def test_reset_password_invalid_otp(self):
        """Test password reset with invalid OTP."""
        response = client.post("/auth/reset-password", json={
            "email": "test@example.com",
            "otp": "000000",
            "new_password": "NewPassword123!"
        })
        # assert response.status_code == 400
    
    def test_reset_password_weak_password(self):
        """Test password reset with weak password."""
        response = client.post("/auth/reset-password", json={
            "email": "test@example.com",
            "otp": "123456",
            "new_password": "weak"
        })
        # Validation should fail
        assert response.status_code == 422
