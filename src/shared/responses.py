"""
Common Response Models
Standard API response formats used across modules.
"""
from pydantic import BaseModel
from typing import Optional, Any


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None


class SuccessResponse(BaseModel):
    """Success response for operations."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
