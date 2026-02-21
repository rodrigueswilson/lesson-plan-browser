"""
LLM Service for Bilingual Lesson Plan Transformation
Integrates OpenAI/Anthropic APIs with prompt_v4.md framework
"""

import json
import os
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import anthropic
import instructor
from dotenv import load_dotenv
from openai import APIError, OpenAI, RateLimitError

from backend.config import settings
from backend.lesson_schema_models import BilingualLessonPlanOutputSchema
from backend.performance_tracker import get_tracker
from backend.telemetry import logger
from tools.json_repair import repair_json

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
        self.prompt_template = self._load_prompt_template()

        # Load schema
        self.schema = self._load_schema()
        self.openai_structured_schema = (
            self._build_openai_structured_schema() if provider == "openai" else None
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

    def _load_prompt_template(self) -> str:
        """Load prompt_v4.md framework"""
        # Try multiple possible locations
        possible_paths = [
            Path("prompt_v4.md"),  # Root directory
            Path("docs/prompt_v4.md"),  # Docs directory
            Path(__file__).parent.parent
            / "docs"
            / "prompt_v4.md",  # Relative to this file
            Path(__file__).parent.parent / "prompt_v4.md",  # Parent directory
        ]

        prompt_path = None
        for path in possible_paths:
            if path.exists():
                prompt_path = path
                break

        if not prompt_path:
            searched_paths = [str(p) for p in possible_paths]
            error_msg = f"ERROR LLM Service: prompt_v4.md not found. Searched in: {', '.join(searched_paths)}"
            print(error_msg)
            raise FileNotFoundError(
                f"prompt_v4.md not found. Searched in: {', '.join(searched_paths)}"
            )

        info_msg = f"OK LLM Service: Loaded prompt template from {prompt_path}"
        try:
            print(info_msg)
        except UnicodeEncodeError:
            # Fallback for Windows console encoding issues
            print(f"OK LLM Service: Loaded prompt template from {prompt_path}")
        logger.info(
            "prompt_template_loaded",
            extra={
                "path": str(prompt_path),
                "message": f"Loaded prompt template from {prompt_path}",
            },
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON output schema"""
        schema_path = Path("schemas/lesson_output_schema.json")
        if not schema_path.exists():
            raise FileNotFoundError("lesson_output_schema.json not found")

        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_openai_structured_schema(self) -> Dict[str, Any]:
        """Prepare schema for OpenAI structured outputs."""
        if not self.schema:
            return {"type": "object", "additionalProperties": False}

        schema_copy = deepcopy(self.schema)
        for key in ("$schema", "$id", "title", "description", "version"):
            schema_copy.pop(key, None)

        if not schema_copy.get("type"):
            schema_copy["type"] = "object"

        # OpenAI structured outputs requires additionalProperties to be explicitly set to false
        # Add it recursively to all object types
        schema_copy = self._add_additional_properties_false(schema_copy)

        # OpenAI structured outputs doesn't support oneOf in certain contexts
        # Transform oneOf to anyOf or flatten union types
        schema_copy = self._transform_oneof_for_openai(schema_copy)

        return schema_copy

    def _add_additional_properties_false(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively add additionalProperties: false to all object schemas."""
        if not isinstance(schema, dict):
            return schema

        result = deepcopy(schema)

        # If it's an object type, ensure additionalProperties is False
        if result.get("type") == "object":
            if "additionalProperties" not in result:
                result["additionalProperties"] = False

        # Process properties
        if "properties" in result:
            for key, value in result["properties"].items():
                result["properties"][key] = self._add_additional_properties_false(value)

        # Process definitions (for $ref references)
        if "definitions" in result:
            for key, value in result["definitions"].items():
                result["definitions"][key] = self._add_additional_properties_false(
                    value
                )

        # Process items (for arrays)
        if "items" in result:
            if isinstance(result["items"], dict):
                result["items"] = self._add_additional_properties_false(result["items"])
            elif isinstance(result["items"], list):
                result["items"] = [
                    self._add_additional_properties_false(item)
                    if isinstance(item, dict)
                    else item
                    for item in result["items"]
                ]

        # Process oneOf, anyOf, allOf (for conditional schemas)
        for keyword in ["oneOf", "anyOf", "allOf"]:
            if keyword in result:
                result[keyword] = [
                    self._add_additional_properties_false(item)
                    if isinstance(item, dict)
                    else item
                    for item in result[keyword]
                ]

        return result

    def _transform_oneof_for_openai(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Transform oneOf to anyOf and handle optional properties for OpenAI structured outputs compatibility.

        OpenAI structured outputs API:
        1. Doesn't support oneOf in certain contexts - convert to anyOf
        2. For strict mode: Requires all properties to be in the 'required' array - remove optional properties
        3. For non-strict mode (gpt-5-mini): Keep optional properties for better compatibility
        """
        if not isinstance(schema, dict):
            return schema

        result = deepcopy(schema)

        # Transform oneOf to anyOf recursively
        if "oneOf" in result:
            # Replace oneOf with anyOf (OpenAI accepts anyOf but not oneOf)
            result["anyOf"] = result.pop("oneOf")

        # Process definitions recursively first
        if "definitions" in result:
            for key, value in result["definitions"].items():
                result["definitions"][key] = self._transform_oneof_for_openai(value)

        # Process properties recursively
        if "properties" in result:
            for key, value in result["properties"].items():
                result["properties"][key] = self._transform_oneof_for_openai(value)

        # NOTE: For strict mode, OpenAI requires all properties to be in 'required' array
        # However, for gpt-5-mini we use strict=False, so we keep optional properties
        # This allows better compatibility and avoids issues where gpt-5-mini returns
        # JSON-encoded strings instead of structured objects
        #
        # We no longer remove optional properties here - let the model have flexibility
        # The schema validation will still ensure structure, but optional fields are allowed

        # Process items recursively
        if "items" in result:
            if isinstance(result["items"], dict):
                result["items"] = self._transform_oneof_for_openai(result["items"])
            elif isinstance(result["items"], list):
                result["items"] = [
                    self._transform_oneof_for_openai(item)
                    if isinstance(item, dict)
                    else item
                    for item in result["items"]
                ]

        # Process anyOf/allOf recursively (they may contain oneOf)
        for keyword in ["anyOf", "allOf"]:
            if keyword in result:
                result[keyword] = [
                    self._transform_oneof_for_openai(item)
                    if isinstance(item, dict)
                    else item
                    for item in result[keyword]
                ]

        return result

    def _structured_response_format(self) -> Optional[Dict[str, Any]]:
        """Return the response_format payload for OpenAI structured outputs."""
        if not self.openai_structured_schema:
            return None

        # GPT-5-mini has known issues with strict mode - use False for better compatibility
        # Based on OpenAI documentation and community reports, strict mode can cause
        # JSON-encoded strings instead of structured objects
        model_name = (self.model or "").lower()
        use_strict = False if "gpt-5-mini" in model_name else True

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "bilingual_lesson_plan",
                "schema": deepcopy(self.openai_structured_schema),
                "strict": use_strict,
            },
        }

    def _model_supports_structured_outputs(self) -> bool:
        """Check if the configured model supports structured outputs."""
        model_name = (self.model or "").lower()
        supported_tokens = (
            "gpt-5-mini",
            "gpt-5",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "o1",
        )
        return any(token in model_name for token in supported_tokens)

    def _model_supports_json_mode(self) -> bool:
        """Check if the configured model supports OpenAI JSON mode."""
        model_name = (self.model or "").lower()
        supported_tokens = (
            "gpt-5-mini",
            "gpt-5",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
        )
        return any(token in model_name for token in supported_tokens)

    def _analyze_domains_from_activities(
        self,
        ell_support: Optional[List[Dict[str, Any]]] = None,
        phase_plan: Optional[List[Dict[str, Any]]] = None,
        content_objective: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Analyze lesson activities to determine which language domains are used.

        Args:
            ell_support: List of ELL support strategies
            phase_plan: List of phase plan activities
            content_objective: Content objective text

        Returns:
            Dict with keys: listening, reading, speaking, writing (all bool)
        """
        domains = {
            "listening": False,
            "reading": False,
            "speaking": False,
            "writing": False,
        }

        # Strategy-based domain mapping
        strategy_domain_map = {
            "think_pair_share": {"listening", "speaking"},
            "collaborative_learning": {"listening", "speaking"},
            "sentence_frames": {"speaking", "writing"},
            "graphic_organizers": {"reading", "writing"},
            "cognate_awareness": {"reading", "writing"},
            "oral_rehearsal": {"speaking", "listening"},
            "peer_tutoring": {"listening", "speaking"},
            "literature_circles": {"reading", "speaking", "listening"},
            "jigsaw": {"reading", "speaking", "listening"},
            "read_aloud": {"listening", "reading"},
            "shared_reading": {"reading", "speaking"},
            "interactive_writing": {"writing", "speaking"},
            "guided_writing": {"writing", "reading"},
        }

        # Analyze ELL support strategies
        if ell_support:
            for strategy in ell_support:
                strategy_id = strategy.get("strategy_id", "").lower()
                if strategy_id in strategy_domain_map:
                    for domain in strategy_domain_map[strategy_id]:
                        domains[domain] = True

        # Analyze phase plan activities (keyword-based)
        if phase_plan:
            activity_text = " ".join(
                [
                    phase.get("phase_name", "")
                    + " "
                    + phase.get("bilingual_teacher_role", "")
                    + " "
                    + phase.get("primary_teacher_role", "")
                    + " "
                    + phase.get("details", "")
                    for phase in phase_plan
                ]
            ).lower()

            # Keyword detection
            if any(
                word in activity_text
                for word in ["listen", "hear", "audio", "explanation", "instruction"]
            ):
                domains["listening"] = True
            if any(
                word in activity_text
                for word in ["read", "text", "passage", "article", "book", "document"]
            ):
                domains["reading"] = True
            if any(
                word in activity_text
                for word in [
                    "speak",
                    "discuss",
                    "share",
                    "present",
                    "talk",
                    "say",
                    "tell",
                ]
            ):
                domains["speaking"] = True
            if any(
                word in activity_text
                for word in [
                    "write",
                    "compose",
                    "draft",
                    "paragraph",
                    "essay",
                    "response",
                ]
            ):
                domains["writing"] = True

        # Analyze content objective for domain hints
        if content_objective:
            obj_lower = content_objective.lower()
            if any(
                word in obj_lower for word in ["read", "comprehend", "analyze text"]
            ):
                domains["reading"] = True
            if any(
                word in obj_lower
                for word in ["write", "compose", "draft", "create text"]
            ):
                domains["writing"] = True
            if any(
                word in obj_lower
                for word in ["speak", "present", "discuss", "explain orally"]
            ):
                domains["speaking"] = True
            if any(word in obj_lower for word in ["listen", "follow instructions"]):
                domains["listening"] = True

        return domains

    def _extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract retry-after time from rate limit error.

        Args:
            error: RateLimitError or APIError exception

        Returns:
            Retry-after time in seconds, or None if not available
        """
        if hasattr(error, "response") and error.response:
            retry_after = error.response.headers.get("retry-after")
            if retry_after:
                try:
                    return float(retry_after)
                except (ValueError, TypeError):
                    pass
        return None

    def _call_openai_chat_completion(
        self,
        prompt: str,
        *,
        response_format: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
    ) -> Tuple[str, Dict[str, int]]:
        """Call OpenAI chat completions with optional response_format and rate limit handling.

        Args:
            prompt: The prompt to send
            response_format: Optional response format specification
            max_retries: Maximum retry attempts for rate limits (defaults to config)

        Returns:
            Tuple of (content, usage_dict)

        Raises:
            RateLimitError: If rate limit exceeded after all retries
            APIError: For other API errors
        """
        if max_retries is None:
            max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS

        # RATE_LIMIT_RETRY_ATTEMPTS means "number of retry attempts" (e.g., 3 retries = 4 total attempts)
        # So we need max_retries + 1 total attempts (1 initial + max_retries retries)
        backoff_multiplier = settings.RATE_LIMIT_BACKOFF_MULTIPLIER

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": self.max_completion_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                usage = {
                    "tokens_input": response.usage.prompt_tokens
                    if response.usage
                    else 0,
                    "tokens_output": response.usage.completion_tokens
                    if response.usage
                    else 0,
                    "tokens_total": response.usage.total_tokens
                    if response.usage
                    else 0,
                }

                # Log finish_reason for debugging truncation issues
                logger.debug(
                    "llm_response_received",
                    extra={
                        "finish_reason": finish_reason,
                        "content_length": len(content) if content else 0,
                        "tokens_output": usage.get("tokens_output", 0),
                        "max_completion_tokens": self.max_completion_tokens,
                    },
                )

                # CRITICAL: Check for truncation (finish_reason == "length")
                # Instead of failing immediately, log a warning and attempt to repair the truncated JSON
                if finish_reason == "length":
                    logger.warning(
                        "llm_response_truncated_attempting_repair",
                        extra={
                            "model": self.model,
                            "tokens_output": usage.get("tokens_output", 0),
                            "max_completion_tokens": self.max_completion_tokens,
                            "content_length": len(content) if content else 0,
                            "response_preview": content[:500] if content else None,
                            "note": "Response truncated but will attempt JSON repair",
                        },
                    )
                    # Don't raise error - let JSON repair attempt to salvage the truncated response
                    # If repair fails, the JSON parsing will raise an error which can be handled

                if not content:
                    logger.error(
                        "openai_empty_response",
                        extra={
                            "finish_reason": finish_reason,
                            "model": self.model,
                        },
                    )
                    raise ValueError(
                        f"OpenAI returned empty response. Finish reason: {finish_reason}"
                    )

                return content, usage

            except RateLimitError as e:
                last_error = e
                retry_after = self._extract_retry_after(e)
                wait_time = retry_after or (backoff_multiplier**attempt)

                logger.warning(
                    "openai_rate_limit_retry",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "total_attempts": max_retries + 1,
                        "wait_time": wait_time,
                        "retry_after": retry_after,
                        "model": self.model,
                    },
                )

                if attempt < max_retries:
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    logger.error(
                        "openai_rate_limit_exceeded",
                        extra={
                            "max_retries": max_retries,
                            "total_attempts": max_retries + 1,
                            "model": self.model,
                            "error": str(e),
                        },
                    )
                    raise

            except APIError as e:
                # Check if it's a rate limit error (429) without proper exception type
                error_str = str(e).lower()
                if "429" in str(e) or "rate limit" in error_str:
                    last_error = e
                    wait_time = backoff_multiplier**attempt

                    logger.warning(
                        "openai_rate_limit_detected",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "total_attempts": max_retries + 1,
                            "wait_time": wait_time,
                            "model": self.model,
                            "error": str(e),
                        },
                    )

                    if attempt < max_retries:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            "openai_rate_limit_exceeded",
                            extra={
                                "max_retries": max_retries,
                                "total_attempts": max_retries + 1,
                                "model": self.model,
                                "error": str(e),
                            },
                        )
                        raise RateLimitError(
                            f"Rate limit exceeded after {max_retries + 1} attempts: {str(e)}"
                        )
                else:
                    # Not a rate limit error, re-raise immediately
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in _call_openai_chat_completion")

    def _convert_enums_to_strings(self, data: Any) -> Any:
        """
        Recursively convert enum objects to their string values.
        Used as fallback if model_dump(mode='json') doesn't work.

        Args:
            data: Any data structure that may contain enums

        Returns:
            Same structure with all enums converted to strings
        """
        from enum import Enum

        if isinstance(data, Enum):
            return data.value
        elif isinstance(data, dict):
            return {k: self._convert_enums_to_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_enums_to_strings(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._convert_enums_to_strings(item) for item in data)
        else:
            return data

    def _check_for_enums(self, data: Any) -> bool:
        """
        Check if a data structure contains any enum objects.
        Used for logging/debugging.

        Args:
            data: Any data structure to check

        Returns:
            True if any enum objects are found, False otherwise
        """
        from enum import Enum

        if isinstance(data, Enum):
            return True
        elif isinstance(data, dict):
            return any(self._check_for_enums(v) for v in data.values())
        elif isinstance(data, (list, tuple)):
            return any(self._check_for_enums(item) for item in data)
        else:
            return False

    def _call_instructor_chat_completion(
        self,
        prompt: str,
        *,
        max_retries: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """
        Call OpenAI using instructor library for guaranteed schema compliance.

        Args:
            prompt: The prompt to send
            max_retries: Maximum validation/retry attempts

        Returns:
            Tuple of (lesson_dict, usage_dict)
        """
        if max_retries is None:
            max_retries = settings.RATE_LIMIT_RETRY_ATTEMPTS

        logger.info("llm_instructor_call_started", extra={"model": self.model})

        # instructor handles both rate limits (via wrap) and validation retries
        try:
            # We use chat.completions.create with response_model
            # max_retries here is for VALIDATION retries (instructor's feature)
            # Rate limit retries are handled by the wrapped client if configured,
            # but instructor's max_retries also covers some aspects.

            logger.debug(
                "llm_instructor_calling_api",
                extra={"model": self.model, "provider": self.provider},
            )

            # PHASE 5: Implementation - Capture token usage with create_with_completion
            if self.provider == "openai":
                response, completion = (
                    self.instructor_client.chat.completions.create_with_completion(
                        model=self.model,
                        response_model=BilingualLessonPlanOutputSchema,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=self.max_completion_tokens,
                        max_retries=max_retries,
                    )
                )
                usage = {
                    "tokens_input": completion.usage.prompt_tokens
                    if completion.usage
                    else 0,
                    "tokens_output": completion.usage.completion_tokens
                    if completion.usage
                    else 0,
                    "tokens_total": completion.usage.total_tokens
                    if completion.usage
                    else 0,
                }
                logger.debug(
                    "llm_instructor_api_success",
                    extra={"response_type": type(response).__name__},
                )
            else:
                # For Anthropic or others, generic create call (or adapt if needed)
                response = self.instructor_client.chat.completions.create(
                    model=self.model,
                    response_model=BilingualLessonPlanOutputSchema,
                    messages=[{"role": "user", "content": prompt}],
                    max_retries=max_retries,
                )
                usage = {"tokens_input": 0, "tokens_output": 0, "tokens_total": 0}
                logger.debug(
                    "llm_instructor_api_success",
                    extra={"response_type": type(response).__name__},
                )

            # Convert Pydantic model to dictionary
            # Use mode='json' to ensure enums are serialized as strings (fixes ProficiencyLevel serialization error)
            # With enums now subclassing str, this should work, but we have defensive fallback
            logger.debug(
                "llm_instructor_converting_to_dict",
                extra={"response_type": type(response).__name__},
            )
            try:
                lesson_dict = response.model_dump(mode="json", exclude_none=False)
                logger.debug(
                    "llm_instructor_dict_conversion_success",
                    extra={"has_enums": self._check_for_enums(lesson_dict)},
                )
            except (TypeError, ValueError) as dump_error:
                # Fallback: if mode='json' fails, use default mode and manually convert enums
                error_msg = str(dump_error)
                if "not JSON serializable" in error_msg or any(
                    enum_name in error_msg
                    for enum_name in ["ProficiencyLevel", "PatternId", "FrameType"]
                ):
                    logger.warning(
                        "llm_instructor_enum_serialization_fallback",
                        extra={
                            "error": error_msg,
                            "fallback": "Using default model_dump + manual enum conversion",
                        },
                    )
                    lesson_dict = response.model_dump(exclude_none=False)
                    lesson_dict = self._convert_enums_to_strings(lesson_dict)
                    logger.debug(
                        "llm_instructor_enum_conversion_complete",
                        extra={"has_enums": self._check_for_enums(lesson_dict)},
                    )
                else:
                    # Re-raise if it's not an enum serialization error
                    raise

            return lesson_dict, usage

        except Exception as e:
            error_msg = str(e)
            logger.error(
                "llm_instructor_error",
                extra={
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "is_serialization_error": "not JSON serializable" in error_msg
                    or any(
                        enum_name in error_msg
                        for enum_name in ["ProficiencyLevel", "PatternId", "FrameType"]
                    ),
                },
            )
            raise

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
                            lesson_json = self._parse_response(response_text)
                    else:
                        lesson_json = self._parse_response(response_text)
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
                        is_valid, validation_error = self._validate_structure(
                            lesson_json
                        )
                else:
                    is_valid, validation_error = self._validate_structure(lesson_json)

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
                    parsed_validation_errors = self._parse_validation_errors(
                        validation_error
                    )
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
            lesson_json = self._normalize_sentence_frame_punctuation(lesson_json)

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
        """Build complete prompt for LLM"""

        # Configure grade level in template
        grade_level = f"{grade}th grade" if grade.isdigit() else grade
        prompt = self.prompt_template.replace(
            "[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]",
            f"[GRADE_LEVEL_VARIABLE = {grade_level}]",
        )

        # Build metadata context
        # Include all metadata to ensure LLM has full context
        metadata_context = f"""
Week: {week_of}
Grade: {grade}
Subject: {subject}
Teacher Name: {teacher_name or "Not specified"}
Homeroom: {homeroom or "Not specified"}
"""

        # Check if structured outputs will be used (to optimize prompt)
        using_structured_outputs = (
            self.provider == "openai"
            and self._model_supports_structured_outputs()
            and self.openai_structured_schema is not None
        )

        # Determine which days to generate
        if available_days:
            # Normalize day names
            available_days_normalized = [day.lower().strip() for day in available_days]
            days_to_generate = [
                d
                for d in ["monday", "tuesday", "wednesday", "thursday", "friday"]
                if d in available_days_normalized
            ]
            if not days_to_generate:
                # Fallback: if available_days doesn't match standard names, use all days
                days_to_generate = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                ]
            days_text = ", ".join([d.capitalize() for d in days_to_generate])
            days_instruction = (
                f"**CRITICAL: Include ALL required fields ONLY for {days_text}**"
            )
            days_count_text = f"{len(days_to_generate)} day{'s' if len(days_to_generate) != 1 else ''}"
        else:
            days_to_generate = ["monday", "tuesday", "wednesday", "thursday", "friday"]
            days_text = "Monday, Tuesday, Wednesday, Thursday, Friday"
            days_instruction = f"**CRITICAL: Include ALL required fields for ALL FIVE DAYS ({days_text})**"
            days_count_text = "ALL 5 DAYS"

        # Build prompt with or without schema examples
        if using_structured_outputs:
            # Optimized prompt for structured outputs - schema provided via API
            # OPTIMIZATION: When available_days is provided, only request those specific days
            # Backend will programmatically fill missing days (see _validate_structure method)
            # This reduces token waste and model confusion by ~80% for single-day slots
            if available_days and days_to_generate and len(days_to_generate) < 5:
                # Only request specific days - backend will fill the rest
                all_days_requirement = f"""
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ONLY the following days: {", ".join(days_to_generate)}
- Generate FULL, DETAILED content for {days_text} with all required fields
- **DO NOT include keys for other days** (monday, tuesday, wednesday, thursday, friday that are NOT in the list above)
- **CRITICAL: USE THE SINGLE-SLOT STRUCTURE** (do not use a "slots" array inside each day; put unit_lesson, objective, etc. directly inside the day object)
- The backend will automatically add missing days - focus your token budget on high-quality content for the requested days
"""
            else:
                all_days_requirement = """
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ALL 5 days: monday, tuesday, wednesday, thursday, friday
- Generate FULL, DETAILED content for ALL days with all required fields
- **CRITICAL: USE THE SINGLE-SLOT STRUCTURE** (do not use a "slots" array inside each day; put unit_lesson, objective, etc. directly inside the day object)
"""

            no_school_instruction = (
                '5. **For days NOT in the list above: Use minimal "No School" placeholders** (see structure above)\n'
                '   **IMPORTANT**: Even for "No School" days, preserve ANY content that exists in the DOCX (especially tailored_instruction.original_content, co_teaching_model, etc.). Only use "No School" placeholders for fields that are TRULY missing from the DOCX.\n'
                '   **SCHEMA COMPLIANCE**: For "No School" days you MUST still satisfy the schema: tailored_instruction.co_teaching_model.wida_context at least 30 characters; phase_plan at least 2 phases with minutes >= 1 each (no zero minutes); assessment.bilingual_overlay.supports_by_level.levels_1_2, levels_3_4, levels_5_6 at least 20 characters each. Do not use "N/A" or "No School day." where the schema requires longer strings.'
            )
            focus_instruction = f"5. **Focus your response on generating high-quality content for {days_text} only** - you have limited tokens, use them efficiently"

            output_req_5 = (
                focus_instruction
                if available_days and days_to_generate and len(days_to_generate) < 5
                else no_school_instruction
            )

            output_req_1 = (
                f"1. **CRITICAL: Your JSON MUST include ONLY the following days: {', '.join(days_to_generate)}** - Do NOT include keys for other days (they will be added programmatically by the backend)"
                if available_days and days_to_generate and len(days_to_generate) < 5
                else "1. **MANDATORY: Your JSON MUST include ALL 5 days (monday, tuesday, wednesday, thursday, friday)** - This is a schema requirement that cannot be skipped"
            )

            full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the schema provided via API
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)

Before generating any JSON, you MUST follow these syntax rules:

1. **ALL property names MUST be in double quotes**
   - CORRECT: {{"key": "value"}}
   - INCORRECT: {{key: "value"}} or {{'key': "value"}}

2. **ALL string values MUST be in double quotes**
   - CORRECT: {{"name": "John"}}
   - INCORRECT: {{"name": John}} or {{"name": 'John'}}

3. **NO unquoted property names**
   - The error "Expecting property name enclosed in double quotes" means you used an unquoted key
   - Example: {{key: value}} is INVALID - must be {{"key": value}}

4. **Proper escaping of special characters**
   - Quotes inside strings: "He said \\"hello\\"" (CRITICAL: ALL quotes inside string values must be escaped)
   - Example: "wida_mapping": "Target \\"levels\\": 1-4" (NOT "Target "levels": 1-4")
   - The error "Expecting ',' delimiter" often means you have an unescaped quote inside a string
   - Newlines: "Line 1\\nLine 2"
   - Backslashes: "Path: C:\\\\Users"

5. **NO trailing commas**
   - CORRECT: {{"a": 1, "b": 2}}
   - INCORRECT: {{"a": 1, "b": 2,}}

6. **NO comments**
   - CORRECT: {{"key": "value"}}
   - INCORRECT: {{"key": "value"}} // comment

CRITICAL: Your JSON must be valid JSON syntax. Invalid JSON will cause parsing errors.
Remember: ALL keys must be quoted. {{key: value}} is INVALID.

{all_days_requirement}

{prompt}

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

## SELF-CHECK BEFORE RETURNING JSON:

Before returning your JSON response, verify:
1. [OK] All property names are in double quotes (scan for unquoted keys)
2. [OK] All string values are properly closed with double quotes
3. [OK] No trailing commas after last items in objects/arrays
4. [OK] All special characters in strings are properly escaped
5. [OK] No comments (// or /* */) in the JSON
6. [OK] The JSON structure matches the schema exactly

If ANY check fails, fix it before returning.

OUTPUT REQUIREMENTS:
{output_req_1}
2. Generate JSON matching the schema structure provided via API
3. {days_instruction}
4. **For {days_text}: Populate with FULL, DETAILED content - no placeholders, no "TBD", no minimal data**
{output_req_5}
6. **CRITICAL: vocabulary_cognates (exactly 6 items) and sentence_frames (exactly 8 items) are MANDATORY for ALL lesson days** - Never omit these fields

**CRITICAL: pattern_id ENUM VALUES (MUST USE EXACTLY ONE):**
The `misconceptions.linguistic_note.pattern_id` field MUST be one of these exact values:
- 'subject_pronoun_omission'
- 'adjective_placement'
- 'past_tense_ed_dropping'
- 'preposition_depend_on'
- 'false_cognate_actual'
- 'false_cognate_library'
- 'default'

**DO NOT** generate creative pattern names. Use ONLY the values listed above.

**CRITICAL: proficiency_level ENUM VALUES:**
The `sentence_frames[].proficiency_level` field MUST be one of:
- 'levels_1_2'
- 'levels_3_4'
- 'levels_5_6'

**CRITICAL: wida_mapping PATTERN REQUIREMENT:**
The `assessment.bilingual_overlay.wida_mapping` field MUST match this pattern:
Pattern: `.*(Explain|Narrate|Inform|Argue).*ELD.*Level`

**Required Format:**
- Must contain one of: Explain, Narrate, Inform, or Argue
- Must contain "ELD" followed by standard code
- Must contain the word "Level" (or "Levels")

**CORRECT Examples:**
- "Explain; ELD-SS.6-8.Explain.Writing; Levels 2-4"
- "Inform; ELD-MA.2-3.Inform.Reading; Level 3"
- "Narrate; ELD-LA.4-5.Narrate.Speaking; Levels 1-2"

**INCORRECT Examples (will fail validation):**
- "Inform; ELD-MA.2-3.Infor...ey Language Use: Inform" (missing "Level")
- "Explain the concept using ELD standards" (missing pattern structure)
"""
            return full_prompt
        else:
            # Full prompt with schema examples for non-structured outputs
            schema_example = self._build_schema_example(
                week_of, grade, subject, teacher_name, homeroom
            )

            full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the exact schema structure below
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)

Before generating any JSON, you MUST follow these syntax rules:

1. **ALL property names MUST be in double quotes**
   - CORRECT: {{"key": "value"}}
   - INCORRECT: {{key: "value"}} or {{'key': "value"}}

2. **ALL string values MUST be in double quotes**
   - CORRECT: {{"name": "John"}}
   - INCORRECT: {{"name": John}} or {{"name": 'John'}}

3. **NO unquoted property names**
   - The error "Expecting property name enclosed in double quotes" means you used an unquoted key
   - Example: {{key: value}} is INVALID - must be {{"key": value}}

4. **Proper escaping of special characters**
   - Quotes inside strings: "He said \\"hello\\"" (CRITICAL: ALL quotes inside string values must be escaped)
   - Example: "wida_mapping": "Target \\"levels\\": 1-4" (NOT "Target "levels": 1-4")
   - The error "Expecting ',' delimiter" often means you have an unescaped quote inside a string
   - Newlines: "Line 1\\nLine 2"
   - Backslashes: "Path: C:\\\\Users"

5. **NO trailing commas**
   - CORRECT: {{"a": 1, "b": 2}}
   - INCORRECT: {{"a": 1, "b": 2,}}

6. **NO comments**
   - CORRECT: {{"key": "value"}}
   - INCORRECT: {{"key": "value"}} // comment

CRITICAL: Your JSON must be valid JSON syntax. Invalid JSON will cause parsing errors.
Remember: ALL keys must be quoted. {{key: value}} is INVALID.

{prompt}

---

REQUIRED JSON SCHEMA STRUCTURE:

You MUST output JSON that matches this EXACT structure:

{schema_example}

CRITICAL REQUIREMENTS:
1. Root object has "metadata" and "days" keys
2. metadata.week_of format: "MM/DD-MM/DD" (e.g., "10/6-10/10")
3. days object must include: {days_text.lower()}
4. {days_instruction}
5. Each day has: unit_lesson, objective, anticipatory_set, tailored_instruction, misconceptions, assessment, homework
6. objective has: content_objective, student_goal, wida_objective
7. wida_objective MUST include ELD standard format: (ELD-XX.#-#.Function.Domain)
8. anticipatory_set has: original_content, bilingual_bridge
9. tailored_instruction has: original_content, co_teaching_model, ell_support (3-5 items), special_needs_support (1-2 items), materials
10. co_teaching_model has: model_name, rationale, wida_context, phase_plan (at least 2 phases, e.g. Warmup+Practice or Input+Closure), implementation_notes
11. Each ell_support item has: strategy_id, strategy_name, implementation, proficiency_levels
12. misconceptions has: original_content, linguistic_note
13. assessment has: primary_assessment, bilingual_overlay
14. homework has: original_content, family_connection

**CRITICAL: pattern_id ENUM VALUES (MUST USE EXACTLY ONE):**
The `misconceptions.linguistic_note.pattern_id` field MUST be one of these exact values:
- 'subject_pronoun_omission'
- 'adjective_placement'
- 'past_tense_ed_dropping'
- 'preposition_depend_on'
- 'false_cognate_actual'
- 'false_cognate_library'
- 'default'

**DO NOT** generate creative pattern names. Use ONLY the values listed above.

**CRITICAL: proficiency_level ENUM VALUES:**
The `sentence_frames[].proficiency_level` field MUST be one of:
- 'levels_1_2'
- 'levels_3_4'
- 'levels_5_6'

**CRITICAL: wida_mapping PATTERN REQUIREMENT:**
The `assessment.bilingual_overlay.wida_mapping` field MUST match this pattern:
Pattern: `.*(Explain|Narrate|Inform|Argue).*ELD.*Level`

**Required Format:**
- Must contain one of: Explain, Narrate, Inform, or Argue
- Must contain "ELD" followed by standard code
- Must contain the word "Level" (or "Levels")

**CORRECT Examples:**
- "Explain; ELD-SS.6-8.Explain.Writing; Levels 2-4"
- "Inform; ELD-MA.2-3.Inform.Reading; Level 3"
- "Narrate; ELD-LA.4-5.Narrate.Speaking; Levels 1-2"

**INCORRECT Examples (will fail validation):**
- "Inform; ELD-MA.2-3.Infor...ey Language Use: Inform" (missing "Level")
- "Explain the concept using ELD standards" (missing pattern structure)

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

## SELF-CHECK BEFORE RETURNING JSON:

Before returning your JSON response, verify:
1. [OK] All property names are in double quotes (scan for unquoted keys)
2. [OK] All string values are properly closed with double quotes
3. [OK] No trailing commas after last items in objects/arrays
4. [OK] All special characters in strings are properly escaped
5. [OK] No comments (// or /* */) in the JSON
6. [OK] The JSON structure matches the schema exactly

If ANY check fails, fix it before returning.

OUTPUT REQUIREMENTS:
1. Generate JSON matching the EXACT schema structure above
2. {days_instruction}
3. **IMPORTANT: The schema requires all 5 days, but only populate {days_text} with FULL, DETAILED content**
4. **For days NOT in the list above, use minimal "No School" placeholders** (this is a single-lesson document)
   **IMPORTANT**: Even for "No School" days, preserve ANY content that exists in the DOCX (especially tailored_instruction.original_content, co_teaching_model, etc.). Only use "No School" placeholders for fields that are TRULY missing from the DOCX.
   **SCHEMA COMPLIANCE**: For "No School" days you MUST still satisfy the schema: tailored_instruction.co_teaching_model.wida_context at least 30 characters; phase_plan at least 2 phases with minutes >= 1 each (no zero minutes); assessment.bilingual_overlay.supports_by_level.levels_1_2, levels_3_4, levels_5_6 at least 20 characters each. Do not use "N/A" or "No School day." where the schema requires longer strings.
5. **Each requested day must have complete data - no placeholders, no "TBD", no minimal data**
6. WIDA objective must include proper ELD standard for each requested day
7. Include 3-5 ELL support strategies for each requested day
8. Add Portuguese cognates in bilingual_bridge for each requested day
9. Include co-teaching model with phase plan for each requested day
10. Add linguistic misconception notes for each requested day
11. Create bilingual assessment overlay for each requested day
12. Add family connection in Portuguese for each requested day

**WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION (CRITICAL):**

The four language domains (Listening, Reading, Speaking, Writing) are the structural backbone of WIDA's framework, but NOT every lesson must include all four. Select 1-4 domains based on:

1. **Lesson Activities Analysis**: 
   - Analyze the activities in `tailored_instruction.co_teaching_model.phase_plan`
   - Analyze the strategies in `tailored_instruction.ell_support`
   - Each strategy supports specific domains (e.g., Think-Pair-Share → Listening + Speaking)
   
2. **Content Objectives**: 
   - What students need to do determines which domains are necessary
   - If students must read → include Reading
   - If students must write → include Writing  
   - If students must discuss → include Speaking + Listening
   - If students must present → include Speaking (possibly + Writing for notes)

3. **Activity-to-Domain Mapping**:
   - Think-Pair-Share → Listening + Speaking
   - Reading comprehension → Reading (possibly + Writing if responses)
   - Writing workshop → Writing (possibly + Reading if mentor texts)
   - Direct instruction/lecture → Listening (possibly + Writing if note-taking)
   - Literature circles → Reading + Speaking + Listening
   - Research projects → Reading + Writing (possibly + Speaking if presentations)
   - Jigsaw activities → Reading + Speaking + Listening

**objective.student_goal REQUIREMENTS:**
- Format: "I will..." (first person, child-friendly language)
- Include ONLY the domains (1-4) that the lesson activities actually support
- Explicitly name each selected domain with child-friendly verbs (e.g., "listen to...", "read...", "speak...", "write...") so students immediately know which language skills they will practice; if multiple domains are targeted, mention each of them inside the sentence
- Append a domain tag at the end of the sentence using parentheses with comma-separated lowercase domains (e.g., `(listening, speaking)` or `(reading)`), followed immediately by a period; list only the domains actually practiced
- Use simple, age-appropriate language that a child can understand
- Keep to 1 sentence, maximum 12-15 words for clarity (not counting the domain tag)
- Structure: "I will [domain actions] about/to [content focus] (domain list)"
- Domain-specific child-friendly verbs:
  - Listening: "listen to", "hear", "pay attention to"
  - Reading: "read", "look at", "find in the text"
  - Speaking: "speak", "tell", "share", "talk about", "say"
  - Writing: "write", "put in writing", "write down"
- **Self-check:** Before returning the JSON, re-read every `objective.student_goal`. If any day is missing at least one of the verbs `listen`, `read`, `speak`, or `write` (or their -ing forms) **or** the sentence does not end with the parentheses domain tag plus trailing period described above, fix it before returning the response.

**Examples by domain count:**
- 1 domain (Writing only): "I will write a paragraph about the water cycle."
- 2 domains (Listening + Speaking): "I will listen to my partner and speak to share my ideas about fractions."
- 2 domains (Reading + Writing): "I will read the story and write about my favorite part."
- 3 domains (Reading + Speaking + Writing): "I will read the text, speak with my group, and write my answer."
- 4 domains (All): "I will listen to the explanation, read the text, speak with my partner, and write my response."

        **objective.wida_objective REQUIREMENTS:**
        - Include ONLY the domains (1-4) that the lesson activities actually support
        - Explicitly name each domain used in the objective text
        - Use appropriate ELD code format with domain notation:
          - Single domain: ELD-XX.#-#.Function.Domain (e.g., ELD-SS.6-8.Explain.Writing)
          - Multiple domains: ELD-XX.#-#.Function.Domain1/Domain2 (e.g., ELD-SS.6-8.Explain.Listening/Speaking)
          - All four: ELD-XX.#-#.Function.Listening/Reading/Speaking/Writing
        - Structure: "Students will [function] [content] through [domain actions], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains])."
        - **Pattern reminder:** The ELD code must include all four segments (`ELD-[Standard].[GradeCluster].[Function].[Domains]`). Example: `ELD-LA.2-3.Explain.Writing` (single domain) or `ELD-LA.2-3.Explain.Listening/Writing` (multiple domains). Formats like `ELD-LA.2-3.Explain/Writing` are invalid because the function segment is missing.
        - **Function-to-domain separator rule:** Always insert a period between the Function segment and the first domain (e.g., `.Explain.Listening`). Never insert a slash between the Function and the first domain; slashes are only used to separate multiple domains after the Function segment.
        - **Pattern reminder:** The ELD code must end with the domain suffix (e.g., `.Listening/Speaking`). Never return `ELD-LA.2-3.Explain` without the domain segment.
        - **Self-check:** Before returning JSON, confirm each `objective.wida_objective` includes an ELD code that matches `ELD-[Standard].[GradeCluster].[Function].[Domains]` with Domains drawn from Listening/Reading/Speaking/Writing. If a code fails this pattern, rewrite it until it passes.

**Examples by domain count:**
- 1 domain (Writing): "Students will explain the water cycle through writing a paragraph describing each stage, using sentence frames and vocabulary supports appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Writing)."
- 2 domains (Listening + Speaking): "Students will compare fractions through listening to explanations and speaking with partners using sentence frames, using visual supports appropriate for WIDA levels 2-3 (ELD-MA.3-5.Compare.Listening/Speaking)."
- 3 domains (Reading + Speaking + Writing): "Students will analyze characters through reading the text, speaking in literature circles, and writing character descriptions, using graphic organizers and sentence frames appropriate for WIDA levels 3-5 (ELD-LA.4-5.Analyze.Reading/Speaking/Writing)."
- 4 domains (All): "Students will explain historical events through listening to primary sources, reading documents, speaking in discussions, and writing summaries, using cognates and sentence frames appropriate for WIDA levels 2-4 (ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)."

**CRITICAL**: Do NOT force all four domains if the lesson activities don't support them. Analyze the actual activities in phase_plan and ell_support, then select domains accordingly. The goal is authentic alignment between activities and language domains.

**CONTENT PRESERVATION RULES (CRITICAL):**
12. **unit_lesson field**: Copy EXACTLY from input - DO NOT transform, paraphrase, or translate. Preserve all hyperlink text verbatim.
13. **objective.content_objective**: Copy EXACTLY from input primary teacher's objective - DO NOT transform or paraphrase.
14. **Hyperlink formatting**: When multiple hyperlinks exist, format each on its own line (use \\n) for readability:
    Example:
    "LESSON 9: MEASURE TO FIND THE AREA\\nLESSON 10: SOLVE AREA PROBLEMS\\nLESSON 11: AREA AND THE MULTIPLICATION TABLE"
    NOT: "LESSON 9: MEASURE TO FIND THE AREA LESSON 10: SOLVE AREA PROBLEMS..."

Generate the complete JSON now with FULL DATA FOR {days_count_text.upper()}. Output ONLY the JSON, nothing else.
"""

        return full_prompt

    def _parse_validation_errors(self, validation_error: str) -> Dict[str, Any]:
        """
        Parse Pydantic validation error messages to extract actionable feedback.

        Args:
            validation_error: Validation error message string (may contain multiple errors)

        Returns:
            Dict with:
            - error_type: 'enum', 'pattern', 'missing_field', 'extra_field', 'structure_confusion', 'unknown'
            - errors: List of parsed error dicts, each with:
              - field_path: Full path to error field
              - error_type: Specific error type
              - allowed_values: List of allowed values (for enum errors)
              - pattern_requirement: Pattern string (for pattern errors)
              - invalid_value: The invalid value provided (if available)
              - guidance: Specific fix instructions
        """

        parsed_errors = []
        structure_confusion_detected = False
        enum_errors = []
        pattern_errors = []
        missing_field_errors = []
        extra_field_errors = []

        # Split error message into individual errors (Pydantic errors are often multi-line)
        error_lines = validation_error.split("\n")

        for idx, line in enumerate(error_lines):
            line = line.strip()
            if not line:
                continue

            # Detect structure confusion
            # Note: Multi-slot structures are for merged data only, not AI generation
            # If AI tries to generate multi-slot, it indicates confusion
            if "DayPlanSingleSlot" in line and "slots" in line.lower():
                structure_confusion_detected = True
            if "DayPlanMultiSlot" in line and (
                "unit_lesson" in line.lower() or "objective" in line.lower()
            ):
                structure_confusion_detected = True
            if "Extra inputs are not permitted" in line and (
                "slots" in line.lower() or "DayPlan" in line
            ):
                structure_confusion_detected = True

            # Parse field path (format: "days.monday.DayPlanSingleSlot.field_name")
            # Pydantic errors typically start with "days." followed by day name and field path
            # Match field paths that start with "days." or other lowercase prefixes with dots
            field_match = re.search(
                r"\b(days\.[a-zA-Z_]+\.[a-zA-Z_]+(?:\.[a-zA-Z_]+)*)\b", line
            )
            if not field_match:
                # Fallback: match any lowercase-starting path with at least 2 dots
                field_match = re.search(r"\b([a-z_]+(?:\.[a-zA-Z_]+){2,})\b", line)

            # Check if next lines have error message (common Pydantic format)
            # Pydantic errors can span 2-3 lines: field_path, error message, [type=...]
            next_line = ""
            next_next_line = ""
            if idx + 1 < len(error_lines):
                next_line = error_lines[idx + 1].strip()
            if idx + 2 < len(error_lines):
                next_next_line = error_lines[idx + 2].strip()

            if field_match:
                field_path = field_match.group(1)

                # Detect error types
                # Combine current line and next 2 lines for error detection (covers multi-line errors)
                combined_line = line
                if next_line:
                    combined_line += " " + next_line
                if next_next_line:
                    combined_line += " " + next_next_line
                error_info = {
                    "field_path": field_path,
                    "error_type": "unknown",
                    "guidance": combined_line,
                }

                # Enum error: "Input should be 'value1', 'value2', ... or 'default'"
                # Check current line and next line for enum indicators
                enum_match = re.search(
                    r"Input should be '([^']+)'(?:, '([^']+)')*.*or '([^']+)'",
                    combined_line,
                )
                if (
                    enum_match
                    or "is not one of" in combined_line
                    or "type=enum" in combined_line
                ):
                    error_info["error_type"] = "enum"
                    # Extract allowed values from combined line (error message may be on next line)
                    allowed_values = re.findall(r"'([^']+)'", combined_line)
                    if allowed_values:
                        error_info["allowed_values"] = allowed_values
                        error_info["guidance"] = (
                            f"Field '{field_path}' must be one of: {', '.join(allowed_values)}"
                        )
                    # Extract invalid value if present (may be on same or next line)
                    value_match = re.search(r"input_value='([^']+)'", combined_line)
                    if value_match:
                        error_info["invalid_value"] = value_match.group(1)
                    enum_errors.append(error_info)

                # Pattern error: "String should match pattern 'pattern'"
                # Check for pattern error indicators, but avoid matching field names like "pattern_id"
                elif (
                    "string should match pattern" in combined_line.lower()
                    or "string_pattern_mismatch" in combined_line
                    or (
                        re.search(r"pattern\s+'([^']+)'", combined_line, re.IGNORECASE)
                        and "should match" in combined_line.lower()
                    )
                ):
                    error_info["error_type"] = "pattern"
                    pattern_match = re.search(r"pattern '([^']+)'", combined_line)
                    if pattern_match:
                        error_info["pattern_requirement"] = pattern_match.group(1)
                    # Extract invalid value if present
                    value_match = re.search(r"input_value='([^']+)'", combined_line)
                    if value_match:
                        error_info["invalid_value"] = value_match.group(1)
                    error_info["guidance"] = (
                        f"Field '{field_path}' must match the required pattern. See examples in prompt."
                    )
                    pattern_errors.append(error_info)

                # Missing field error
                elif (
                    "Field required" in combined_line or "type=missing" in combined_line
                ):
                    error_info["error_type"] = "missing_field"
                    error_info["guidance"] = (
                        f"Field '{field_path}' is required but missing. Please add this field."
                    )
                    missing_field_errors.append(error_info)

                # Extra field error
                elif (
                    "Extra inputs are not permitted" in combined_line
                    or "extra_forbidden" in combined_line
                ):
                    error_info["error_type"] = "extra_field"
                    # Extract the extra field name
                    extra_match = re.search(r"\.([a-z_]+)\s", combined_line)
                    if extra_match:
                        error_info["extra_field"] = extra_match.group(1)
                    error_info["guidance"] = (
                        f"Field '{field_path}' contains an extra field that is not allowed. Remove it."
                    )
                    extra_field_errors.append(error_info)

                parsed_errors.append(error_info)

        return {
            "errors": parsed_errors,
            "structure_confusion_detected": structure_confusion_detected,
            "enum_errors": enum_errors,
            "pattern_errors": pattern_errors,
            "missing_field_errors": missing_field_errors,
            "extra_field_errors": extra_field_errors,
            "has_errors": len(parsed_errors) > 0,
        }

    def _build_retry_prompt(
        self,
        original_prompt: str,
        validation_error: Optional[str],
        retry_count: int,
        available_days: Optional[List[str]] = None,
        error_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a retry prompt with feedback about validation errors.

        Args:
            original_prompt: The original prompt sent to the LLM
            validation_error: The validation error message
            retry_count: Current retry attempt number (1-based)
            available_days: Optional list of specific days requested
            error_analysis: Optional error analysis dictionary with detailed error context

        Returns:
            Enhanced prompt with validation feedback
        """

        # Determine which days are required
        days_to_generate = (
            [d.lower() for d in available_days]
            if available_days
            else ["monday", "tuesday", "wednesday", "thursday", "friday"]
        )

        if len(days_to_generate) < 5:
            days_str = ", ".join(days_to_generate)
            days_requirement = f"REQUIRED DAYS: {days_str}"
            vocab_rule_1 = f"1. **vocabulary_cognates is MANDATORY**: For the requested days ({days_str}), each day must have exactly 6 English-Portuguese word pairs. **CRITICAL: Do not skip this field for any of the requested days.**"
            sentence_rule_2 = "2. **sentence_frames is MANDATORY**: For the requested days, each day must have exactly 8 sentence frames. This field cannot be omitted or empty."
            combined_rule_3 = f"3. **Both fields are required for ALL requested days** ({days_str}). Ensure vocabulary_cognates is included for every single requested day."
            structure_rule_4 = f"4. **Check your JSON structure**: Ensure keys exist ONLY for: {days_str}. Do not generate other days."
            regenerate_instruction = f"Please regenerate the lesson plan JSON for {days_str} with all required fields included."
        else:
            vocab_rule_1 = "1. **vocabulary_cognates is MANDATORY**: Every day (Monday, Tuesday, Wednesday, Thursday, Friday) must have exactly 6 English-Portuguese word pairs in the `vocabulary_cognates` array. This field cannot be omitted, empty, or have zero items. **CRITICAL: Do not skip this field for any day - it is required for ALL lesson days without exception.**"
            sentence_rule_2 = "2. **sentence_frames is MANDATORY**: Every day must have exactly 8 sentence frames/stems/questions in the `sentence_frames` array (3 for levels_1_2, 3 for levels_3_4, 2 for levels_5_6). This field cannot be omitted or empty."
            combined_rule_3 = "3. **Both fields are required for ALL lesson days** (Monday, Tuesday, Wednesday, Thursday, Friday), even if the lesson content is minimal. Extract vocabulary from lesson objectives or identify essential academic vocabulary that supports the lesson's core concepts. **Ensure vocabulary_cognates is included for every single day.**"
            structure_rule_4 = "4. **Check your JSON structure**: Ensure all required fields are present and properly formatted according to the schema."
            regenerate_instruction = "Please regenerate the complete lesson plan JSON with all required fields included. Do not omit vocabulary_cognates or sentence_frames for any day."

        # Build error context section if error analysis is provided
        error_context_section = ""
        if error_analysis:
            error_type = error_analysis.get("error_type", "unknown")
            error_pos = error_analysis.get("error_position")
            error_line = error_analysis.get("error_line")
            error_col = error_analysis.get("error_column")
            problematic_snippet = error_analysis.get("problematic_snippet", "")
            day_being_generated = error_analysis.get("day_being_generated")
            field_being_generated = error_analysis.get("field_being_generated")

            error_context_section = "\n## JSON SYNTAX ERROR DETECTED\n\n"
            error_context_section += "Your previous response had a JSON syntax error:\n"
            error_context_section += f"- Error Type: {error_type}\n"
            if error_line and error_col:
                error_context_section += (
                    f"- Location: Line {error_line}, Column {error_col}"
                )
            if error_pos:
                error_context_section += f" (Character {error_pos})"
            error_context_section += "\n"

            if day_being_generated:
                error_context_section += (
                    f"- Day being generated: {day_being_generated}\n"
                )
            if field_being_generated:
                error_context_section += (
                    f"- Field being generated: {field_being_generated}\n"
                )

            if problematic_snippet:
                error_context_section += (
                    f"\nProblematic JSON snippet:\n```\n{problematic_snippet}\n```\n\n"
                )

            # Add specific guidance based on error type
            if error_type == "unquoted_property_name":
                error_context_section += (
                    "What's wrong: You used an unquoted property name.\n\n"
                )
                error_context_section += (
                    "How to fix: ALL property names must be in double quotes.\n\n"
                )
                error_context_section += "Example:\n"
                error_context_section += '- WRONG: {key: "value"}\n'
                error_context_section += '- CORRECT: {"key": "value"}\n\n'
            elif error_type == "incomplete_string":
                error_context_section += "What's wrong: A string value is not properly closed with a closing quote.\n\n"
                error_context_section += "How to fix: Ensure all string values are closed with double quotes.\n\n"
            elif error_type == "trailing_comma":
                error_context_section += "What's wrong: There is a trailing comma after the last item in an object or array.\n\n"
                error_context_section += (
                    "How to fix: Remove trailing commas. JSON does not allow them.\n\n"
                )

            error_context_section += "## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)\n\n"
            error_context_section += (
                "1. **ALL property names MUST be in double quotes**\n"
            )
            error_context_section += '   - CORRECT: {"key": "value"}\n'
            error_context_section += '   - INCORRECT: {key: "value"}\n\n'
            error_context_section += (
                "2. **ALL string values MUST be in double quotes**\n"
            )
            error_context_section += "3. **NO unquoted property names**\n"
            error_context_section += "   - The error 'Expecting property name' means you used an unquoted property name.\n"
            error_context_section += (
                "   - ALL property names must be in double quotes.\n\n"
            )

        # Use pre-parsed errors if available, otherwise parse now
        # This avoids redundant parsing when called from validation flow
        parsed_errors = None
        if error_analysis and "validation_errors" in error_analysis:
            # Use already parsed errors from validation flow
            parsed_errors = error_analysis["validation_errors"]
        elif validation_error:
            # Fallback: parse errors if not already parsed (e.g., if called independently)
            parsed_errors = self._parse_validation_errors(validation_error)

        # Build structured error feedback
        structured_feedback = ""

        if parsed_errors and parsed_errors.get("structure_confusion_detected"):
            structured_feedback += """
## CRITICAL: STRUCTURE CONFUSION DETECTED

You are mixing DayPlanSingleSlot and DayPlanMultiSlot structures.

**IMPORTANT:** The schema only allows single-slot structures for AI generation. Multi-slot structures are created by merging multiple lessons, NOT by AI.

**CORRECT STRUCTURE (DayPlanSingleSlot - ALWAYS USE THIS):**
```json
{
  "unit_lesson": "...",
  "objective": {...},
  "vocabulary_cognates": [...],
  "sentence_frames": [...],
  ...
}
```

**INCORRECT (DO NOT USE):**
```json
{
  "slots": [...]  // DO NOT include this field - AI should never generate multi-slot
}
```

**Rule:** Always put fields directly in the day object. Never use a "slots" array. The schema only supports the single-slot structure for AI generation.

"""

        if parsed_errors and parsed_errors.get("enum_errors"):
            structured_feedback += "\n## ENUM VALUE ERRORS\n\n"
            for enum_error in parsed_errors["enum_errors"]:
                field_path = enum_error.get("field_path", "unknown")
                allowed_values = enum_error.get("allowed_values", [])
                invalid_value = enum_error.get("invalid_value", "unknown")

                structured_feedback += f"**Field:** `{field_path}`\n"
                structured_feedback += f"**You used:** `{invalid_value}`\n"
                if allowed_values:
                    # Format allowed values with quotes (can't use backslash in f-string expression)
                    allowed_values_str = ", ".join([f"'{v}'" for v in allowed_values])
                    structured_feedback += f"**Allowed values:** {allowed_values_str}\n"
                structured_feedback += "**Fix:** Use one of the allowed values exactly as listed above.\n\n"

        if parsed_errors and parsed_errors.get("pattern_errors"):
            structured_feedback += "\n## PATTERN MISMATCH ERRORS\n\n"
            for pattern_error in parsed_errors["pattern_errors"]:
                field_path = pattern_error.get("field_path", "unknown")
                pattern_req = pattern_error.get("pattern_requirement", "unknown")
                invalid_value = pattern_error.get("invalid_value", "unknown")

                structured_feedback += f"**Field:** `{field_path}`\n"
                structured_feedback += f"**Required pattern:** `{pattern_req}`\n"
                if invalid_value != "unknown":
                    structured_feedback += f"**Your value:** `{invalid_value}`\n"
                structured_feedback += "**Fix:** Ensure your value matches the pattern. See examples in original prompt.\n\n"

        if parsed_errors and parsed_errors.get("missing_field_errors"):
            structured_feedback += "\n## MISSING REQUIRED FIELDS\n\n"
            for missing_error in parsed_errors["missing_field_errors"]:
                field_path = missing_error.get("field_path", "unknown")
                structured_feedback += f"- `{field_path}` is required but missing. Please add this field.\n"
            structured_feedback += "\n"

        if parsed_errors and parsed_errors.get("extra_field_errors"):
            structured_feedback += "\n## EXTRA FIELDS (NOT ALLOWED)\n\n"
            for extra_error in parsed_errors["extra_field_errors"]:
                field_path = extra_error.get("field_path", "unknown")
                extra_field = extra_error.get("extra_field", "unknown")
                structured_feedback += f"- `{field_path}` contains field `{extra_field}` which is not allowed. Remove it.\n"
            structured_feedback += "\n"

        feedback_section = f"""
## CRITICAL: VALIDATION ERROR - RETRY ATTEMPT {retry_count}

Your previous response failed validation. Please fix the following issues:

{validation_error}

{structured_feedback}

{error_context_section}

### SPECIFIC REQUIREMENTS TO FIX:

{vocab_rule_1}

{sentence_rule_2}

{combined_rule_3}

{structure_rule_4}

{regenerate_instruction}

---
"""
        return feedback_section + "\n\n" + original_prompt

    def _build_schema_example(
        self,
        week_of: str,
        grade: str,
        subject: str,
        teacher_name: Optional[str],
        homeroom: Optional[str],
    ) -> str:
        """Build schema example with actual values.

        Note: This method only generates single-slot structure examples (DayPlanSingleSlot).
        The schema now enforces single-slot structure only to eliminate ambiguity.
        """

        def create_day(
            unit_lesson: str,
            *,
            wida_objective: str = "Students will explain [content] through [selected domains based on activities], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains]).",
            student_goal: str = "I will [domain actions based on lesson activities] about [content].",
            anticipatory_bridge: str = "...",
            co_teaching_model: Optional[Dict[str, Any]] = None,
            ell_support: Optional[List[Dict[str, Any]]] = None,
            special_needs_support: Optional[List[str]] = None,
            materials: Optional[List[str]] = None,
            linguistic_note: Optional[Dict[str, Any]] = None,
            bilingual_overlay: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            return {
                "unit_lesson": unit_lesson,
                "objective": {
                    "content_objective": "Students will...",
                    "student_goal": student_goal,
                    "wida_objective": wida_objective,
                },
                "anticipatory_set": {
                    "original_content": "...",
                    "bilingual_bridge": anticipatory_bridge,
                },
                "tailored_instruction": {
                    "original_content": "...",
                    "co_teaching_model": co_teaching_model or {},
                    "ell_support": ell_support or [],
                    "special_needs_support": special_needs_support or [],
                    "materials": materials or [],
                },
                "misconceptions": {
                    "original_content": "...",
                    "linguistic_note": linguistic_note or {},
                },
                "assessment": {
                    "primary_assessment": "...",
                    "bilingual_overlay": bilingual_overlay or {},
                },
                "homework": {"original_content": "...", "family_connection": "..."},
            }

        day_definitions = [
            (
                "monday",
                {
                    "unit_lesson": "Unit One Lesson One",
                    "wida_objective": "Students will explain the water cycle through listening to explanations, reading diagrams, speaking with partners, and writing paragraphs, using visual supports and sentence frames appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Listening/Reading/Speaking/Writing).",
                    "student_goal": "I will listen to explanations, read diagrams, speak with my partner, and write about the water cycle.",
                    "anticipatory_bridge": "Preview key cognates: word/palavra...",
                    "co_teaching_model": {
                        "model_name": "Station Teaching",
                        "rationale": "...",
                        "wida_context": "...",
                        "phase_plan": [
                            {
                                "phase_name": "Warmup",
                                "minutes": 5,
                                "bilingual_teacher_role": "...",
                                "primary_teacher_role": "...",
                            }
                        ],
                        "implementation_notes": ["..."],
                    },
                    "ell_support": [
                        {
                            "strategy_id": "cognate_awareness",
                            "strategy_name": "Cognate Awareness",
                            "implementation": "...",
                            "proficiency_levels": "Levels 2-5",
                        }
                    ],
                    "special_needs_support": ["..."],
                    "materials": ["..."],
                    "linguistic_note": {
                        "pattern_id": "subject_pronoun_omission",
                        "note": "...",
                        "prevention_tip": "...",
                    },
                    "bilingual_overlay": {
                        "instrument": "...",
                        "wida_mapping": "...",
                        "supports_by_level": {
                            "levels_1_2": "...",
                            "levels_3_4": "...",
                            "levels_5_6": "...",
                        },
                        "scoring_lens": "...",
                        "constraints_honored": "...",
                    },
                },
            ),
            (
                "tuesday",
                {
                    "unit_lesson": "Unit One Lesson Two",
                    "co_teaching_model": {
                        "model_name": "Station Teaching",
                        "rationale": "...",
                        "wida_context": "...",
                        "phase_plan": [],
                        "implementation_notes": [],
                    },
                    "linguistic_note": {
                        "pattern_id": "...",
                        "note": "...",
                        "prevention_tip": "...",
                    },
                    "bilingual_overlay": {
                        "instrument": "...",
                        "wida_mapping": "...",
                        "supports_by_level": {},
                        "scoring_lens": "...",
                        "constraints_honored": "...",
                    },
                },
            ),
            ("wednesday", {"unit_lesson": "Unit One Lesson Three"}),
            ("thursday", {"unit_lesson": "Unit One Lesson Four"}),
            ("friday", {"unit_lesson": "Unit One Lesson Five"}),
        ]

        example = {
            "metadata": {"week_of": week_of, "grade": grade, "subject": subject},
            "days": {
                day: create_day(**definition) for day, definition in day_definitions
            },
        }

        if teacher_name:
            example["metadata"]["teacher_name"] = teacher_name
        if homeroom:
            example["metadata"]["homeroom"] = homeroom

        return json.dumps(example, indent=2)

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
            if self._model_supports_structured_outputs():
                response_format = self._structured_response_format()
                if response_format:
                    try:
                        logger.info(
                            "using_openai_structured_outputs",
                            extra={"model": self.model},
                        )
                        return self._call_openai_chat_completion(
                            prompt, response_format=response_format
                        )
                    except Exception as exc:
                        logger.warning(
                            "structured_outputs_failed_fallback",
                            extra={"model": self.model, "error": str(exc)},
                        )

            if self._model_supports_json_mode():
                try:
                    logger.info(
                        "using_openai_json_mode",
                        extra={"model": self.model},
                    )
                    return self._call_openai_chat_completion(
                        prompt, response_format={"type": "json_object"}
                    )
                except Exception as exc:
                    logger.warning(
                        "json_mode_failed_fallback",
                        extra={"model": self.model, "error": str(exc)},
                    )

            logger.info("using_openai_legacy_mode", extra={"model": self.model})
            return self._call_openai_chat_completion(prompt)

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_completion_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract token usage
            usage = {
                "tokens_input": response.usage.input_tokens if response.usage else 0,
                "tokens_output": response.usage.output_tokens if response.usage else 0,
                "tokens_total": (
                    response.usage.input_tokens + response.usage.output_tokens
                )
                if response.usage
                else 0,
            }
            return response.content[0].text, usage

        raise ValueError(f"Unsupported provider: {self.provider}")

    def _pre_validate_json(
        self, json_string: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Pre-validate JSON string for common issues before parsing.

        Returns:
            (is_valid, error_message, fix_attempts)
        """
        issues = []
        fix_attempts = []
        fixed_string = json_string

        # Check 1: Unquoted property names (pattern: key: value where key is not quoted)
        # Look for word followed by colon, not preceded by quote
        unquoted_pattern = re.search(r'(?<!["\w])(\w+):\s*["\d\[\{]', json_string)
        if unquoted_pattern:
            issues.append(
                f"Unquoted property name detected at position {unquoted_pattern.start()}"
            )
            # Attempt fix: quote the key
            key_name = unquoted_pattern.group(1)
            fixed_string = re.sub(
                r'(?<!["\w])' + re.escape(key_name) + r":",
                f'"{key_name}":',
                fixed_string,
                count=1,
            )
            fix_attempts.append(f"Quoted property name '{key_name}'")

        # Check 2: Unmatched quotes
        quote_count = json_string.count('"')
        if quote_count % 2 != 0:
            issues.append("Unmatched quotes detected")
            # Try to find and close the last unclosed quote
            last_quote_idx = json_string.rfind('"')
            if last_quote_idx >= 0:
                # Check if it's actually unclosed
                remaining = json_string[last_quote_idx + 1 :]
                if '"' not in remaining or remaining.count('"') % 2 == 0:
                    fixed_string = (
                        json_string[: last_quote_idx + 1]
                        + '"'
                        + json_string[last_quote_idx + 1 :]
                    )
                    fix_attempts.append("Closed unmatched quote")

        # Check 3: Trailing commas
        trailing_comma = re.search(r",(\s*[}\]])", json_string)
        if trailing_comma:
            issues.append(f"Trailing comma at position {trailing_comma.start()}")
            # Attempt fix: remove trailing comma
            fixed_string = re.sub(r",(\s*[}\]])", r"\1", fixed_string)
            fix_attempts.append("Removed trailing comma")

        # Check 4: Incomplete strings near end
        trimmed = json_string.rstrip()
        if trimmed and not trimmed.endswith(("}", "]", '"', ",", ":", "[", "{")):
            # Check if ends with incomplete string value
            last_colon_quote = trimmed.rfind(': "')
            if last_colon_quote > 0:
                remaining_after_colon = trimmed[last_colon_quote + 3 :]
                if '"' not in remaining_after_colon:
                    issues.append("Incomplete string value detected near end")
                    fixed_string = trimmed + '"'
                    fix_attempts.append("Closed incomplete string value")

        # Check 5: Unescaped quotes in wida_mapping field (SPECIFIC FIX)
        # This targets the most common failure point: "wida_mapping": "Target WIDA "levels": 1-6"
        # We look for "wida_mapping followed by a colon and then a string value that contains internal quotes
        wida_mapping_matches = list(
            re.finditer(
                r'("wida_mapping"\s*:\s*")(.+?)(")(?=\s*[,}])',
                fixed_string,
                re.IGNORECASE | re.DOTALL,
            )
        )

        if wida_mapping_matches:
            # Sort matches in reverse to replace from end to avoid shifting indices
            for match in reversed(wida_mapping_matches):
                prefix, content, suffix = match.groups()

                # If content contains unescaped quotes (not \" already)
                if '"' in content and '\\"' not in content:
                    issues.append(
                        f"Unescaped quotes detected in wida_mapping field at position {match.start()}"
                    )

                    # Escape quotes that aren't already escaped
                    # We use a negative lookbehind to ensure we don't double escape
                    escaped_content = re.sub(r'(?<!\\)"', r'\\"', content)

                    # Reconstruction of the full string
                    fixed_match = prefix + escaped_content + suffix
                    fixed_string = (
                        fixed_string[: match.start()]
                        + fixed_match
                        + fixed_string[match.end() :]
                    )
                    fix_attempts.append("Escaped quotes in wida_mapping field")

        if issues:
            return (
                False,
                "; ".join(issues),
                {"fix_attempts": fix_attempts, "fixed_string": fixed_string},
            )
        return True, None, None

    def _identify_day_at_position(
        self, json_string: str, position: int
    ) -> Optional[str]:
        """Find which day is being generated at the given position"""
        # Look backwards from position for day keys
        text_before = json_string[:position]
        # Find the last day key before the position
        day_patterns = [
            ('"monday":', "monday"),
            ('"tuesday":', "tuesday"),
            ('"wednesday":', "wednesday"),
            ('"thursday":', "thursday"),
            ('"friday":', "friday"),
        ]
        last_day = None
        last_pos = -1
        for pattern, day_name in day_patterns:
            pos = text_before.rfind(pattern)
            if pos > last_pos:
                last_pos = pos
                last_day = day_name
        return last_day

    def _identify_field_at_position(
        self, json_string: str, position: int
    ) -> Optional[str]:
        """Find which field is being generated at the given position"""
        # Common field patterns
        field_patterns = [
            ('"unit_lesson":', "unit_lesson"),
            ('"objective":', "objective"),
            ('"anticipatory_set":', "anticipatory_set"),
            ('"tailored_instruction":', "tailored_instruction"),
            ('"misconceptions":', "misconceptions"),
            ('"assessment":', "assessment"),
            ('"homework":', "homework"),
            ('"content_objective":', "content_objective"),
            ('"student_goal":', "student_goal"),
            ('"wida_objective":', "wida_objective"),
            ('"bilingual_bridge":', "bilingual_bridge"),
            ('"co_teaching_model":', "co_teaching_model"),
            ('"ell_support":', "ell_support"),
            ('"vocabulary_cognates":', "vocabulary_cognates"),
            ('"sentence_frames":', "sentence_frames"),
        ]
        text_before = json_string[:position]
        last_field = None
        last_pos = -1
        for pattern, field_name in field_patterns:
            pos = text_before.rfind(pattern)
            if pos > last_pos:
                last_pos = pos
                last_field = field_name
        return last_field

    def _detect_error_type(
        self, error: json.JSONDecodeError, json_string: str, error_pos: int
    ) -> str:
        """Classify the type of JSON error"""
        error_msg = str(error).lower()
        if (
            "expecting property name" in error_msg
            or "property name enclosed" in error_msg
        ):
            return "unquoted_property_name"
        elif "expecting" in error_msg and "delimiter" in error_msg:
            return "syntax_error"
        elif "unterminated string" in error_msg or "unterminated" in error_msg:
            return "incomplete_string"
        elif "trailing comma" in error_msg or "trailing" in error_msg:
            return "trailing_comma"
        elif "expecting value" in error_msg:
            return "missing_value"
        else:
            return "unknown_error"

    def _analyze_characters_around_error(
        self, json_string: str, error_pos: int
    ) -> Dict[str, Any]:
        """Analyze character balance around error position"""
        context_start = max(0, error_pos - 200)
        context_end = min(len(json_string), error_pos + 200)
        context = json_string[context_start:context_end]

        # Count quotes, brackets, braces
        quote_count = context.count('"')
        bracket_count = context.count("[") - context.count("]")
        brace_count = context.count("{") - context.count("}")

        # Check if we're inside a string
        text_before = json_string[:error_pos]
        # Simple check: count quotes before position
        quotes_before = text_before.count('"')
        in_string = quotes_before % 2 != 0

        return {
            "quote_balance": quote_count % 2,
            "bracket_balance": bracket_count,
            "brace_balance": brace_count,
            "in_string": in_string,
        }

    def _find_complete_days_before_error(
        self, json_string: str, error_pos: int
    ) -> List[str]:
        """Find which days were successfully parsed before the error"""
        text_before = json_string[:error_pos]
        complete_days = []

        # Look for complete day structures (day key followed by closing brace)
        day_patterns = [
            ('"monday":', "monday"),
            ('"tuesday":', "tuesday"),
            ('"wednesday":', "wednesday"),
            ('"thursday":', "thursday"),
            ('"friday":', "friday"),
        ]

        for pattern, day_name in day_patterns:
            # Find the day key
            day_start = text_before.find(pattern)
            if day_start >= 0:
                # Check if we can find a matching closing brace for this day
                # This is a simplified check - look for the pattern and count braces
                after_day = text_before[day_start:]
                brace_count = 0
                in_string = False
                escape_next = False
                found_closing = False

                for i, char in enumerate(after_day):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == "\\":
                        escape_next = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if not in_string:
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0 and i > len(pattern):
                                found_closing = True
                                break

                if found_closing:
                    complete_days.append(day_name)

        return complete_days

    def _extract_problematic_snippet(
        self, json_string: str, error_pos: int, context_size: int = 200
    ) -> str:
        """Extract a snippet of code around the error position"""
        start = max(0, error_pos - context_size)
        end = min(len(json_string), error_pos + context_size)
        snippet = json_string[start:end]
        # Mark the error position
        relative_pos = error_pos - start
        if relative_pos < len(snippet):
            # Add a marker at the error position
            snippet = (
                snippet[:relative_pos] + " <-- ERROR HERE --> " + snippet[relative_pos:]
            )
        return snippet

    def _detect_truncation(self, json_string: str) -> bool:
        """Detect if the JSON response appears to be truncated"""
        trimmed = json_string.rstrip()
        # Check if ends abruptly (not with proper closing)
        if not trimmed.endswith(("}", "]", '"')):
            # Check if we're in the middle of a structure
            open_braces = trimmed.count("{")
            close_braces = trimmed.count("}")
            open_brackets = trimmed.count("[")
            close_brackets = trimmed.count("]")

            if open_braces > close_braces or open_brackets > close_brackets:
                return True
        return False

    def _analyze_json_error(
        self, json_string: str, error: json.JSONDecodeError
    ) -> Dict[str, Any]:
        """
        Analyze JSON parsing error to extract comprehensive context.

        Returns structured error information for logging and retry prompts.
        """
        error_pos = getattr(error, "pos", len(json_string))
        error_line = getattr(error, "lineno", None)
        error_col = getattr(error, "colno", None)

        # Extract context around error
        context_before = json_string[max(0, error_pos - 500) : error_pos]
        context_after = json_string[error_pos : min(len(json_string), error_pos + 500)]

        # Identify day/field being generated
        day_being_generated = self._identify_day_at_position(json_string, error_pos)
        field_being_generated = self._identify_field_at_position(json_string, error_pos)

        # Detect error type
        error_type = self._detect_error_type(error, json_string, error_pos)

        # Character analysis
        char_analysis = self._analyze_characters_around_error(json_string, error_pos)

        # Complete days before error
        complete_days = self._find_complete_days_before_error(json_string, error_pos)

        return {
            "error_type": error_type,
            "error_position": error_pos,
            "error_position_percent": round((error_pos / len(json_string)) * 100, 2)
            if len(json_string) > 0
            else 0,
            "error_line": error_line,
            "error_column": error_col,
            "context_before": context_before,
            "context_after": context_after,
            "problematic_snippet": self._extract_problematic_snippet(
                json_string, error_pos
            ),
            "day_being_generated": day_being_generated,
            "field_being_generated": field_being_generated,
            "response_length": len(json_string),
            "was_truncated": self._detect_truncation(json_string),
            "complete_days_before_error": complete_days,
            "character_analysis": char_analysis,
        }

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to JSON"""
        # Clean up response
        cleaned = response_text.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # Pre-validate JSON for common issues
        is_valid, pre_validation_error, pre_validation_fixes = self._pre_validate_json(
            cleaned
        )
        if (
            not is_valid
            and pre_validation_fixes
            and pre_validation_fixes.get("fixed_string")
        ):
            # Try the fixed version
            cleaned = pre_validation_fixes["fixed_string"]
            logger.info(
                "json_pre_validation_fixes_applied",
                extra={
                    "pre_validation_error": pre_validation_error,
                    "fixes_applied": pre_validation_fixes.get("fix_attempts", []),
                },
            )

        # Parse JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            original_error = str(e)

            # Analyze the error for comprehensive context
            error_analysis = self._analyze_json_error(cleaned, e)

            logger.warning(
                "json_parse_error_attempting_repair",
                extra={
                    "error": original_error,
                    "response_preview": cleaned[:500],
                    "response_length": len(cleaned),
                    "error_position": getattr(e, "pos", None),
                    "error_type": error_analysis.get("error_type"),
                    "error_position_percent": error_analysis.get(
                        "error_position_percent"
                    ),
                    "day_being_generated": error_analysis.get("day_being_generated"),
                    "field_being_generated": error_analysis.get(
                        "field_being_generated"
                    ),
                    "complete_days_before_error": error_analysis.get(
                        "complete_days_before_error"
                    ),
                    "was_truncated": error_analysis.get("was_truncated"),
                    "problematic_snippet": error_analysis.get("problematic_snippet"),
                    "character_analysis": error_analysis.get("character_analysis"),
                },
            )

            # Attempt to repair the JSON with error position and analysis
            error_pos = error_analysis.get("error_position")
            success, repaired, repair_error = repair_json(
                cleaned, error_pos, error_analysis
            )

            if success and repaired:
                logger.info(
                    "json_repair_successful",
                    extra={
                        "repair_message": repair_error,
                        "original_length": len(cleaned),
                        "repaired_length": len(repaired) if repaired else 0,
                    },
                )
                try:
                    parsed = json.loads(repaired)
                    logger.info(
                        "json_repair_parse_success",
                        extra={
                            "salvaged_days": list(parsed.get("days", {}).keys())
                            if isinstance(parsed, dict)
                            else [],
                        },
                    )
                    return parsed
                except json.JSONDecodeError as e2:
                    logger.error(
                        "json_repair_failed_to_parse",
                        extra={
                            "repair_error": str(e2),
                            "original_error": original_error,
                            "repaired_preview": repaired[:500] if repaired else None,
                        },
                    )

            # If repair failed, log detailed error with analysis and raise
            logger.error(
                "json_parse_error_repair_failed",
                extra={
                    "original_error": original_error,
                    "repair_error": repair_error,
                    "response_preview": cleaned[:500],
                    "response_length": len(cleaned),
                    "error_analysis": error_analysis,
                },
            )
            # Store error analysis in the exception for retry prompt
            error_with_analysis = ValueError(f"Failed to parse JSON: {original_error}")
            error_with_analysis.error_analysis = error_analysis  # type: ignore
            raise error_with_analysis

    def _validate_structure(
        self, lesson_json: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON structure matches schema.

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if structure is valid
            - error_message: Detailed error message if validation fails, None if valid
        """
        # Check root keys
        if "metadata" not in lesson_json or "days" not in lesson_json:
            error_msg = "Missing root keys: 'metadata' or 'days'"
            logger.error("schema_validation_failed", extra={"reason": error_msg})
            return False, error_msg

        # Check metadata
        metadata = lesson_json["metadata"]
        required_metadata = ["week_of", "grade", "subject"]
        for field in required_metadata:
            if field not in metadata:
                error_msg = f"Missing metadata.{field}"
                logger.error("schema_validation_failed", extra={"reason": error_msg})
                return False, error_msg

        # Check days
        days = lesson_json["days"]
        required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        missing_days = []
        for day in required_days:
            if day not in days:
                missing_days.append(day)
                logger.warning(
                    "schema_validation_missing_day",
                    extra={"day": day, "action": "Adding placeholder"},
                )

        # Fill in missing days with "No School" placeholders
        # Also check days that exist but have "No School" in unit_lesson - preserve any existing content
        if missing_days:
            no_school_placeholder = {
                "unit_lesson": "No School",
                "objective": {
                    "content_objective": "No School",
                    "student_goal": "No School",
                    "wida_objective": "No School",
                },
                "anticipatory_set": {
                    "original_content": "No School",
                    "bilingual_bridge": "No School",
                },
                "vocabulary_cognates": [],
                "sentence_frames": [],
                "tailored_instruction": {
                    "original_content": "No School",
                    "co_teaching_model": {},
                    "ell_support": [],
                    "special_needs_support": [],
                    "materials": [],
                },
                "misconceptions": {
                    "original_content": "No School",
                    "linguistic_note": {},
                },
                "assessment": {
                    "primary_assessment": "No School",
                    "bilingual_overlay": {},
                },
                "homework": {
                    "original_content": "No School",
                    "family_connection": "No School",
                },
            }

            for day in missing_days:
                days[day] = no_school_placeholder.copy()

        # For days that exist but have "No School" in unit_lesson, preserve any existing content
        # This handles cases where the DOCX has content in tailored_instruction or other fields
        # even though unit_lesson is "No School"
        for day_name in required_days:
            if day_name not in days:
                continue
            day_data = days[day_name]
            if day_data.get("unit_lesson") == "No School":
                # Check if there's actual content in tailored_instruction that should be preserved
                tailored_instruction = day_data.get("tailored_instruction", {})
                if isinstance(tailored_instruction, dict):
                    original_content = tailored_instruction.get("original_content", "")
                    # If original_content exists and is not empty/placeholder, preserve it
                    if (
                        original_content
                        and original_content.strip()
                        and original_content.strip() != "No School"
                    ):
                        # Content exists, preserve the entire tailored_instruction structure
                        logger.info(
                            "preserving_tailored_instruction_content",
                            extra={"day": day_name, "has_content": True},
                        )
                    # Preserve co_teaching_model if it has content
                    co_teaching = tailored_instruction.get("co_teaching_model", {})
                    if isinstance(co_teaching, dict) and co_teaching:
                        # Check if co_teaching_model has any meaningful content
                        has_co_teaching_content = (
                            co_teaching.get("model_name")
                            or co_teaching.get("rationale")
                            or (
                                isinstance(co_teaching.get("phase_plan"), list)
                                and len(co_teaching.get("phase_plan", [])) > 0
                            )
                        )
                        if has_co_teaching_content:
                            logger.info(
                                "preserving_co_teaching_model",
                                extra={"day": day_name, "has_content": True},
                            )
                    # Preserve ell_support, special_needs_support, materials if they have content
                    for field in ["ell_support", "special_needs_support", "materials"]:
                        field_value = tailored_instruction.get(field, [])
                        if isinstance(field_value, list) and len(field_value) > 0:
                            logger.info(
                                "preserving_tailored_instruction_field",
                                extra={
                                    "day": day_name,
                                    "field": field,
                                    "count": len(field_value),
                                },
                            )

                # Preserve objective content if it exists and is not just "No School"
                objective = day_data.get("objective", {})
                if isinstance(objective, dict):
                    for obj_field in [
                        "content_objective",
                        "student_goal",
                        "wida_objective",
                    ]:
                        obj_value = objective.get(obj_field, "")
                        if (
                            obj_value
                            and obj_value.strip()
                            and obj_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_objective_content",
                                extra={"day": day_name, "field": obj_field},
                            )

                # Preserve anticipatory_set content if it exists
                anticipatory_set = day_data.get("anticipatory_set", {})
                if isinstance(anticipatory_set, dict):
                    for as_field in ["original_content", "bilingual_bridge"]:
                        as_value = anticipatory_set.get(as_field, "")
                        if (
                            as_value
                            and as_value.strip()
                            and as_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_anticipatory_set_content",
                                extra={"day": day_name, "field": as_field},
                            )

            logger.info(
                "schema_validation_missing_days_filled",
                extra={"missing_days": missing_days, "filled_count": len(missing_days)},
            )

        # Check Monday structure (at minimum)
        monday = days["monday"]
        if "unit_lesson" not in monday:
            error_msg = "Missing monday.unit_lesson"
            logger.error("schema_validation_failed", extra={"reason": error_msg})
            return False, error_msg

        # Validate required fields for each day
        missing_fields = []
        for day_name in required_days:
            day_data = days.get(day_name, {})
            if not day_data or day_data.get("unit_lesson") == "No School":
                continue  # Skip "No School" days

            # Check for vocabulary_cognates
            vocab = day_data.get("vocabulary_cognates")
            if vocab is None:
                missing_fields.append(f"{day_name}.vocabulary_cognates (missing)")
            elif not isinstance(vocab, list):
                missing_fields.append(f"{day_name}.vocabulary_cognates (not a list)")
            elif len(vocab) == 0:
                missing_fields.append(
                    f"{day_name}.vocabulary_cognates (empty array - must have exactly 6 items)"
                )
            elif len(vocab) > 6:
                # Truncate to 6 items (LLM sometimes returns 7) - modify in place for downstream Pydantic
                day_data["vocabulary_cognates"] = vocab[:6]
            elif len(vocab) != 6:
                missing_fields.append(
                    f"{day_name}.vocabulary_cognates (has {len(vocab)} items, need exactly 6)"
                )

            # Check for sentence_frames
            frames = day_data.get("sentence_frames")
            if frames is None:
                missing_fields.append(f"{day_name}.sentence_frames (missing)")
            elif not isinstance(frames, list):
                missing_fields.append(f"{day_name}.sentence_frames (not a list)")
            elif len(frames) != 8:
                missing_fields.append(
                    f"{day_name}.sentence_frames (has {len(frames)} items, need exactly 8)"
                )

        if missing_fields:
            error_msg = f"Missing or invalid required fields: {', '.join(missing_fields)}. vocabulary_cognates (exactly 6 items) and sentence_frames (exactly 8 items) are MANDATORY for all lesson days."
            logger.error(
                "schema_validation_missing_fields",
                extra={"missing_fields": missing_fields},
            )
            return False, error_msg

        logger.info("schema_validation_success")
        return True, None

    def _normalize_sentence_frame_punctuation(
        self, lesson_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize sentence frame punctuation based on frame_type.
        - frame/stem: ends with "."
        - open_question: ends with "?"

        Acts as a safety net if LLM misses prompt instructions.
        """
        if not lesson_json or "days" not in lesson_json:
            return lesson_json

        days = lesson_json["days"]
        for day_name, day_data in days.items():
            if not isinstance(day_data, dict):
                continue

            frames = day_data.get("sentence_frames")
            if not isinstance(frames, list):
                continue

            for frame in frames:
                if not isinstance(frame, dict):
                    continue

                frame_type = frame.get("frame_type")

                # Normalize both English and Portuguese
                for lang in ["english", "portuguese"]:
                    text = frame.get(lang)
                    if not text or not isinstance(text, str):
                        continue

                    text = text.strip()
                    if not text:
                        continue

                    if frame_type in ["frame", "stem"]:
                        # Ensure ends with period
                        if not text.endswith("."):
                            # If it ends with other punctuation, maybe replace?
                            # User said "Has no period at the end of any sentence".
                            # Let's be safe: if it ends with ?, ; or : we leave it?
                            # No, frames should end with .
                            if text[-1] in ["?", "!", ":", ";"]:
                                text = text[:-1] + "."
                            else:
                                text = text + "."
                    elif frame_type == "open_question":
                        # Ensure ends with question mark
                        if not text.endswith("?"):
                            if text[-1] in [".", "!", ":", ";"]:
                                text = text[:-1] + "?"
                            else:
                                text = text + "?"

                    frame[lang] = text

        return lesson_json


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
