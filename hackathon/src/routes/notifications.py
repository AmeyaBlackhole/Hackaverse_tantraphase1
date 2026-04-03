from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
from ..auth import get_api_key, get_current_user_id
from ..database import get_db
from ..db_models import COLLECTIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str
    related_id: Optional[str] = None

class NotificationUpdate(BaseModel):
    read: bool

@router.post("")
async def create_notification(notification: NotificationCreate, api_key: str = Depends(get_api_key)):
    """Create a new notification"""
    db = get_db()
    
    notification_data = {
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "related_id": notification.related_id,
        "read": False,
        "created_at": datetime.now().isoformat()
    }
    
    if db is not None:
        result = db[COLLECTIONS["notifications"]].insert_one(notification_data)
        notification_data["_id"] = str(result.inserted_id)
    
    logger.info(f"Created notification for user {notification.user_id}")
    
    return {
        "success": True,
        "message": "Notification created",
        "data": notification_data
    }


class AnnouncementCreate(BaseModel):
    title: str
    message: str
    target: Optional[str] = "all"
    created_by: Optional[str] = None


@router.post("/announcements")
async def create_announcement(announcement: AnnouncementCreate, api_key: str = Depends(get_api_key)):
    """Create a new announcement for participants/judges"""
    db = get_db()
    announcement_data = {
        "title": announcement.title,
        "message": announcement.message,
        "target": announcement.target,
        "created_by": announcement.created_by,
        "created_at": datetime.now().isoformat()
    }

    if db is not None:
        result = db[COLLECTIONS.get("announcements", "announcements")].insert_one(announcement_data)
        announcement_data["_id"] = str(result.inserted_id)

    logger.info(f"Created announcement: {announcement.title}")

    return {
        "success": True,
        "message": "Announcement created",
        "data": announcement_data
    }


@router.get("/announcements")
async def get_announcements():
    """Get all announcements (public endpoint)"""
    db = get_db()
    announcements = []

    if db is not None:
        cursor = db[COLLECTIONS.get("announcements", "announcements")].find().sort("created_at", -1)
        announcements = list(cursor)
        for ann in announcements:
            ann["_id"] = str(ann.get("_id", ""))

    return {"success": True, "data": announcements}


@router.get("/user/{user_id}")
async def get_user_notifications(user_id: str, unread_only: bool = False, current_user_id: str = Depends(get_current_user_id)):
    """Get notifications for a user (user can only access their own)"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db = get_db()
    notifications = []
    
    if db is not None:
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        
        cursor = db[COLLECTIONS["notifications"]].find(query).sort("created_at", -1)
        notifications = list(cursor)
        for n in notifications:
            n["_id"] = str(n["_id"])
    
    return {
        "success": True,
        "data": notifications,
        "unread_count": sum(1 for n in notifications if not n.get("read", False))
    }

@router.get("/me")
async def get_my_notifications(unread_only: bool = False, user_id: str = Depends(get_current_user_id)):
    """Get current user's notifications"""
    db = get_db()
    notifications = []
    
    if db is not None:
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        
        cursor = db[COLLECTIONS["notifications"]].find(query).sort("created_at", -1)
        notifications = list(cursor)
        for n in notifications:
            n["_id"] = str(n["_id"])
    
    return {
        "success": True,
        "data": notifications,
        "unread_count": sum(1 for n in notifications if not n.get("read", False))
    }

@router.patch("/{notification_id}")
async def update_notification(notification_id: str, update: NotificationUpdate, user_id: str = Depends(get_current_user_id)):
    """Mark notification as read/unread (user can only update their own)"""
    db = get_db()
    
    if db is not None:
        from bson import ObjectId
        try:
            notification = db[COLLECTIONS["notifications"]].find_one({"_id": ObjectId(notification_id)})
            if not notification:
                raise HTTPException(status_code=404, detail="Notification not found")
            
            if notification.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            result = db[COLLECTIONS["notifications"]].update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"read": update.read}}
            )
            
            if result.modified_count > 0:
                notification = db[COLLECTIONS["notifications"]].find_one({"_id": ObjectId(notification_id)})
                notification["_id"] = str(notification["_id"])
                return {
                    "success": True,
                    "message": "Notification updated",
                    "data": notification
                }
        except Exception as e:
            logger.error(f"Error updating notification: {e}")
    
    raise HTTPException(status_code=404, detail="Notification not found")

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a notification (user can only delete their own)"""
    db = get_db()
    
    if db is not None:
        from bson import ObjectId
        try:
            notification = db[COLLECTIONS["notifications"]].find_one({"_id": ObjectId(notification_id)})
            if not notification:
                raise HTTPException(status_code=404, detail="Notification not found")
            
            if notification.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            result = db[COLLECTIONS["notifications"]].delete_one({"_id": ObjectId(notification_id)})
            if result.deleted_count > 0:
                return {
                    "success": True,
                    "message": "Notification deleted"
                }
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
    
    raise HTTPException(status_code=404, detail="Notification not found")
