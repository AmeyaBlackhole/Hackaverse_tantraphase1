# src/routes/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
import logging
import secrets
import hashlib
from ..database import get_db
from ..auth import get_current_user_id
from ..db_models import COLLECTIONS
from ..schemas.response import APIResponse
import os

logger = logging.getLogger(__name__)

print("Auth routes loaded")

router = APIRouter(tags=["auth"])

# ============================================================================
# SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    role: Optional[str] = Field(default="participant", pattern="^(admin|participant|judge)$")

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored hash"""
    return hash_password(password) == stored_hash

def generate_token(length: int = 32) -> str:
    """Generate a random token"""
    return secrets.token_urlsafe(length)

def create_jwt_token(user_id: str, email: str) -> str:
    """Create a simple JWT-like token (base format: header.payload.signature)"""
    import json
    import base64
    
    # Header
    header = json.dumps({"alg": "HS256", "typ": "JWT"})
    # Payload
    payload = json.dumps({
        "user_id": user_id,
        "email": email,
        "iat": datetime.now().timestamp(),
        "exp": (datetime.now() + timedelta(hours=24)).timestamp()
    })
    # Simple signature
    signature = generate_token(16)
    
    header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    sig_b64 = base64.urlsafe_b64encode(signature.encode()).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def get_user_response(user_doc: dict) -> dict:
    """Format user document for response"""
    return {
        "id": str(user_doc.get("_id", "")),
        "user_id": user_doc.get("user_id", ""),
        "email": user_doc.get("email", ""),
        "name": user_doc.get("name", ""),
        "role": user_doc.get("role", "participant"),
        "profile_completion": user_doc.get("profile_completion", 0),
        "team_id": user_doc.get("team_id", None),
        "created_at": user_doc.get("created_at", datetime.now().isoformat())
    }

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/register", summary="Register a new user")
async def register(request: RegisterRequest):
    """
    Register a new user account
    
    - **name**: Full name (2-100 characters)
    - **email**: Valid email address
    - **password**: Password (min 6 characters)
    - **role**: User role (admin, participant, judge) - default: participant
    """
    try:
        db = get_db()
        if db is None:
            logger.warning(f"[REGISTER] Database unavailable - using in-memory storage for {request.email}")
            user_id = f"user_{datetime.now().timestamp()}"
            access_token = create_jwt_token(user_id, request.email)
            refresh_token = generate_token(32)
            
            user_data = {
                "user_id": user_id,
                "email": request.email,
                "name": request.name,
                "role": request.role,
                "_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "message": "User registered successfully (in-memory)",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": get_user_response(user_data)
                }
            }
        
        # Check if user already exists
        existing_user = db[COLLECTIONS["users"]].find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user
        user_id = f"user_{datetime.now().timestamp()}"
        password_hash = hash_password(request.password)
        
        user_data = {
            "user_id": user_id,
            "email": request.email,
            "name": request.name,
            "role": request.role,
            "password_hash": password_hash,
            "profile_completion": 0,
            "skills": [],
            "bio": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = db[COLLECTIONS["users"]].insert_one(user_data)
        
        # Generate tokens
        access_token = create_jwt_token(user_id, request.email)
        refresh_token = generate_token(32)
        
        # Store refresh token
        db[COLLECTIONS["sessions"]].insert_one({
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        })
        
        user_data["_id"] = str(result.inserted_id)
        
        logger.info(f"User registered: {request.email} (user_id: {user_id})")
        logger.debug(f"[REGISTER] Access token generated: {access_token[:20]}...")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": get_user_response(user_data)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", summary="Login user")
async def login(request: LoginRequest):
    """
    Login with email and password
    
    - **email**: User email
    - **password**: User password
    """
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Find user by email
        user = db[COLLECTIONS["users"]].find_one({"email": request.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(user.get("password_hash", ""), request.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate tokens
        user_id = user.get("user_id", "")
        access_token = create_jwt_token(user_id, request.email)
        refresh_token = generate_token(32)
        
        # Store refresh token
        db[COLLECTIONS["sessions"]].insert_one({
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        })
        
        logger.info(f"User logged in: {request.email} (user_id: {user_id})")
        logger.debug(f"[LOGIN] Access token generated: {access_token[:20]}...")
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": get_user_response(user)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh", summary="Refresh access token", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token from login/register
    """
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Find session with refresh token
        session = db[COLLECTIONS["sessions"]].find_one({
            "refresh_token": request.refresh_token
        })
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(session.get("expires_at", datetime.now().isoformat()))
        if datetime.now() > expires_at:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        
        # Get user
        user = db[COLLECTIONS["users"]].find_one({"user_id": session["user_id"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Generate new access token
        access_token = create_jwt_token(user.get("user_id", ""), user.get("email", ""))
        new_refresh_token = generate_token(32)
        
        # Update session
        db[COLLECTIONS["sessions"]].update_one(
            {"_id": session["_id"]},
            {"$set": {"refresh_token": new_refresh_token}}
        )
        
        logger.info(f"Token refreshed for user: {user.get('email')}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user=get_user_response(user)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout", summary="Logout user")
async def logout(refresh_token: str):
    """
    Logout user by invalidating refresh token
    
    - **refresh_token**: Refresh token to invalidate
    """
    try:
        db = get_db()
        if db is not None:
            result = db[COLLECTIONS["sessions"]].delete_one({
                "refresh_token": refresh_token
            })
            
            if result.deleted_count > 0:
                logger.info("User logged out")
        
        return APIResponse(
            success=True,
            message="Logged out successfully",
            data=None
        )
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return APIResponse(
            success=False,
            message="Logout failed",
            data=None
        )

@router.get("/me", summary="Get current user", dependencies=[])
async def get_current_user(authorization: str = Header(None)):
    """
    Get current authenticated user (requires Bearer token in Authorization header)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract user_id from token
    user_id = get_current_user_id(authorization)
    
    # Fetch user from database
    db = get_db()
    if db is None:
        # For development/testing, return basic user info from token
        logger.warning("[GET_ME] Database unavailable, returning token-based user info")
        return APIResponse(
            success=True,
            message="User retrieved successfully (DB unavailable)",
            data={
                "user_id": user_id,
                "email": "user@example.com",
                "name": "Test User",
                "role": "participant"
            }
        )
    
    user = db[COLLECTIONS["users"]].find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return APIResponse(
        success=True,
        message="User retrieved successfully",
        data=get_user_response(user)
    )
