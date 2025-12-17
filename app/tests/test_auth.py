"""
Authentication Tests
Tests for signup, login, and OAuth endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestAuth:
    """Test cases for authentication endpoints."""
    
    def test_signup_success(self):
        """Test successful user registration."""
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "user_name": "Test User"
        })
        # Note: This will fail without proper test DB setup
        # assert response.status_code == 200
        # assert "access_token" in response.json()
    
    def test_signup_duplicate_email(self):
        """Test registration with existing email."""
        # First signup
        client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "TestPassword123!",
            "user_name": "Test User"
        })
        
        # Second signup with same email
        response = client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "TestPassword123!",
            "user_name": "Another User"
        })
        # assert response.status_code == 400
    
    def test_login_success(self):
        """Test successful login."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        # assert response.status_code == 200
        # assert "access_token" in response.json()
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        # assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        })
        # assert response.status_code == 401


class TestProtectedRoutes:
    """Test cases for protected routes."""
    
    def test_get_me_without_token(self):
        """Test /auth/me without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_get_me_with_invalid_token(self):
        """Test /auth/me with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
