"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class RecaptchaRequest(BaseModel):
    """Request model for submitting reCAPTCHA task."""
    sitekey: str = Field(..., description="reCAPTCHA site key", min_length=1)
    pageurl: str = Field(..., description="URL of the page with reCAPTCHA")
    proxy: Optional[str] = Field(None, description="Proxy in format protocol://user:pass@host:port")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sitekey": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
                "pageurl": "https://www.google.com/recaptcha/api2/demo",
                "proxy": "http://user:pass@proxy.example.com:8080"
            }
        }
    }


class RecaptchaResponse(BaseModel):
    """Response model for task submission."""
    taskId: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "taskId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing"
            }
        }
    }


class TaskStatusResponse(BaseModel):
    """Response model for task status query."""
    status: TaskStatus = Field(..., description="Current task status")
    taskId: str = Field(..., description="Task identifier")
    token: Optional[str] = Field(None, description="reCAPTCHA token (if ready)")
    solveTime: Optional[float] = Field(None, description="Time taken to solve in seconds")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ready",
                "taskId": "550e8400-e29b-41d4-a716-446655440000",
                "token": "03AGdBq25...",
                "solveTime": 12.5
            }
        }
    }


class TaskModel(BaseModel):
    """Database model for tasks."""
    task_id: str
    sitekey: str
    pageurl: str
    proxy: Optional[str]
    status: TaskStatus
    token: Optional[str] = None
    solve_time: Optional[float] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
