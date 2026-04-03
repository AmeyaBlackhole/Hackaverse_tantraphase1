# src/database.py
# Simple MongoDB connection management for HackaVerse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# CRITICAL: Load .env FIRST
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)

# Global database connection variables
client = None
db = None
DB_AVAILABLE = False


def connect_to_db():
    """Connect to MongoDB - Simple and Clear"""
    global client, db, DB_AVAILABLE
    
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("BUCKET_DB_NAME", "hackaverse_db")
    
    # Check if URI is set
    if not MONGODB_URI:
        print("\n❌ ERROR: MONGODB_URI environment variable is NOT SET")
        print("   Please add MONGODB_URI to your .env file")
        DB_AVAILABLE = False
        return False
    
    # Check if URI is valid format
    if not MONGODB_URI.startswith(("mongodb://", "mongodb+srv://")):
        print(f"\n❌ ERROR: MONGODB_URI has invalid format")
        print(f"   Expected: mongodb:// or mongodb+srv://")
        print(f"   Got: {MONGODB_URI[:50]}...")
        DB_AVAILABLE = False
        return False
    
    try:
        print(f"\n🔄 Connecting to MongoDB...")
        print(f"   Database: {DB_NAME}")
        print(f"   URI: {MONGODB_URI[:50]}...")
        
        # Create connection
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test connection with ping
        client.admin.command("ping")
        
        # Set database
        db = client[DB_NAME]
        
        # Get collections count
        collections = db.list_collection_names()
        
        print(f"\n✅ MongoDB Connected Successfully!")
        print(f"   Database: {DB_NAME}")
        print(f"   Collections: {len(collections)}")
        print()
        
        DB_AVAILABLE = True
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB Connection Failed!")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print()
        DB_AVAILABLE = False
        return False


def close_db():
    """Close database connection"""
    global client, db
    if client is not None:
        try:
            client.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning(f"Error closing database: {e}")
        finally:
            db = None
            client = None


def get_db():
    """Get database object - returns None if not connected"""
    global db
    return db


def get_db_status():
    """Get database status for health checks"""
    global DB_AVAILABLE
    
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("BUCKET_DB_NAME", "hackaverse_db")
    
    return {
        "connected": DB_AVAILABLE,
        "database": DB_NAME,
        "uri_set": bool(MONGODB_URI),
        "status": "✅ Connected" if DB_AVAILABLE else "❌ Not Connected"
    }
