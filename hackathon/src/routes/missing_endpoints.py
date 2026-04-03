# Additional Missing Endpoints - Complete Implementation
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging
from ..auth import get_api_key
from ..database import get_db
from ..db_models import COLLECTIONS

logger = logging.getLogger(__name__)

# ============================================================================
# REWARD ENDPOINTS
# ============================================================================

reward_router = APIRouter(prefix="/reward", tags=["reward"])

@reward_router.get("")
async def get_rewards(api_key: str = Depends(get_api_key)):
    """
    Get all rewards (admin endpoint)
    """
    logger.info("[GET_REWARDS] Starting")
    
    try:
        db = get_db()
        if db is None:
            logger.error("[GET_REWARDS] Database unavailable")
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get rewards from database
        rewards = list(db[COLLECTIONS.get("rewards", "rewards")].find({}))
        
        # Convert ObjectIds to strings
        for reward in rewards:
            reward["_id"] = str(reward.get("_id", ""))
        
        logger.info(f"[GET_REWARDS] Success - found {len(rewards)} rewards")
        
        return {
            "success": True,
            "data": rewards
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_REWARDS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get rewards")

# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

leaderboard_router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@leaderboard_router.get("/{hackathon_id}")
async def get_leaderboard(hackathon_id: str, limit: int = 50, api_key: str = Depends(get_api_key)):
    """
    Get leaderboard for a hackathon (public endpoint)
    
    - **hackathon_id**: Hackathon ID
    - **limit**: Maximum number of results (default: 50)
    """
    logger.info(f"[GET_LEADERBOARD] Starting - hackathon_id={hackathon_id}")
    
    try:
        db = get_db()
        if db is None:
            logger.error("[GET_LEADERBOARD] Database unavailable")
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Limit max results
        limit = min(limit, 100)
        
        # Get judgments for this hackathon
        judgments = list(db[COLLECTIONS["judgments"]].find({
            "hackathon_id": hackathon_id
        }).sort("total_score", -1).limit(limit))
        
        # Build leaderboard
        leaderboard = []
        for rank, judgment in enumerate(judgments, start=1):
            leaderboard.append({
                "rank": rank,
                "team_id": judgment.get("team_id", "unknown"),
                "total_score": judgment.get("total_score", 0),
                "clarity": judgment.get("clarity", 0),
                "quality": judgment.get("quality", 0),
                "innovation": judgment.get("innovation", 0),
                "confidence": judgment.get("confidence", 0.5)
            })
        
        logger.info(f"[GET_LEADERBOARD] Success - {len(leaderboard)} teams")
        
        return {
            "success": True,
            "data": leaderboard
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_LEADERBOARD] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")

# ============================================================================
# JUDGING SCORES ENDPOINTS
# ============================================================================

judging_router = APIRouter(prefix="/judging", tags=["judging"])

@judging_router.get("/scores/{project_id}")
async def get_judging_scores(project_id: str):
    """
    Get judging scores for a project
    
    - **project_id**: Project/Submission ID
    """
    logger.info(f"[GET_SCORES] Starting - project_id={project_id}")
    
    try:
        db = get_db()
        if db is None:
            logger.error("[GET_SCORES] Database unavailable")
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get judgments for this project
        judgments = list(db[COLLECTIONS["judgments"]].find({
            "submission_hash": project_id
        }).sort("timestamp", -1))
        
        if not judgments:
            logger.warning(f"[GET_SCORES] No judgments found - project_id={project_id}")
            return {
                "success": True,
                "data": []
            }
        
        # Build scores response
        scores = []
        for judgment in judgments:
            scores.append({
                "version": judgment.get("version", 1),
                "total_score": judgment.get("total_score", 0),
                "clarity": judgment.get("clarity", 0),
                "quality": judgment.get("quality", 0),
                "innovation": judgment.get("innovation", 0),
                "confidence": judgment.get("confidence", 0.5),
                "timestamp": judgment.get("timestamp")
            })
        
        logger.info(f"[GET_SCORES] Success - {len(scores)} scores")
        
        return {
            "success": True,
            "data": scores
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_SCORES] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get scores")

# ============================================================================
# HACKATHON ENDPOINTS
# ============================================================================

hackathon_router = APIRouter(tags=["hackathons"])

class HackathonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    start_date: str
    end_date: str
    min_team_size: int = Field(ge=1)
    max_team_size: int = Field(ge=1)
    status: Optional[str] = "active"

class HackathonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None

@hackathon_router.get("")
async def get_all_hackathons(api_key: str = Depends(get_api_key)):
    """
    Get all hackathons
    """
    logger.info("[GET_ALL_HACKATHONS] Starting")
    
    try:
        db = get_db()
        if db is None:
            logger.error("[GET_ALL_HACKATHONS] Database unavailable")
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get all hackathons
        hackathons = list(db[COLLECTIONS["hackathons"]].find({}))
        
        # Convert ObjectIds to strings
        for h in hackathons:
            h["_id"] = str(h.get("_id", ""))
        
        logger.info(f"[GET_ALL_HACKATHONS] Success - found {len(hackathons)} hackathons")
        
        return {
            "success": True,
            "data": hackathons
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET_ALL_HACKATHONS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get hackathons")

@hackathon_router.post("")
async def create_hackathon(data: HackathonCreate, api_key: str = Depends(get_api_key)):
    """
    Create a new hackathon (admin only)
    
    - **name**: Hackathon name
    - **description**: Description
    - **start_date**: Start date
    - **end_date**: End date
    - **min_team_size**: Minimum team size
    - **max_team_size**: Maximum team size
    """
    logger.info(f"[CREATE_HACKATHON] Starting - name={data.name}")
    
    try:
        db = get_db()
        print(f"DB object: {db}")
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        from uuid import uuid4
        hackathon_id = f"hackathon_{uuid4()}"
        print(f"Generated hackathon_id: {hackathon_id}")
        
        hackathon = {
            "id": hackathon_id,
            "hackathon_id": hackathon_id,
            "name": data.name,
            "description": data.description,
            "start_date": data.start_date,
            "end_date": data.end_date,
            "min_team_size": data.min_team_size,
            "max_team_size": data.max_team_size,
            "status": data.status or "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        print(f"Hackathon data: {hackathon}")
        
        result = db[COLLECTIONS["hackathons"]].insert_one(hackathon)
        print(f"Insert result: {result}")
        logger.info(f"[CREATE_HACKATHON] Success - id={hackathon_id}")
        
        return {
            "success": True,
            "message": "Hackathon created successfully",
            "data": {
                "hackathon_id": hackathon_id,
                "name": data.name,
                "status": data.status or "active",
                "created_at": hackathon["created_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CREATE_HACKATHON] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create hackathon")

@hackathon_router.patch("/{hackathon_id}")
async def update_hackathon(hackathon_id: str, data: HackathonUpdate, api_key: str = Depends(get_api_key)):
    """
    Update hackathon details (admin only)
    
    - **hackathon_id**: Hackathon ID
    - **name**: New name
    - **description**: New description
    - **status**: New status
    """
    logger.info(f"[UPDATE_HACKATHON] Starting - hackathon_id={hackathon_id}")
    
    try:
        db = get_db()
        if db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get hackathon
        hackathon = db[COLLECTIONS["hackathons"]].find_one({"hackathon_id": hackathon_id})
        if not hackathon:
            logger.error(f"[UPDATE_HACKATHON] Hackathon not found - id={hackathon_id}")
            raise HTTPException(status_code=404, detail="Hackathon not found")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if data.name:
            update_data["name"] = data.name
        if data.description:
            update_data["description"] = data.description
        if data.start_date:
            update_data["start_date"] = data.start_date
        if data.end_date:
            update_data["end_date"] = data.end_date
        if data.status:
            update_data["status"] = data.status
        
        # Update hackathon
        result = db[COLLECTIONS["hackathons"]].update_one(
            {"hackathon_id": hackathon_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            logger.warning(f"[UPDATE_HACKATHON] No changes made")
            raise HTTPException(status_code=400, detail="No changes were made")
        
        logger.info(f"[UPDATE_HACKATHON] Success - id={hackathon_id}")
        
        return {
            "success": True,
            "message": "Hackathon updated successfully",
            "data": {"hackathon_id": hackathon_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPDATE_HACKATHON] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update hackathon")

# @hackathon_router.post("/join")
