"""
Resolve LLM API key for a given provider (environment + optional api_key.txt).
"""

import os
from typing import Optional

from backend.telemetry import logger


def get_llm_api_key(provider: str) -> Optional[str]:
    """Get API key from environment or api_key.txt for the given provider.

    Args:
        provider: "openai" or "anthropic"

    Returns:
        API key if found, None otherwise. Logs warnings/errors as in original behavior.
    """
    key: Optional[str] = None

    if provider == "openai":
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
    elif provider == "anthropic":
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
                "provider": provider,
                "message": f"Unknown LLM provider: {provider}",
            },
        )
        return None

    if not key:
        try:
            with open("api_key.txt", "r") as f:
                key = f.read().strip()
            if key:
                info_msg = f"OK LLM Service: API key loaded from api_key.txt file for {provider}"
                print(info_msg)
                logger.info(
                    "api_key_found_in_file",
                    extra={
                        "provider": provider,
                        "source": "api_key.txt",
                        "message": "API key loaded from api_key.txt file",
                    },
                )
        except (FileNotFoundError, IOError):
            logger.debug(
                "api_key_file_not_found",
                extra={
                    "provider": provider,
                    "file": "api_key.txt",
                    "message": "api_key.txt file not found, checking environment only",
                },
            )

    if not key:
        error_msg = f"✗ LLM Service: No API key found for {provider}. Checked environment variables and api_key.txt file. Service will fail to initialize."
        print(error_msg)
        logger.error(
            "api_key_not_found_anywhere",
            extra={
                "provider": provider,
                "checked_env_vars": [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "LLM_API_KEY",
                ]
                if provider == "openai"
                else ["ANTHROPIC_API_KEY", "LLM_API_KEY"],
                "checked_file": "api_key.txt",
                "message": f"No API key found for {provider} in environment variables or api_key.txt file",
            },
        )

    return key
