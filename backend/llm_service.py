"""
LLM Service for Bilingual Lesson Plan Transformation
Integrates OpenAI/Anthropic APIs with prompt_v4.md framework
"""

import json
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
)
from backend.llm.validation import (
    parse_llm_response,
    parse_validation_errors,
    validate_structure,
)
from backend.llm.post_process import normalize_sentence_frame_punctuation
from backend.performance_tracker import get_tracker
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
        self.api_key = api_key or self._get_api_key()

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
        self.max_completion_tokens = self._determine_max_completion_tokens()

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

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or file"""
        # Try environment first
        if self.provider == "openai":
            # Check for GPT-5 specific API key first
            model = os.getenv("LLM_MODEL", "")
            if "gpt-5" in model.lower():
                key = (
                    os.getenv("GPT5_API_KEY")
                    or os.getenv("OPENAI_API_KEY")
                    or os.getenv("LLM_API_KEY")
                )
                if not key:
                    warning_msg = "⚠ LLM Service: No API key found in environment variables for OpenAI. Checked: GPT5_API_KEY, OPENAI_API_KEY, LLM_API_KEY"
                    print(warning_msg)
                    logger.warning(
                        "openai_api_key_not_found",
                        extra={
                            "provider": "openai",
                            "model": model,
                            "checked_keys": [
                                "GPT5_API_KEY",
                                "OPENAI_API_KEY",
                                "LLM_API_KEY",
                            ],
                            "message": "No API key found in environment variables",
                        },
                    )
            else:
                key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
                if not key:
                    warning_msg = "⚠ LLM Service: No API key found in environment variables for OpenAI. Checked: OPENAI_API_KEY, LLM_API_KEY"
                    print(warning_msg)
                    logger.warning(
                        "openai_api_key_not_found",
                        extra={
                            "provider": "openai",
                            "model": model or "default",
                            "checked_keys": ["OPENAI_API_KEY", "LLM_API_KEY"],
                            "message": "No API key found in environment variables",
                        },
                    )
        elif self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
            if not key:
                warning_msg = "⚠ LLM Service: No API key found in environment variables for Anthropic. Checked: ANTHROPIC_API_KEY, LLM_API_KEY"
                print(warning_msg)
                logger.warning(
                    "anthropic_api_key_not_found",
                    extra={
                        "provider": "anthropic",
                        "checked_keys": ["ANTHROPIC_API_KEY", "LLM_API_KEY"],
                        "message": "No API key found in environment variables",
                    },
                )
        else:
            logger.warning(
                "unknown_llm_provider",
                extra={
                    "provider": self.provider,
                    "message": f"Unknown LLM provider: {self.provider}",
                },
            )
            return None

        # If not in environment, try file
        if not key:
            try:
                with open("api_key.txt", "r") as f:
                    key = f.read().strip()
                if key:
                    info_msg = f"OK LLM Service: API key loaded from api_key.txt file for {self.provider}"
                    print(info_msg)
                    logger.info(
                        "api_key_found_in_file",
                        extra={
                            "provider": self.provider,
                            "source": "api_key.txt",
                            "message": "API key loaded from api_key.txt file",
                        },
                    )
            except (FileNotFoundError, IOError):
                logger.debug(
                    "api_key_file_not_found",
                    extra={
                        "provider": self.provider,
                        "file": "api_key.txt",
                        "message": "api_key.txt file not found, checking environment only",
                    },
                )

        if not key:
            error_msg = f"✗ LLM Service: No API key found for {self.provider}. Checked environment variables and api_key.txt file. Service will fail to initialize."
            print(error_msg)
            logger.error(
                "api_key_not_found_anywhere",
                extra={
                    "provider": self.provider,
                    "checked_env_vars": [
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "LLM_API_KEY",
                    ]
                    if self.provider == "openai"
                    else ["ANTHROPIC_API_KEY", "LLM_API_KEY"],
                    "checked_file": "api_key.txt",
                    "message": f"No API key found for {self.provider} in environment variables or api_key.txt file",
                },
            )

        return key

    def _determine_max_completion_tokens(self) -> int:
        """
        Determine max completion tokens based on model limits and configuration.

        Priority:
        1. LLM_MAX_COMPLETION_TOKENS environment variable
        2. Model-specific limit (if known)
        3. Default safe value (4000)

        Returns:
            Maximum completion tokens to request
        """
        # Check for explicit override
        env_value = os.getenv("LLM_MAX_COMPLETION_TOKENS")
        if env_value:
            try:
                override = int(env_value)
                logger.info("using_env_max_tokens", extra={"value": override})
                return override
            except ValueError:
                logger.warning(
                    "invalid_max_completion_tokens_env", extra={"value": env_value}
                )

        # Get model-specific limit
        model_limit = self._model_token_limit()

        # Default base limit - use model limit if available, otherwise use config default
        # For full 5-day multi-slot lesson plans, we need higher limits
        if model_limit:
            return model_limit

        # Fallback to config setting (default 16000) instead of hardcoded 4000
        from backend.config import settings

        return settings.MAX_COMPLETION_TOKENS

    def _model_token_limit(self) -> Optional[int]:
        """
        Get the maximum completion token limit for the current model.

        Returns:
            Token limit if known, None otherwise
        """
        # Known model limits (completion tokens only)
        # Updated limits to support full 5-day multi-slot lesson plans
        limits = {
            "gpt-4-turbo-preview": 16384,  # Increased for multi-slot lesson plans
            "gpt-4-turbo": 16384,  # Increased for multi-slot lesson plans
            "gpt-4o": 16384,  # GPT-4o has higher limit
            "gpt-4o-mini": 16384,
            "gpt-4": 16384,  # Increased for multi-slot lesson plans
            "gpt-3.5-turbo": 4096,  # Keep lower for older models
            "gpt-5": 16384,  # GPT-5 flagship has larger output capacity
            "gpt-5-mini": 32768,  # GPT-5-mini - increased for full 5-day lesson plans
            "gpt-5-nano": 8192,  # GPT-5-nano (smaller/faster)
            "o1-preview": 32768,  # O1 models have very high limits
            "o1-mini": 65536,
            "claude-3-opus": 4096,
            "claude-3-sonnet": 4096,
            "claude-3-haiku": 4096,
        }

        model_name = (self.model or "").lower()

        # Check for exact or partial match
        for key, limit in limits.items():
            if key in model_name:
                logger.info(
                    "model_token_limit_found",
                    extra={"model": self.model, "limit": limit},
                )
                return limit

        logger.warning("model_token_limit_unknown", extra={"model": self.model})
        return None

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
        Transform primary teacher content to bilingual lesson plan

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
        logger.info(
            "llm_transform_started",
            extra={
                "grade": grade,
                "subject": subject,
                "week_of": week_of,
                "available_days": available_days,
            },
        )

        # Update progress: Starting transformation
        if progress_callback:
            progress_callback(
                "processing", 10, f"Preparing to transform {subject} lesson plan..."
            )

        tracker = get_tracker()

        # Track original max_completion_tokens to restore after retries (must be before try block)
        original_max_tokens = self.max_completion_tokens

        try:
            # Track prompt building
            if progress_callback:
                progress_callback(
                    "processing", 15, "Building prompt for AI transformation..."
                )

            if plan_id:
                with tracker.track_operation(plan_id, "llm_build_prompt"):
                    full_prompt = self._build_prompt(
                        primary_content,
                        grade,
                        subject,
                        week_of,
                        teacher_name,
                        homeroom,
                        available_days,
                    )
            else:
                full_prompt = self._build_prompt(
                    primary_content,
                    grade,
                    subject,
                    week_of,
                    teacher_name,
                    homeroom,
                    available_days,
                )

            if progress_callback:
                progress_callback(
                    "processing", 20, "Prompt built. Sending to AI service..."
                )

            # Retry logic: use config setting for max retries
            # RATE_LIMIT_RETRY_ATTEMPTS means "number of retry attempts" (e.g., 3 retries = 4 total attempts)
            max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS
            retry_count = 0
            lesson_json = None
            validation_error = None
            error_analysis = None  # Store error analysis for retry prompts

            # Loop allows max_retries + 1 total attempts (1 initial + max_retries retries)
            while retry_count <= max_retries:
                # Update progress: About to call LLM API
                if progress_callback:
                    if retry_count > 0:
                        progress_callback(
                            "processing",
                            25,
                            f"Retrying AI transformation (attempt {retry_count + 1})...",
                        )
                    else:
                        progress_callback(
                            "processing",
                            25,
                            "Calling AI service to transform lesson plan...",
                        )

                # PHASE 5: Try Instructor Path for OpenAI
                if self.provider == "openai" and self.instructor_client:
                    try:
                        if plan_id:
                            with tracker.track_operation(
                                plan_id, "llm_api_call_instructor"
                            ) as op:
                                # We let instructor handle retries for validation internally
                                # But we still track tokens and outcomes
                                lesson_json, usage = (
                                    self._call_instructor_chat_completion(
                                        full_prompt, max_retries=max_retries
                                    )
                                )
                                op["llm_model"] = self.model
                                op["llm_provider"] = "openai-instructor"
                        else:
                            lesson_json, usage = self._call_instructor_chat_completion(
                                full_prompt, max_retries=max_retries
                            )

                        # If we got here, lesson_json is already a validated dict
                        # We can skip the parse and validate structure steps
                        is_valid = True
                        validation_error = None
                        response_text = json.dumps(
                            lesson_json
                        )  # For logging compatibility
                        break  # Exit retry loop

                    except Exception as e:
                        logger.warning(
                            "llm_instructor_failed_falling_back",
                            extra={"error": str(e), "retry_count": retry_count},
                        )
                        # Fallback to legacy path if instructor fails repeatedly or has issues
                        # (though instructor is usually more robust)
                        # If it's a validation error instructor couldn't fix, we might want to retry with legacy?
                        # For now, let's keep the legacy path as fallback inside the loop

                # LEGACY PATH (Phase 1-3 fixes still apply here)
                # Track LLM API call
                if plan_id:
                    with tracker.track_operation(plan_id, "llm_api_call") as op:
                        if retry_count > 0:
                            # Add feedback to prompt for retry
                            feedback_prompt = self._build_retry_prompt(
                                full_prompt,
                                validation_error,
                                retry_count,
                                available_days,
                                error_analysis,
                            )
                            response_text, usage = self._call_llm(feedback_prompt)
                        else:
                            response_text, usage = self._call_llm(full_prompt)
                        # Store usage info for tracking
                        op["tokens_input"] = usage.get("tokens_input", 0)
                        op["tokens_output"] = usage.get("tokens_output", 0)
                        op["llm_model"] = self.model
                        op["llm_provider"] = self.provider
                        op["retry_count"] = retry_count
                else:
                    if retry_count > 0:
                        # Add feedback to prompt for retry
                        feedback_prompt = self._build_retry_prompt(
                            full_prompt,
                            validation_error,
                            retry_count,
                            None,
                            error_analysis,
                        )
                        response_text, usage = self._call_llm(feedback_prompt)
                    else:
                        response_text, usage = self._call_llm(full_prompt)

                # Update progress: API call completed
                if progress_callback:
                    progress_callback(
                        "processing", 60, "AI response received. Processing results..."
                    )

                # CRITICAL: Check if response was truncated (near token limit)
                was_truncated = usage.get("tokens_output", 0) >= (
                    self.max_completion_tokens * 0.95
                )
                if was_truncated:
                    logger.warning(
                        "llm_response_near_limit",
                        extra={
                            "tokens_output": usage.get("tokens_output", 0),
                            "max_completion_tokens": self.max_completion_tokens,
                            "model": self.model,
                            "retry_count": retry_count,
                        },
                    )
                    # Increase max tokens for retry (up to 2x original, but cap at model limit)
                    if retry_count < max_retries:
                        new_max_tokens = min(
                            int(self.max_completion_tokens * 1.5),
                            settings.MAX_COMPLETION_TOKENS * 2,  # Cap at 2x config max
                            32000,  # Hard cap for most models
                        )
                        if new_max_tokens > self.max_completion_tokens:
                            logger.info(
                                "increasing_max_tokens_for_retry",
                                extra={
                                    "old_max": self.max_completion_tokens,
                                    "new_max": new_max_tokens,
                                    "retry_count": retry_count,
                                },
                            )
                            self.max_completion_tokens = new_max_tokens

                # Update progress: Parsing response
                if progress_callback:
                    progress_callback("processing", 70, "Parsing AI response...")

                # Track JSON parsing with error handling for retry
                try:
                    if plan_id:
                        with tracker.track_operation(plan_id, "llm_parse_response"):
                            lesson_json = parse_llm_response(response_text)
                    else:
                        lesson_json = parse_llm_response(response_text)
                except ValueError as json_error:
                    # JSON parsing failed - retry if attempts remain
                    json_error_msg = str(json_error)
                    # Extract error_analysis if available
                    error_analysis = getattr(json_error, "error_analysis", None)

                    logger.warning(
                        "json_parse_error_retry",
                        extra={
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "error": json_error_msg,
                            "response_length": len(response_text)
                            if response_text
                            else 0,
                            "tokens_output": usage.get("tokens_output", 0),
                            "was_truncated": was_truncated,
                            "error_analysis": error_analysis,
                        },
                    )
                    if retry_count < max_retries:
                        retry_count += 1
                        # Include JSON error in validation_error so retry prompt mentions it
                        validation_error = f"JSON parsing failed: {json_error_msg}. Please ensure the response is complete, valid JSON without truncation."
                        # Store error_analysis for use in retry prompt
                        error_analysis = getattr(json_error, "error_analysis", None)
                        # If truncated, max_tokens already increased above
                        continue  # Retry the LLM call
                    else:
                        # Restore original max tokens before returning error
                        self.max_completion_tokens = original_max_tokens
                        # No more retries, return error
                        return (
                            False,
                            None,
                            f"Failed to parse JSON after {max_retries + 1} attempts: {json_error_msg}",
                        )

                # Update progress: Validating structure
                if progress_callback:
                    progress_callback(
                        "processing", 80, "Validating lesson plan structure..."
                    )

                # Track validation
                if plan_id:
                    with tracker.track_operation(plan_id, "llm_validate_structure"):
                        is_valid, validation_error = validate_structure(lesson_json)
                else:
                    is_valid, validation_error = validate_structure(lesson_json)

                if progress_callback:
                    if is_valid:
                        progress_callback(
                            "processing",
                            90,
                            "Validation passed. Finalizing lesson plan...",
                        )
                    else:
                        progress_callback(
                            "processing", 75, "Validation issue detected. Retrying..."
                        )

                if is_valid:
                    # Validation passed, restore original max tokens and break out of retry loop
                    self.max_completion_tokens = original_max_tokens
                    break

                # Validation failed - parse errors for structured feedback
                parsed_validation_errors = None
                if validation_error:
                    parsed_validation_errors = parse_validation_errors(validation_error)
                    # Merge parsed validation errors into error_analysis for retry prompt
                    if error_analysis is None:
                        error_analysis = {}
                    error_analysis["validation_errors"] = parsed_validation_errors

                # Validation failed - log and retry if attempts remain
                logger.warning(
                    "llm_validation_failed_retry",
                    extra={
                        "retry_count": retry_count,
                        "max_retries": max_retries,
                        "validation_error": validation_error,
                        "parsed_errors": parsed_validation_errors,
                    },
                )

                if retry_count < max_retries:
                    retry_count += 1
                    logger.info(
                        "llm_retry_attempt",
                        extra={
                            "retry_count": retry_count,
                            "validation_error": validation_error,
                            "parsed_errors": parsed_validation_errors,
                        },
                    )
                else:
                    # No more retries, restore original max tokens and return error
                    self.max_completion_tokens = original_max_tokens
                    return (
                        False,
                        None,
                        validation_error
                        or "Generated JSON does not match required schema structure",
                    )

            # Add usage information to result
            lesson_json["_usage"] = usage
            lesson_json["_model"] = self.model
            lesson_json["_provider"] = self.provider

            logger.info(
                "llm_transform_success",
                extra={
                    "response_length": len(response_text),
                    "tokens_total": usage.get("tokens_total", 0),
                },
            )

            # PHASE 6: Normalize sentence frame punctuation for consistency
            lesson_json = normalize_sentence_frame_punctuation(lesson_json)

            if plan_id:
                tracker.update_plan_summary(plan_id)

            return True, lesson_json, None

        except Exception as e:
            # Restore original max tokens in case of exception
            self.max_completion_tokens = original_max_tokens
            error_msg = f"LLM transformation failed: {str(e)}"
            logger.error("llm_transform_error", extra={"error": str(e)})
            return False, None, error_msg

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
