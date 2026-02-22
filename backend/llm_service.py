"""
LLM Service for Bilingual Lesson Plan Transformation
Integrates OpenAI/Anthropic APIs with prompt_v4.md framework
"""

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import anthropic
import instructor
from dotenv import load_dotenv
from openai import OpenAI

from backend.config import settings
from backend.llm.prompt_builder import (
    build_prompt as build_prompt_fn,
    build_retry_prompt as build_retry_prompt_fn,
    build_schema_example,
    load_prompt_template,
)
from backend.llm.schema import (
    build_openai_structured_schema,
    load_schema,
    model_supports_json_mode,
    model_supports_structured_outputs,
    structured_response_format,
)
from backend.llm.providers import (
    call_anthropic_messages,
    call_instructor_chat_completion,
    call_openai_chat_completion,
    check_for_enums,
    convert_enums_to_strings,
)
from backend.llm.validation import parse_validation_errors
from backend.llm.api_key import get_llm_api_key
from backend.llm.post_process import normalize_sentence_frame_punctuation
from backend.llm.token_limits import get_max_completion_tokens, get_model_token_limit
from backend.llm.transform_runner import run_transform_lesson
from backend.telemetry import logger

# Load environment variables
load_dotenv()


class LLMService:
    """Service for transforming primary teacher content to bilingual lesson plans"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize LLM service

        Args:
            provider: "openai" or "anthropic"
            api_key: API key (if None, reads from environment)
        """
        self.provider = provider
        self.api_key = api_key or get_llm_api_key(provider)

        if not self.api_key:
            raise ValueError(
                f"No API key found for {provider}. Check environment variables or api_key.txt file."
            )

        # Log successful initialization
        api_key_preview = (
            f"{self.api_key[:8]}...{self.api_key[-4:]}"
            if len(self.api_key) > 12
            else "***"
        )
        success_msg = f"[OK] LLM Service: API key found for {provider} (preview: {api_key_preview}), service initialized successfully"
        try:
            print(success_msg)
        except UnicodeEncodeError:
            # Fallback for terminals that don't support Unicode
            print(
                f"[OK] LLM Service: API key found for {provider}, service initialized successfully"
            )
        logger.info(
            "llm_service_api_key_found",
            extra={
                "provider": provider,
                "api_key_preview": api_key_preview,
                "message": f"API key found for {provider}, LLM service initialized successfully",
            },
        )

        # Initialize client
        if provider == "openai":
            # Support custom base URL for specialized models
            base_url = os.getenv("OPENAI_BASE_URL")
            if base_url:
                self.client = OpenAI(
                    api_key=self.api_key, base_url=base_url, timeout=300.0
                )
            else:
                self.client = OpenAI(
                    api_key=self.api_key, timeout=300.0
                )  # 5 minute timeout for large responses
            self.model = os.getenv("LLM_MODEL") or "gpt-4-turbo-preview"
            # Wrap client with instructor for structured output management
            self.instructor_client = instructor.from_openai(self.client)
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = os.getenv("LLM_MODEL") or "claude-3-opus-20240229"
            # Wrap client with instructor for Anthropic support
            self.instructor_client = instructor.from_anthropic(self.client)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Load prompt template
        self.prompt_template = load_prompt_template()

        # Load schema
        self.schema = load_schema()
        self.openai_structured_schema = (
            build_openai_structured_schema(self.schema) if provider == "openai" else None
        )

        # Determine max completion tokens based on model and config
        self.max_completion_tokens = get_max_completion_tokens(provider, self.model)

        init_msg = f"OK LLM Service: Fully initialized - Provider: {provider}, Model: {self.model}, Max tokens: {self.max_completion_tokens}"
        print(init_msg)
        logger.info(
            "llm_service_initialized",
            extra={
                "provider": provider,
                "model": self.model,
                "max_completion_tokens": self.max_completion_tokens,
            },
        )

    def _convert_enums_to_strings(self, data: Any) -> Any:
        """Convert enum objects to strings (delegates to backend.llm.providers)."""
        return convert_enums_to_strings(data)

    def _check_for_enums(self, data: Any) -> bool:
        """Return True if data contains any enum objects (delegates to backend.llm.providers)."""
        return check_for_enums(data)

    def _parse_validation_errors(self, validation_error: str) -> Dict[str, Any]:
        """Parse validation error message (delegates to backend.llm.validation)."""
        return parse_validation_errors(validation_error)

    def _model_token_limit(self) -> Optional[int]:
        """Get model completion token limit (delegates to backend.llm.token_limits)."""
        return get_model_token_limit(self.model)

    def _call_openai_chat_completion(
        self,
        prompt: str,
        *,
        response_format: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Call OpenAI chat completions (delegates to backend.llm.providers)."""
        return call_openai_chat_completion(
            self.client,
            self.model,
            self.max_completion_tokens,
            prompt,
            response_format=response_format,
            max_retries=max_retries,
        )

    def _call_instructor_chat_completion(
        self,
        prompt: str,
        *,
        max_retries: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Call instructor for schema-compliant response (delegates to backend.llm.providers)."""
        return call_instructor_chat_completion(
            self.instructor_client,
            self.model,
            self.max_completion_tokens,
            prompt,
            max_retries=max_retries,
            provider=self.provider,
        )

    def transform_lesson(
        self,
        primary_content: str,
        grade: str,
        subject: str,
        week_of: str,
        teacher_name: Optional[str] = None,
        homeroom: Optional[str] = None,
        plan_id: Optional[str] = None,
        available_days: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Transform primary teacher content to bilingual lesson plan.

        Args:
            primary_content: Primary teacher's lesson content
            grade: Grade level (e.g., "6", "7")
            subject: Subject area
            week_of: Week date range (MM/DD-MM/DD)
            teacher_name: Bilingual teacher name (optional)
            homeroom: Homeroom/class identifier (optional)
            plan_id: Plan ID for performance tracking (optional)
            available_days: List of days that have content (e.g., ["monday"]). If None, generates all 5 days.

        Returns:
            Tuple of (success, lesson_json, error_message)
        """
        return run_transform_lesson(
            self,
            primary_content,
            grade,
            subject,
            week_of,
            teacher_name=teacher_name,
            homeroom=homeroom,
            plan_id=plan_id,
            available_days=available_days,
            progress_callback=progress_callback,
        )

    def _build_prompt(
        self,
        primary_content: str,
        grade: str,
        subject: str,
        week_of: str,
        teacher_name: Optional[str],
        homeroom: Optional[str],
        available_days: Optional[list[str]] = None,
    ) -> str:
        """Build complete prompt for LLM (delegates to backend.llm.prompt_builder)."""
        using_structured_outputs = (
            self.provider == "openai"
            and model_supports_structured_outputs(self.model)
            and self.openai_structured_schema is not None
        )
        schema_example = None if using_structured_outputs else build_schema_example(
            week_of, grade, subject, teacher_name, homeroom
        )
        return build_prompt_fn(
            self.prompt_template,
            primary_content,
            grade,
            subject,
            week_of,
            teacher_name,
            homeroom,
            available_days,
            using_structured_outputs,
            schema_example,
        )

    def _build_retry_prompt(
        self,
        original_prompt: str,
        validation_error: Optional[str],
        retry_count: int,
        available_days: Optional[List[str]] = None,
        error_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build retry prompt with validation feedback (delegates to backend.llm.prompt_builder)."""
        return build_retry_prompt_fn(
            original_prompt,
            validation_error,
            retry_count,
            available_days,
            error_analysis,
        )

    def _call_llm(self, prompt: str) -> Tuple[str, Dict[str, int]]:
        """Call LLM API and return content with token usage.

        Returns:
            Tuple of (response_text, usage_dict)
            usage_dict contains: tokens_input, tokens_output, tokens_total
        """
        logger.info(
            "llm_api_call_started",
            extra={
                "provider": self.provider,
                "model": self.model,
                "prompt_length": len(prompt),
                "max_completion_tokens": self.max_completion_tokens,
                "estimated_time_seconds": min(
                    180, (len(prompt) // 4 + self.max_completion_tokens) // 100
                ),  # Rough estimate
            },
        )

        if self.provider == "openai":
            if model_supports_structured_outputs(self.model):
                response_format = structured_response_format(
                    self.openai_structured_schema, self.model
                )
                if response_format:
                    try:
                        logger.info(
                            "using_openai_structured_outputs",
                            extra={"model": self.model},
                        )
                        return call_openai_chat_completion(
                            self.client,
                            self.model,
                            self.max_completion_tokens,
                            prompt,
                            response_format=response_format,
                        )
                    except Exception as exc:
                        logger.warning(
                            "structured_outputs_failed_fallback",
                            extra={"model": self.model, "error": str(exc)},
                        )

            if model_supports_json_mode(self.model):
                try:
                    logger.info(
                        "using_openai_json_mode",
                        extra={"model": self.model},
                    )
                    return call_openai_chat_completion(
                        self.client,
                        self.model,
                        self.max_completion_tokens,
                        prompt,
                        response_format={"type": "json_object"},
                    )
                except Exception as exc:
                    logger.warning(
                        "json_mode_failed_fallback",
                        extra={"model": self.model, "error": str(exc)},
                    )

            logger.info("using_openai_legacy_mode", extra={"model": self.model})
            return call_openai_chat_completion(
                self.client,
                self.model,
                self.max_completion_tokens,
                prompt,
            )

        if self.provider == "anthropic":
            return call_anthropic_messages(
                self.client,
                self.model,
                self.max_completion_tokens,
                prompt,
            )

        raise ValueError(f"Unsupported provider: {self.provider}")

# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: str = "openai", api_key: Optional[str] = None
) -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService(provider=provider, api_key=api_key)

    return _llm_service
