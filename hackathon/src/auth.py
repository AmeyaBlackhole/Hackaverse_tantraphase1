from fastapi import Depends, HTTPException, Header
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
import os
import json
import base64
import logging

# API Key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_current_user_id(authorization: str = Header(None)) -> str:
    """Extract user_id from simple JWT-like bearer token."""
    logger = logging.getLogger(__name__)
    
    if not authorization:
        logger.warning("[AUTH] Missing Authorization header")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        logger.warning(f"[AUTH] Invalid Authorization format: {authorization[:20]}...")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Authorization format")

    token = authorization.split(" ", 1)[1]
    logger.debug(f"[AUTH] Token received: {token[:20]}...")
    
    parts = token.split('.')
    if len(parts) < 2:
        logger.warning(f"[AUTH] Invalid token format - not enough parts: {len(parts)}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    payload_b64 = parts[1]
    try:
        padding = '=' * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode('utf-8'))
        logger.debug(f"[AUTH] Payload parsed: {payload}")
    except Exception as e:
        logger.error(f"[AUTH] Failed to decode token payload: {str(e)}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Failed to decode token payload")

    user_id = payload.get('user_id')
    if not user_id:
        logger.warning(f"[AUTH] Invalid token payload - no user_id: {payload}")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    logger.info(f"[AUTH] User authenticated: {user_id}")
    return user_id

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    """Validate API key for protected endpoints"""
    expected_key = os.getenv("API_KEY", "default_key")
    if api_key_header == expected_key:
        return api_key_header
    else:
        logger.warning(f"[API_KEY] Invalid API key provided: {api_key_header[:10]}... (expected: {expected_key[:10]}...)")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )