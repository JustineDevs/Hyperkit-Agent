"""
Authentication routes for HyperKit AI Agent production system.

This module provides FastAPI routes for user authentication including
registration, login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from ..db.connection import get_db
from ..db.models import User
from .jwt import get_jwt_auth, get_api_key_manager

logger = logging.getLogger(__name__)

# FastAPI router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()


# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class APIKeyResponse(BaseModel):
    api_key: str
    message: str


class UserProfile(BaseModel):
    id: str
    email: str
    tier: str
    is_active: bool
    created_at: str


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    jwt_auth = get_jwt_auth()
    
    # Verify token
    payload = jwt_auth.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    jwt_auth = get_jwt_auth()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = jwt_auth.hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        tier="free"
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create tokens
        tokens = jwt_auth.create_token_pair(
            user_id=str(user.id),
            email=user.email,
            tier=user.tier
        )
        
        logger.info(f"User registered: {user.email}")
        return tokens
        
    except Exception as e:
        db.rollback()
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return tokens."""
    jwt_auth = get_jwt_auth()
    
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not jwt_auth.verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create tokens
    tokens = jwt_auth.create_token_pair(
        user_id=str(user.id),
        email=user.email,
        tier=user.tier
    )
    
    logger.info(f"User logged in: {user.email}")
    return tokens


@router.post("/refresh", response_model=dict)
async def refresh_token(
    token_data: RefreshTokenRequest
):
    """Refresh access token using refresh token."""
    jwt_auth = get_jwt_auth()
    
    new_tokens = jwt_auth.refresh_access_token(token_data.refresh_token)
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return new_tokens


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should discard tokens)."""
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        tier=current_user.tier,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate API key for current user."""
    api_key_manager = get_api_key_manager()
    
    # Generate new API key
    api_key = api_key_manager.generate_api_key()
    hashed_api_key = api_key_manager.hash_api_key(api_key)
    
    # Update user with new API key
    current_user.api_key = hashed_api_key
    db.commit()
    
    logger.info(f"API key generated for user: {current_user.email}")
    return APIKeyResponse(
        api_key=api_key,
        message="API key generated successfully. Store it securely."
    )


@router.delete("/api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke current user's API key."""
    current_user.api_key = None
    db.commit()
    
    logger.info(f"API key revoked for user: {current_user.email}")
    return {"message": "API key revoked successfully"}
