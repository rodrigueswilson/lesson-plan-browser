"""
Configuration settings for the Bilingual Lesson Plan Builder backend.
Supports feature flags, environment variables, and observability settings.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Bilingual Lesson Plan Builder"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    FRONTEND_ORIGINS: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins",
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/lesson_planner.db",
        description="SQLite database URL (absolute path computed from root)",
    )
    SQLITE_DB_PATH: Path = Field(
        default=Path("data/lesson_planner.db"),
        description="SQLite database path (absolute path computed from root)",
    )

    def __init__(self, **values):
        super().__init__(**values)
        # Force absolute paths after loading from env
        root = Path(__file__).parents[1]
        db_file = root / "data" / "lesson_planner.db"
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.SQLITE_DB_PATH = db_file.absolute()
        self.DATABASE_URL = f"sqlite:///{self.SQLITE_DB_PATH}"

    # Supabase Configuration
    USE_SUPABASE: bool = Field(
        default=False,
        description="Use Supabase PostgreSQL instead of SQLite (requires SUPABASE_URL and SUPABASE_KEY)",
    )
    SUPABASE_PROJECT: str = Field(
        default="project1",
        description="Which Supabase project to use: 'project1' (Wilson) or 'project2' (Daniela)",
    )
    # Project 1 (Wilson Rodrigues)
    SUPABASE_URL_PROJECT1: Optional[str] = Field(
        default=None, description="Supabase Project 1 URL (Wilson Rodrigues User 1)"
    )
    SUPABASE_KEY_PROJECT1: Optional[str] = Field(
        default=None, description="Supabase Project 1 anon/service role key"
    )
    SUPABASE_SERVICE_ROLE_KEY_PROJECT1: Optional[str] = Field(
        default=None, description="Supabase Project 1 service role key (optional)"
    )
    # Project 2 (Daniela Silva)
    SUPABASE_URL_PROJECT2: Optional[str] = Field(
        default=None, description="Supabase Project 2 URL (Daniela Silva User 2)"
    )
    SUPABASE_KEY_PROJECT2: Optional[str] = Field(
        default=None, description="Supabase Project 2 anon/service role key"
    )
    SUPABASE_SERVICE_ROLE_KEY_PROJECT2: Optional[str] = Field(
        default=None, description="Supabase Project 2 service role key (optional)"
    )
    # Legacy/backward compatibility - these map to the selected project
    SUPABASE_URL: Optional[str] = Field(
        default=None,
        description="Supabase project URL (legacy - use SUPABASE_URL_PROJECT1/2 instead)",
    )
    SUPABASE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase anon/service role key (legacy - use SUPABASE_KEY_PROJECT1/2 instead)",
    )
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase service role key (legacy - use SUPABASE_SERVICE_ROLE_KEY_PROJECT1/2 instead)",
    )

    @property
    def supabase_url(self) -> Optional[str]:
        """Get the active Supabase URL based on SUPABASE_PROJECT setting."""
        if self.SUPABASE_URL:
            return self.SUPABASE_URL  # Legacy support
        if self.SUPABASE_PROJECT == "project1":
            return self.SUPABASE_URL_PROJECT1
        elif self.SUPABASE_PROJECT == "project2":
            return self.SUPABASE_URL_PROJECT2
        return None

    @property
    def supabase_key(self) -> Optional[str]:
        """Get the active Supabase key based on SUPABASE_PROJECT setting.

        Preference order:
        1. Service-role key for the active project (if available)
        2. Legacy/global SUPABASE_KEY override
        3. Project-specific anon/service key
        """
        service_key = self.supabase_service_role_key
        if service_key:
            return service_key
        if self.SUPABASE_KEY:
            return self.SUPABASE_KEY  # Legacy support
        if self.SUPABASE_PROJECT == "project1":
            return self.SUPABASE_KEY_PROJECT1
        elif self.SUPABASE_PROJECT == "project2":
            return self.SUPABASE_KEY_PROJECT2
        return None

    @property
    def supabase_service_role_key(self) -> Optional[str]:
        """Get the active Supabase service role key based on SUPABASE_PROJECT setting."""
        if self.SUPABASE_SERVICE_ROLE_KEY:
            return self.SUPABASE_SERVICE_ROLE_KEY  # Legacy support
        if self.SUPABASE_PROJECT == "project1":
            return self.SUPABASE_SERVICE_ROLE_KEY_PROJECT1
        elif self.SUPABASE_PROJECT == "project2":
            return self.SUPABASE_SERVICE_ROLE_KEY_PROJECT2
        return None

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # or "anthropic", "google"
    LLM_MODEL: str = "gpt-4"
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Parallel Processing Configuration
    PARALLEL_LLM_PROCESSING: bool = Field(
        default=True,
        description="Enable parallel LLM API calls for multiple slots (faster but uses more API quota). Default: True"
    )
    MAX_CONCURRENT_LLM_REQUESTS: int = Field(
        default=5,
        description="Maximum concurrent LLM requests (typical: 5 slots). Adjust based on API tier limits. Default: 5"
    )
    RATE_LIMIT_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for rate limit errors. Default: 3"
    )
    RATE_LIMIT_BACKOFF_MULTIPLIER: float = Field(
        default=2.0,
        description="Exponential backoff multiplier for rate limit retries. Default: 2.0"
    )
    # OpenAI Rate Limits (default to Tier 1 - adjust based on your tier)
    OPENAI_RPM_LIMIT: int = Field(
        default=500,
        description="OpenAI requests per minute limit (based on tier). Tier 1: 500, Tier 2+: higher. Default: 500"
    )
    OPENAI_TPM_LIMIT: int = Field(
        default=500_000,
        description="OpenAI tokens per minute limit (based on tier). Tier 1: 500K, Tier 2+: higher. Default: 500000"
    )

    # Token budget settings
    MAX_PROMPT_TOKENS: int = 8000
    MAX_COMPLETION_TOKENS: int = (
        16000  # Increased from 4000 to handle full 5-day multi-slot lesson plans
    )
    TOKEN_ALERT_THRESHOLD_PCT: int = 20  # Alert if increase > 20%

    # Path settings
    TEMPLATE_DIR: str = "templates"

    ENABLE_JSON_OUTPUT: bool = Field(
        default=False,
        description="Enable JSON-based output pipeline (default: legacy markdown)",
    )
    JSON_PIPELINE_ROLLOUT_PERCENTAGE: int = Field(
        default=0,
        le=100,
        description="Percentage of users to enable JSON pipeline for (0-100)",
    )
    ENABLE_TELEMETRY: bool = Field(
        default=True, description="Enable structured logging and telemetry"
    )

    # Token Budget & Performance
    MAX_TOKEN_INCREASE_PCT: int = Field(
        default=20, description="Alert threshold for token usage increase (%)"
    )
    MAX_TOKENS_PER_LESSON: int = Field(
        default=4000, description="Hard limit for tokens per lesson plan"
    )
    RENDER_TIMEOUT_SECONDS: int = Field(
        default=30, description="Maximum time for rendering (seconds)"
    )
    PROGRESS_PROCESSING_WEIGHT: float = Field(
        default=0.8, description="Portion of progress allocated to slot processing"
    )
    PROGRESS_RENDERING_WEIGHT: float = Field(
        default=0.2, description="Portion of progress allocated to rendering"
    )

    # Validation & Retry
    MAX_VALIDATION_RETRIES: int = Field(
        default=3, description="Maximum retry attempts for validation errors"
    )
    ENABLE_JSON_REPAIR: bool = Field(
        default=True, description="Enable automatic JSON syntax repair"
    )

    # Storage & Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "console"
    LOG_FILE: str = "logs/json_pipeline.log"
    RETAIN_VALIDATED_PAYLOADS: bool = Field(
        default=True, description="Retain validated JSON payloads for debugging"
    )
    MAX_RETAINED_PAYLOADS: int = Field(
        default=100, description="Maximum number of payloads to retain per user"
    )

    # Performance Tracking (Session 2)
    ENABLE_PERFORMANCE_TRACKING: bool = Field(
        default=True, description="Enable performance metrics tracking"
    )
    PERFORMANCE_RETENTION_DAYS: int = Field(
        default=90, description="Number of days to retain performance metrics"
    )

    # Rate Limiting
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (e.g., redis://localhost:6379/0). If not set, uses in-memory storage.",
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None, description="Redis password (if required)"
    )
    REDIS_SSL: bool = Field(
        default=False, description="Use SSL/TLS for Redis connection"
    )
    REDIS_KEY_PREFIX: str = Field(
        default="rate_limit",
        description="Prefix for rate limit keys in Redis. Use format 'env:service:limiter' for better organization (e.g., 'prod:lesson_planner:rate_limit')",
    )
    REDIS_ENVIRONMENT: str = Field(
        default="prod",
        description="Environment name for Redis key namespacing (e.g., 'dev', 'staging', 'prod')",
    )
    REDIS_CIRCUIT_BREAKER_THRESHOLD: int = Field(
        default=5,
        description="Number of Redis connection failures before opening circuit breaker",
    )
    REDIS_CIRCUIT_BREAKER_TIMEOUT: int = Field(
        default=60,
        description="Seconds to keep circuit breaker open before attempting reconnection",
    )

    # Paths
    SCHEMA_PATH: str = "schemas/lesson_output_schema.json"
    OUTPUT_DIR: str = "output"
    DEFAULT_PLAN_LIMIT: int = Field(
        default=50, description="Default maximum number of plans to return"
    )

    # DOCX Template
    DOCX_TEMPLATE_PATH: str = "input/Lesson Plan Template SY'25-26.docx"

    # School Year Configuration
    SCHOOL_YEAR_START_YEAR: Optional[int] = Field(
        default=None,
        description="Start year of school year (e.g., 2025 for SY 2025-2026). If None, will be inferred from dates.",
    )
    SCHOOL_YEAR_END_YEAR: Optional[int] = Field(
        default=None,
        description="End year of school year (e.g., 2026 for SY 2025-2026). If None, will be inferred from dates.",
    )

    # Media Anchoring Settings (Session 7)
    MEDIA_MATCH_CONFIDENCE_THRESHOLD: float = Field(
        default=0.65,
        description="Minimum confidence score (0-1) for placing media inline vs fallback section",
    )
    IMAGE_INLINE_MIN_COLUMN_WIDTH_INCHES: float = Field(
        default=1.0,
        description="Minimum column width (inches) required for inline image placement",
    )
    MEDIA_CONTEXT_WINDOW_CHARS: int = Field(
        default=100,
        description="Number of characters to capture around media for context matching",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Return configured CORS origins as a list."""
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ]


# Global settings instance
settings = Settings()


def is_json_pipeline_enabled_for_user(user_id: str) -> bool:
    """
    Determine if JSON pipeline should be enabled for a specific user.

    Uses feature flag and rollout percentage for gradual deployment.

    Args:
        user_id: User identifier

    Returns:
        True if JSON pipeline should be enabled for this user
    """
    if not settings.ENABLE_JSON_OUTPUT:
        return False

    if settings.JSON_PIPELINE_ROLLOUT_PERCENTAGE == 0:
        return False

    if settings.JSON_PIPELINE_ROLLOUT_PERCENTAGE == 100:
        return True

    # Hash user_id to get consistent assignment
    import hashlib

    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    bucket = hash_value % 100

    return bucket < settings.JSON_PIPELINE_ROLLOUT_PERCENTAGE


def get_pipeline_mode() -> str:
    """
    Get current pipeline mode.

    Returns:
        "json" or "markdown"
    """
    return "json" if settings.ENABLE_JSON_OUTPUT else "markdown"
