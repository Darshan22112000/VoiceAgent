"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.config import DEFAULT_TIMEZONE
import re
import pytz


class AppointmentDetails(BaseModel):
    """Validated appointment details with comprehensive error checking."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name of client")
    phone: str | int = Field(..., min_length=5, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address for calendar invite")
    date: str = Field(..., description="Session date in YYYY-MM-DD format")
    time: str = Field(..., description="Session time in HH:MM 24-hour format")
    purpose: Optional[str] = Field(default="Discovery Session", max_length=200)
    timezone: str = Field(default=DEFAULT_TIMEZONE, description="IANA timezone string")
    duration_minutes: str | int = Field(default=30, ge=15, le=480, description="Duration in minutes (15-480)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone contains only digits, spaces, hyphens, parentheses, +."""

        if not re.match(r"^[\d\s\-\+\(\)]{10,20}$", str(v)):
            raise ValueError("Invalid phone format")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Validate date is in YYYY-MM-DD format and is in the future."""
        try:
            date_obj = datetime.strptime(v, "%Y-%m-%d").date()
            if date_obj < datetime.now().date():
                raise ValueError("Date must be in the future")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    @field_validator("time")
    @classmethod
    def validate_time(cls, v):
        """Validate time is in HH:MM 24-hour format."""
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format (24-hour)")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone is a valid IANA timezone."""
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "+1 (555) 123-4567",
                "email": "john@example.com",
                "date": "2026-03-15",
                "time": "14:00",
                "purpose": "AI Transformation Discussion",
                "timezone": "America/Los_Angeles",
                "duration_minutes": 60,
            }
        }


class ToolCallFunction(BaseModel):
    """Represents a function call from VAPI."""
    name: str
    arguments: dict | str  # VAPI sometimes sends as string


class ToolCall(BaseModel):
    """Represents a tool call wrapper."""
    function: ToolCallFunction


class VapiToolRequest(BaseModel):
    """Represents a VAPI tool invocation request."""
    toolCall: ToolCall


class GoogleTokenData(BaseModel):
    """Google OAuth token data (for storage)."""
    token: str
    refresh_token: Optional[str] = None
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list[str]
    expires_in: Optional[int] = None



class CallResponse(BaseModel):
    """Response from call start endpoints."""
    call_id: str
    assistant_id: Optional[str] = None
    web_call_url: str

