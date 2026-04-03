import uuid
from datetime import datetime

def log_event(db, eventType, message, userId=None, hackathonId=None, teamId=None):
    """Log an activity event to the database"""
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": eventType,
        "message": message,
        "userId": userId,
        "hackathonId": hackathonId,
        "teamId": teamId,
        "timestamp": datetime.utcnow()
    }
    
    try:
        db["activity_events"].insert_one(event)
    except Exception as e:
        print(f"Error logging event: {e}")
    
    return event
