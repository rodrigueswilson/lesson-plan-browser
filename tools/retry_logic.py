"""
LLM Retry Logic with Validation Feedback
Handles retries when JSON validation fails, providing specific error feedback to the LLM.
"""

import json
import time
from typing import Callable, Optional, Dict, List, Tuple
from pathlib import Path

from .json_repair import validate_and_repair


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def format_validation_errors_for_llm(errors: List[str]) -> str:
    """
    Format validation errors in a way that's helpful for LLM correction.
    
    Args:
        errors: List of validation error messages
        
    Returns:
        Formatted error message for LLM
    """
    formatted = []
    
    for error in errors:
        # Extract key information and make it actionable
        if "is a required property" in error:
            # Extract field name
            if "'" in error:
                field = error.split("'")[1]
                formatted.append(f"❌ Missing required field: '{field}' - Please add this field with appropriate content")
        elif "is not of type" in error:
            formatted.append(f"❌ Wrong data type: {error} - Check the schema for the correct type")
        elif "is not one of" in error:
            formatted.append(f"❌ Invalid enum value: {error} - Use one of the allowed values from the schema")
        elif "is too short" in error:
            formatted.append(f"❌ String too short: {error} - Provide more detailed content")
        elif "is too long" in error:
            formatted.append(f"❌ String too long: {error} - Shorten the content to meet the limit")
        elif "does not match" in error:
            formatted.append(f"❌ Pattern mismatch: {error} - Ensure the format matches the required pattern")
        else:
            formatted.append(f"❌ {error}")
    
    return "\n".join(formatted)


def create_retry_prompt(original_prompt: str, json_response: str, validation_errors: List[str], attempt: int) -> str:
    """
    Create a retry prompt with specific error feedback.
    
    Args:
        original_prompt: Original prompt sent to LLM
        json_response: The invalid JSON response
        validation_errors: List of validation errors
        attempt: Current attempt number
        
    Returns:
        New prompt with error feedback
    """
    error_summary = format_validation_errors_for_llm(validation_errors)
    
    retry_prompt = f"""
Your previous JSON response had validation errors. Please correct them and regenerate.

**Attempt:** {attempt}

**Validation Errors:**
{error_summary}

**What to fix:**
1. Review each error above carefully
2. Correct the specific issues mentioned
3. Ensure all required fields are present
4. Verify data types match the schema
5. Check string lengths meet minimum/maximum requirements
6. Ensure enum values are exactly as specified in the schema

**Important:**
- Output ONLY valid JSON (no markdown code blocks, no explanations)
- Use double quotes for all strings
- No trailing commas
- No comments in JSON

**Original Request:**
{original_prompt}

Please regenerate the complete JSON response with all errors corrected.
"""
    
    return retry_prompt


def generate_with_retry(
    llm_generate: Callable[[str], str],
    initial_prompt: str,
    validator: Callable[[Dict], Tuple[bool, List[str]]],
    max_retries: int = 3,
    enable_repair: bool = True,
    telemetry_callback: Optional[Callable] = None
) -> Optional[Dict]:
    """
    Generate lesson plan with automatic retry on validation errors.
    
    Args:
        llm_generate: Function that takes prompt and returns LLM response
        initial_prompt: Initial prompt to send to LLM
        validator: Function that validates JSON and returns (is_valid, errors)
        max_retries: Maximum number of retry attempts
        enable_repair: Whether to attempt JSON repair before retrying
        telemetry_callback: Optional callback for logging attempts
        
    Returns:
        Validated lesson plan data or None if all retries failed
        
    Raises:
        RetryExhausted: If all retry attempts fail
    """
    prompt = initial_prompt
    last_response = None
    last_errors = []
    
    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        
        # Generate response
        try:
            response = llm_generate(prompt)
            last_response = response
        except Exception as e:
            if telemetry_callback:
                telemetry_callback(
                    attempt=attempt,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=f"LLM generation failed: {str(e)}"
                )
            
            if attempt == max_retries:
                raise RetryExhausted(f"LLM generation failed after {max_retries} attempts: {str(e)}")
            
            # Wait before retry
            time.sleep(1)
            continue
        
        # Try to parse and repair JSON
        if enable_repair:
            success, data, repair_message = validate_and_repair(response)
            
            if telemetry_callback and repair_message and "Repaired" in repair_message:
                telemetry_callback(
                    attempt=attempt,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    repair_attempted=True,
                    repair_message=repair_message
                )
        else:
            # Try direct parsing
            try:
                data = json.loads(response)
                success = True
            except json.JSONDecodeError as e:
                success = False
                data = None
                last_errors = [f"JSON parsing error: {str(e)}"]
        
        if not success or data is None:
            # JSON parsing/repair failed
            if attempt == max_retries:
                raise RetryExhausted(
                    f"Failed to parse valid JSON after {max_retries} attempts. "
                    f"Last errors: {last_errors}"
                )
            
            # Create retry prompt with parsing error
            prompt = f"""
Your previous response was not valid JSON.

**Error:** {last_errors[0] if last_errors else 'Could not parse JSON'}

**Requirements:**
1. Output ONLY valid JSON (no text before or after)
2. Do NOT wrap in markdown code blocks (no ```json```)
3. Use double quotes for all strings
4. No trailing commas
5. Proper escaping of special characters

**Original Request:**
{initial_prompt}

Please regenerate the complete JSON response with valid syntax.
"""
            
            if telemetry_callback:
                telemetry_callback(
                    attempt=attempt,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error="JSON parsing failed"
                )
            
            continue
        
        # Validate against schema
        valid, errors = validator(data)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if valid:
            # Success!
            if telemetry_callback:
                telemetry_callback(
                    attempt=attempt,
                    success=True,
                    duration_ms=duration_ms,
                    retry_count=attempt - 1
                )
            
            return data
        
        # Validation failed
        last_errors = errors
        
        if telemetry_callback:
            telemetry_callback(
                attempt=attempt,
                success=False,
                duration_ms=duration_ms,
                validation_errors=errors
            )
        
        if attempt == max_retries:
            raise RetryExhausted(
                f"Validation failed after {max_retries} attempts. "
                f"Last errors: {errors}"
            )
        
        # Create retry prompt with validation errors
        prompt = create_retry_prompt(initial_prompt, response, errors, attempt + 1)
    
    # Should not reach here
    raise RetryExhausted(f"Unexpected: Exhausted {max_retries} retries")


def generate_with_retry_simple(
    llm_generate: Callable[[str], str],
    initial_prompt: str,
    validator: Callable[[Dict], Tuple[bool, List[str]]],
    max_retries: int = 3
) -> Dict:
    """
    Simplified version without telemetry callback.
    
    Args:
        llm_generate: Function that takes prompt and returns LLM response
        initial_prompt: Initial prompt to send to LLM
        validator: Function that validates JSON and returns (is_valid, errors)
        max_retries: Maximum number of retry attempts
        
    Returns:
        Validated lesson plan data
        
    Raises:
        RetryExhausted: If all retry attempts fail
    """
    return generate_with_retry(
        llm_generate=llm_generate,
        initial_prompt=initial_prompt,
        validator=validator,
        max_retries=max_retries,
        enable_repair=True,
        telemetry_callback=None
    )
