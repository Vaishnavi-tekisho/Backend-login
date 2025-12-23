"""
Custom Exceptions
Application-wide exception definitions.
"""
from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    """Raised when a user is not found."""
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class InvalidCredentialsError(HTTPException):
    """Raised when credentials are invalid."""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenError(HTTPException):
    """Raised when token is invalid or expired."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InactiveUserError(HTTPException):
    """Raised when user is inactive."""
    def __init__(self, detail: str = "Inactive user"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DuplicateEmailError(HTTPException):
    """Raised when email already exists."""
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class InvalidOTPError(HTTPException):
    """Raised when OTP is invalid or expired."""
    def __init__(self, detail: str = "Invalid or expired OTP"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class PasswordResetError(HTTPException):
    """Raised when password reset fails."""
    def __init__(self, detail: str = "Password reset failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
