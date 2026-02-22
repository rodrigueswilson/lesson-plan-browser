"""
Schema loading and OpenAI structured-output transformation.
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


def load_schema(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load JSON output schema from schemas/lesson_output_schema.json."""
    if base_path is not None:
        schema_path = base_path / "schemas" / "lesson_output_schema.json"
    else:
        schema_path = Path("schemas/lesson_output_schema.json")
    if not schema_path.exists():
        project_root = Path(__file__).resolve().parent.parent.parent
        schema_path = project_root / "schemas" / "lesson_output_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError("lesson_output_schema.json not found")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def add_additional_properties_false(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively add additionalProperties: false to all object schemas."""
    if not isinstance(schema, dict):
        return schema

    result = deepcopy(schema)

    if result.get("type") == "object":
        if "additionalProperties" not in result:
            result["additionalProperties"] = False

    if "properties" in result:
        for key, value in result["properties"].items():
            result["properties"][key] = add_additional_properties_false(value)

    if "definitions" in result:
        for key, value in result["definitions"].items():
            result["definitions"][key] = add_additional_properties_false(value)

    if "items" in result:
        if isinstance(result["items"], dict):
            result["items"] = add_additional_properties_false(result["items"])
        elif isinstance(result["items"], list):
            result["items"] = [
                add_additional_properties_false(item)
                if isinstance(item, dict)
                else item
                for item in result["items"]
            ]

    for keyword in ["oneOf", "anyOf", "allOf"]:
        if keyword in result:
            result[keyword] = [
                add_additional_properties_false(item)
                if isinstance(item, dict)
                else item
                for item in result[keyword]
            ]

    return result


def transform_oneof_for_openai(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Transform oneOf to anyOf for OpenAI structured outputs compatibility."""
    if not isinstance(schema, dict):
        return schema

    result = deepcopy(schema)

    if "oneOf" in result:
        result["anyOf"] = result.pop("oneOf")

    if "definitions" in result:
        for key, value in result["definitions"].items():
            result["definitions"][key] = transform_oneof_for_openai(value)

    if "properties" in result:
        for key, value in result["properties"].items():
            result["properties"][key] = transform_oneof_for_openai(value)

    if "items" in result:
        if isinstance(result["items"], dict):
            result["items"] = transform_oneof_for_openai(result["items"])
        elif isinstance(result["items"], list):
            result["items"] = [
                transform_oneof_for_openai(item)
                if isinstance(item, dict)
                else item
                for item in result["items"]
            ]

    for keyword in ["anyOf", "allOf"]:
        if keyword in result:
            result[keyword] = [
                transform_oneof_for_openai(item)
                if isinstance(item, dict)
                else item
                for item in result[keyword]
            ]

    return result


def build_openai_structured_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare schema for OpenAI structured outputs."""
    if not schema:
        return {"type": "object", "additionalProperties": False}

    schema_copy = deepcopy(schema)
    for key in ("$schema", "$id", "title", "description", "version"):
        schema_copy.pop(key, None)

    if not schema_copy.get("type"):
        schema_copy["type"] = "object"

    schema_copy = add_additional_properties_false(schema_copy)
    schema_copy = transform_oneof_for_openai(schema_copy)

    return schema_copy


def structured_response_format(
    openai_structured_schema: Dict[str, Any], model_name: str
) -> Optional[Dict[str, Any]]:
    """Return the response_format payload for OpenAI structured outputs."""
    if not openai_structured_schema:
        return None

    model_lower = (model_name or "").lower()
    use_strict = False if "gpt-5-mini" in model_lower else True

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "bilingual_lesson_plan",
            "schema": deepcopy(openai_structured_schema),
            "strict": use_strict,
        },
    }


def model_supports_structured_outputs(model_name: str) -> bool:
    """Check if the configured model supports structured outputs."""
    model_lower = (model_name or "").lower()
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
    return any(token in model_lower for token in supported_tokens)


def model_supports_json_mode(model_name: str) -> bool:
    """Check if the configured model supports OpenAI JSON mode."""
    model_lower = (model_name or "").lower()
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
    return any(token in model_lower for token in supported_tokens)
