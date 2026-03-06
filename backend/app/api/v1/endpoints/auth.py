"""
Authentication Endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import os

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    User login endpoint
    Returns JWT token for authentication
    """
    # Mock authentication - replace with real authentication in production
    if credentials.email and credentials.password:
        # In production, verify against database
        mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token"
        
        return {
            "access_token": mock_token,
            "token_type": "bearer",
            "user": {
                "id": "user_123",
                "email": credentials.email,
                "full_name": "Security Admin",
                "role": "admin"
            }
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password"
    )


@router.post("/register")
async def register(user_data: RegisterRequest):
    """
    User registration endpoint
    """
    # Mock registration - replace with real database insertion
    return {
        "message": "User registered successfully",
        "user": {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "organization": user_data.organization
        }
    }


@router.post("/logout")
async def logout():
    """
    User logout endpoint
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user():
    """
    Get current user information
    """
    # Mock user data - replace with real JWT token verification
    return {
        "id": "user_123",
        "email": "admin@sentinelai.com",
        "full_name": "Security Admin",
        "role": "admin",
        "organization": "SentinelAI"
    }
