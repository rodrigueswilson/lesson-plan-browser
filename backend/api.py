"""
FastAPI Backend for Bilingual Lesson Plan Builder.

Provides REST API endpoints for:
- JSON validation
- DOCX rendering
- Progress streaming (SSE)
- Health checks
"""

import gc
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# FORCE UTF-8 ENCODING FOR STDOUT/STDERR (Windows Fix)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.database import get_db
from backend.errors import (
    RenderError,
    ValidationError,
    general_exception_handler,
    render_error_handler,
    validation_error_handler,
)
from backend.rate_limiter import setup_rate_limiting
from backend.routers.analytics import router as analytics_router
from backend.routers.core import router as core_router
from backend.routers.health import router as health_router
from backend.routers.lesson_mode import router as lesson_mode_router
from backend.routers.lesson_steps import router as lesson_steps_router
from backend.routers.plans import router as plans_router
from backend.routers.process_week import router as process_week_router
from backend.routers.settings import router as settings_router
from backend.routers.users import router as users_router
from backend.telemetry import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup and cleanup on shutdown."""
    try:
        db = get_db()
        if hasattr(db, "engine"):
            logger.info("Database initialized successfully (SQLite)")
        elif hasattr(db, "client"):
            logger.info("Database initialized successfully (Supabase)")
        else:
            logger.warning("Database initialized but type unknown")
    except Exception as db_test_error:
        logger.warning(
            f"Database initialized but test query failed: {db_test_error}",
            exc_info=True,
        )
    from backend.progress import progress_tracker

    progress_tracker._cleanup_old_tasks()
    gc.collect()
    print("Cache cleared on startup")
    logger.info("Application startup completed")
    yield
    try:
        progress_tracker._save_state()
        gc.collect()
        print("Cache cleared on shutdown")
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Initialize FastAPI app
app = FastAPI(
    title="Bilingual Lesson Plan Builder API",
    description="REST API for generating bilingual lesson plans with WIDA support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Include routers (health uses full paths; others use prefix="/api")
app.include_router(health_router)
app.include_router(settings_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(lesson_mode_router, prefix="/api")
app.include_router(lesson_steps_router, prefix="/api")
app.include_router(plans_router, prefix="/api")
app.include_router(process_week_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(core_router, prefix="/api")

# Add CORS middleware for Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(RenderError, render_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Set up rate limiting
setup_rate_limiting(app)

# Add rate limit metrics middleware (optional - tracks allowed requests)
# Note: Blocked requests are tracked in exception handler
try:
    from backend.rate_limit_middleware import RateLimitMetricsMiddleware

    app.add_middleware(RateLimitMetricsMiddleware)
except ImportError:
    # Metrics not available, skip middleware
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )
