"""
Tests for model pricing module.
"""

import pytest

from backend.model_pricing import (
    calculate_cost,
    get_model_pricing,
    is_model_supported,
    list_supported_models,
)


def test_calculate_cost_gpt4_turbo():
    """Test cost calculation for GPT-4 Turbo."""
    cost = calculate_cost("gpt-4-turbo-preview", 1000, 500)
    # (1000 / 1000 * 0.01) + (500 / 1000 * 0.03) = 0.01 + 0.015 = 0.025
    expected = 0.025
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_gpt4():
    """Test cost calculation for GPT-4."""
    cost = calculate_cost("gpt-4", 2000, 1000)
    # (2000 / 1000 * 0.03) + (1000 / 1000 * 0.06) = 0.06 + 0.06 = 0.12
    expected = 0.12
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_gpt35_turbo():
    """Test cost calculation for GPT-3.5 Turbo."""
    cost = calculate_cost("gpt-3.5-turbo", 5000, 2000)
    # (5000 / 1000 * 0.0005) + (2000 / 1000 * 0.0015) = 0.0025 + 0.003 = 0.0055
    expected = 0.0055
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_claude_opus():
    """Test cost calculation for Claude 3 Opus."""
    cost = calculate_cost("claude-3-opus-20240229", 2000, 1000)
    # (2000 / 1000 * 0.015) + (1000 / 1000 * 0.075) = 0.03 + 0.075 = 0.105
    expected = 0.105
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_claude_sonnet():
    """Test cost calculation for Claude 3 Sonnet."""
    cost = calculate_cost("claude-3-sonnet-20240229", 3000, 1500)
    # (3000 / 1000 * 0.003) + (1500 / 1000 * 0.015) = 0.009 + 0.0225 = 0.0315
    expected = 0.0315
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_claude_haiku():
    """Test cost calculation for Claude 3 Haiku."""
    cost = calculate_cost("claude-3-haiku-20240307", 10000, 5000)
    # (10000 / 1000 * 0.00025) + (5000 / 1000 * 0.00125) = 0.0025 + 0.00625 = 0.00875
    expected = 0.00875
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_zero_tokens():
    """Test cost calculation with zero tokens."""
    cost = calculate_cost("gpt-4-turbo-preview", 0, 0)
    assert cost == 0.0


def test_calculate_cost_unknown_model():
    """Test handling of unknown model."""
    cost = calculate_cost("unknown-model-xyz", 1000, 500)
    assert cost == 0.0


def test_calculate_cost_custom_pricing():
    """Test cost calculation with custom pricing."""
    custom = {"test-model": {"input": 0.1, "output": 0.2}}
    cost = calculate_cost("test-model", 1000, 500, custom_pricing=custom)
    # (1000 / 1000 * 0.1) + (500 / 1000 * 0.2) = 0.1 + 0.1 = 0.2
    expected = 0.2
    assert abs(cost - expected) < 0.0001


def test_get_model_pricing_gpt4():
    """Test retrieving pricing for GPT-4 Turbo."""
    pricing = get_model_pricing("gpt-4-turbo-preview")
    assert pricing == {"input": 0.01, "output": 0.03}


def test_get_model_pricing_claude():
    """Test retrieving pricing for Claude."""
    pricing = get_model_pricing("claude-3-opus-20240229")
    assert pricing == {"input": 0.015, "output": 0.075}


def test_get_model_pricing_unknown():
    """Test retrieving pricing for unknown model."""
    pricing = get_model_pricing("unknown-model")
    assert pricing is None


def test_list_supported_models():
    """Test listing all supported models."""
    models = list_supported_models()
    assert isinstance(models, list)
    assert len(models) > 0
    assert "gpt-4-turbo-preview" in models
    assert "claude-3-opus-20240229" in models
    assert "gpt-3.5-turbo" in models


def test_is_model_supported_true():
    """Test checking if model is supported (positive case)."""
    assert is_model_supported("gpt-4-turbo-preview") is True
    assert is_model_supported("claude-3-opus-20240229") is True


def test_is_model_supported_false():
    """Test checking if model is supported (negative case)."""
    assert is_model_supported("unknown-model") is False
    assert is_model_supported("") is False


def test_cost_precision():
    """Test that costs are rounded to 6 decimal places."""
    cost = calculate_cost("gpt-4-turbo-preview", 1, 1)
    # Should have at most 6 decimal places
    cost_str = f"{cost:.10f}"
    decimal_part = cost_str.split(".")[1]
    # Check that there are no significant digits beyond 6 places
    assert len(decimal_part.rstrip("0")) <= 6


def test_large_token_counts():
    """Test cost calculation with large token counts."""
    cost = calculate_cost("gpt-4-turbo-preview", 100000, 50000)
    # (100000 / 1000 * 0.01) + (50000 / 1000 * 0.03) = 1.0 + 1.5 = 2.5
    expected = 2.5
    assert abs(cost - expected) < 0.0001
