from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from ..schemas.response import APIResponse
import logging

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: Exception):
    """Handle general API exceptions."""
    # Clean the exception message to avoid encoding issues
    error_msg = str(exc).encode('ascii', 'ignore').decode('ascii')
    logger.error(f"Unhandled exception: {error_msg}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message=f"Internal server error: {error_msg}",
            data=None
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with clear messages."""
    errors = exc.errors()
    
    # Format validation errors into user-friendly messages
    formatted_errors = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = str(error.get("msg", "Unknown error")).encode('ascii', 'ignore').decode('ascii')
        error_type = error.get("type", "")
        
        # Create a clear error message
        if "missing" in error_type or "required" in error_type:
            formatted_errors.append(f"Field '{field}' is required but was not provided")
        elif "type_error" in error_type:
            formatted_errors.append(f"Field '{field}' has an invalid type: {msg}")
        elif "value_error" in error_type:
            formatted_errors.append(f"Field '{field}' validation failed: {msg}")
        else:
            formatted_errors.append(f"Field '{field}': {msg}")
    
    error_message = "; ".join(formatted_errors) if formatted_errors else "Validation failed"
    
    logger.warning(f"Validation error for {request.url.path}: {error_message}")
    
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False,
            message=error_message,
            data={"errors": formatted_errors} if formatted_errors else None
        ).dict()
    )