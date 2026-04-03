# Configure logging FIRST, before any other imports that might interfere
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Force load .env from correct path BEFORE any other imports
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import time
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from .schemas.response import APIResponse

# Import database module
from .database import connect_to_db, close_db, get_db_status, DB_AVAILABLE

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="HackaVerse API",
    description="Hackathon management platform - Production",
    version="v5.0",
    contact={"name": "HackaVerse Team", "email": "team@hackaverse.com"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    """Startup event - connect to database"""
    print("\n" + "="*70)
    print("[STARTUP] HackaVerse Backend Starting...")
    print("="*70)
    
    # Connect to database
    success = connect_to_db()
    
    if success:
        print("\n[SUCCESS] Backend Ready!")
        print("   - Database: Connected")
        print("   - API Docs: http://localhost:8000/docs")
    else:
        print("\n[WARNING] Backend Started in Degraded Mode")
        print("   - Database: NOT Connected")
        print("   - Some features may not work")
    
    print("="*70 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - close database connection"""
    close_db()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add security middleware FIRST
from .middleware import SecurityMiddleware
app.add_middleware(SecurityMiddleware)

# ============================================================================
# CORE ROUTERS
# ============================================================================

from .routes.auth_routes import router as auth_router
from .routes.admin import router as admin_router
from .routes.hackathons import router as hackathons_router, public_router as hackathons_public_router
from .routes.teams_crud import router as teams_crud_router
from .routes.submissions import router as submissions_router
from .routes.leaderboard import router as leaderboard_router
from .routes.system import router as system_router
from .routes.notifications import router as notifications_router
from .routes.judge import router as judge_router
from .routes.judge_review import router as judge_review_router
from .routes.team_members_management import router as team_members_router
from .routes.judge_invitations import router as judge_invitations_router
from .routes.mcp import router as mcp_router

app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router)
app.include_router(hackathons_public_router)
app.include_router(hackathons_router)
app.include_router(teams_crud_router)
app.include_router(submissions_router)
app.include_router(leaderboard_router)
app.include_router(system_router)
app.include_router(notifications_router)
app.include_router(judge_router)
app.include_router(judge_review_router)
app.include_router(judge_invitations_router)
app.include_router(team_members_router)
app.include_router(mcp_router)

# Register error handlers
from .middleware_handlers.error_handler import api_exception_handler, validation_exception_handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, api_exception_handler)

# ============================================================================
# ESSENTIAL SYSTEM ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "HackaVerse API",
        "version": "v5.0",
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for frontend"""
    status = get_db_status()
    
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={
            "status": "ok" if DB_AVAILABLE else "degraded",
            "database": status["status"],
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"[MAIN] Starting FastAPI server")
    logger.info(f"[MAIN] Host: {host}")
    logger.info(f"[MAIN] Port: {port}")
    logger.info(f"[MAIN] Environment: {os.getenv('ENV', 'development')}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
