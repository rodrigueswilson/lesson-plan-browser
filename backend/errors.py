"""
Custom error handlers for FastAPI application.
"""

import traceback
from typing import List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.telemetry import logger


class ValidationError(HTTPException):
    """Raised when JSON validation fails."""

    def __init__(self, errors: List[dict]):
        super().__init__(
            status_code=400, detail={"error": "Validation failed", "errors": errors}
        )


class RenderError(HTTPException):
    """Raised when DOCX rendering fails."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(status_code=500, detail={"error": message, "detail": detail})


class TemplateNotFoundError(HTTPException):
    """Raised when template file is not found."""

    def __init__(self, template_path: str):
        super().__init__(
            status_code=404,
            detail={"error": "Template not found", "template_path": template_path},
        )


async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


async def render_error_handler(request: Request, exc: RenderError):
    """Handle rendering errors."""
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    # Log the full traceback
    error_trace = traceback.format_exc()
    logger.error(
        "unexpected_error",
        extra={
            "path": str(request.url),
            "method": request.method,
            "error": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": error_trace,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )
