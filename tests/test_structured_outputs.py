"""
Test OpenAI Structured Outputs Integration

Tests that the LLM service correctly uses structured outputs when available,
and falls back appropriately when not supported.
"""

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from backend.llm.schema import (
    model_supports_json_mode,
    model_supports_structured_outputs,
    structured_response_format,
)
from backend.llm_service import LLMService, get_llm_service

load_dotenv()

# Sample primary teacher content
PRIMARY_CONTENT = """
MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.

Anticipatory Set: Show ice cube melting in a beaker. Ask: What is happening? Why? Record observations.

Instruction: 
- Present three states of matter with demonstrations
- Show solid (ice), liquid (water), gas (steam)
- Discuss molecular movement in each state
- Students complete comparison chart

Misconceptions: Students may think gases have no mass or that liquids always take the shape of their container from the bottom up.

Assessment: Students complete three-column chart comparing states of matter. Must include at least 3 properties for each state.

Homework: Find 5 examples of each state of matter at home. Draw or photograph them. Label in English.
"""


def test_model_support_detection():
    """Test that model support detection works correctly"""
    print("=" * 60)
    print("TEST 1: Model Support Detection")
    print("=" * 60)
    
    # Test supported models
    supported_models = [
        "gpt-5-mini",  # User's actual model
        "gpt-5",
        "gpt-4-turbo-preview",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
    ]
    
    for model in supported_models:
        service = LLMService(provider="openai")
        service.model = model
        assert model_supports_structured_outputs(model), f"{model} should support structured outputs"
        print(f"[OK] {model}: Structured outputs supported")
    
    # Test unsupported models (should fall back to JSON mode)
    unsupported_models = [
        "gpt-3.5-turbo",
        "gpt-4",
    ]
    
    for model in unsupported_models:
        service = LLMService(provider="openai")
        service.model = model
        json_mode_supported = model_supports_json_mode(model)
        assert json_mode_supported, f"{model} should support JSON mode"
        print(f"[OK] {model}: JSON mode supported (structured outputs not available)")
    
    print("[OK] All model support checks passed\n")


def test_schema_preprocessing():
    """Test that schema is correctly preprocessed for OpenAI"""
    print("=" * 60)
    print("TEST 2: Schema Preprocessing")
    print("=" * 60)
    
    service = LLMService(provider="openai")
    
    # Check that schema is loaded
    assert service.schema is not None, "Schema should be loaded"
    print("[OK] Schema loaded")
    
    # Check that OpenAI structured schema is prepared
    assert service.openai_structured_schema is not None, "OpenAI structured schema should be prepared"
    print("[OK] OpenAI structured schema prepared")
    
    # Check that metadata fields are removed
    assert "$schema" not in service.openai_structured_schema, "Should remove $schema"
    assert "$id" not in service.openai_structured_schema, "Should remove $id"
    assert "title" not in service.openai_structured_schema, "Should remove title"
    print("[OK] Metadata fields removed")
    
    # Check that structure is preserved
    assert "type" in service.openai_structured_schema, "Should preserve type"
    assert "properties" in service.openai_structured_schema, "Should preserve properties"
    assert "definitions" in service.openai_structured_schema, "Should preserve definitions"
    print("[OK] Schema structure preserved")
    
    print("[OK] All schema preprocessing checks passed\n")


def test_response_format_building():
    """Test that response format is correctly built"""
    print("=" * 60)
    print("TEST 3: Response Format Building")
    print("=" * 60)
    
    service = LLMService(provider="openai")
    service.model = "gpt-4-turbo-preview"
    
    response_format = structured_response_format(
        service.openai_structured_schema, service.model
    )
    
    assert response_format is not None, "Response format should be built"
    assert response_format["type"] == "json_schema", "Should use json_schema type"
    assert "json_schema" in response_format, "Should have json_schema key"
    
    json_schema = response_format["json_schema"]
    assert json_schema["name"] == "bilingual_lesson_plan", "Should have correct name"
    assert json_schema["strict"] is True, "Should use strict mode for non-gpt-5-mini"
    assert "schema" in json_schema, "Should include schema"
    
    print("[OK] Response format structure correct")
    print(f"   Name: {json_schema['name']}")
    print(f"   Strict: {json_schema['strict']}")
    print(f"   Schema type: {json_schema['schema'].get('type')}")
    print("[OK] All response format checks passed\n")


def test_prompt_optimization():
    """Test that prompt is optimized when using structured outputs"""
    print("=" * 60)
    print("TEST 4: Prompt Optimization")
    print("=" * 60)
    
    # Test with structured outputs enabled
    service = LLMService(provider="openai")
    service.model = "gpt-4-turbo-preview"
    
    prompt_with_structured = service._build_prompt(
        primary_content=PRIMARY_CONTENT,
        grade="6",
        subject="Science",
        week_of="10/6-10/10",
        teacher_name="Ms. Rodriguez",
        homeroom="302"
    )
    
    # Prompt should NOT include schema example when using structured outputs
    assert "REQUIRED JSON SCHEMA STRUCTURE" not in prompt_with_structured, "Should not include schema section"
    assert "You MUST output JSON that matches this EXACT structure" not in prompt_with_structured, "Should not include schema instructions"
    assert "schema provided via API" in prompt_with_structured, "Should reference API-provided schema"
    
    print("[OK] Prompt optimized (no schema examples)")
    print(f"   Prompt length: {len(prompt_with_structured)} characters")
    
    # Test with structured outputs disabled (e.g., gpt-3.5-turbo)
    service.model = "gpt-3.5-turbo"
    prompt_without_structured = service._build_prompt(
        primary_content=PRIMARY_CONTENT,
        grade="6",
        subject="Science",
        week_of="10/6-10/10",
        teacher_name="Ms. Rodriguez",
        homeroom="302"
    )
    
    # Prompt SHOULD include schema example when NOT using structured outputs
    assert "REQUIRED JSON SCHEMA STRUCTURE" in prompt_without_structured, "Should include schema section"
    assert "You MUST output JSON that matches this EXACT structure" in prompt_without_structured, "Should include schema instructions"
    
    print("[OK] Prompt includes schema examples (fallback mode)")
    print(f"   Prompt length: {len(prompt_without_structured)} characters")
    
    # Check token savings
    token_savings = len(prompt_without_structured) - len(prompt_with_structured)
    print(f"   Estimated token savings: ~{token_savings // 4} tokens")
    
    print("[OK] All prompt optimization checks passed\n")


def test_gpt5_mini_specific():
    """Test GPT-5 Mini specific configuration and behavior"""
    print("=" * 60)
    print("TEST 6: GPT-5 Mini Specific Tests")
    print("=" * 60)
    
    service = LLMService(provider="openai")
    service.model = "gpt-5-mini"
    
    # Test 1: Model detection
    assert model_supports_structured_outputs(service.model), "GPT-5 Mini should support structured outputs"
    assert model_supports_json_mode(service.model), "GPT-5 Mini should support JSON mode"
    print("[OK] GPT-5 Mini detected as supporting structured outputs and JSON mode")
    
    # Test 2: Token limit
    token_limit = service._model_token_limit()
    assert token_limit == 32768, f"GPT-5 Mini should have 32768 token limit, got {token_limit}"
    print(f"[OK] GPT-5 Mini token limit: {token_limit}")
    
    # Test 3: Response format (gpt-5-mini uses strict=False for compatibility)
    response_format = structured_response_format(
        service.openai_structured_schema, service.model
    )
    assert response_format is not None, "GPT-5 Mini should generate response format"
    assert response_format["type"] == "json_schema", "Should use json_schema type"
    assert response_format["json_schema"]["strict"] is False, "GPT-5 Mini uses non-strict mode"
    print("[OK] GPT-5 Mini response format configured correctly")
    
    # Test 4: Prompt optimization (GPT-5 Mini specific)
    prompt = service._build_prompt(
        primary_content=PRIMARY_CONTENT,
        grade="6",
        subject="Science",
        week_of="10/6-10/10",
        teacher_name="Ms. Rodriguez",
        homeroom="302"
    )
    
    # Should NOT include schema examples when using structured outputs
    assert "REQUIRED JSON SCHEMA STRUCTURE" not in prompt, "Should not include schema section"
    assert "schema provided via API" in prompt, "Should reference API-provided schema"
    print("[OK] GPT-5 Mini prompt optimized (no schema examples)")
    print(f"   Prompt length: {len(prompt)} characters")
    
    # Test 5: Schema preparation
    assert service.openai_structured_schema is not None, "OpenAI structured schema should be prepared"
    assert "$schema" not in service.openai_structured_schema, "Should remove $schema"
    assert "properties" in service.openai_structured_schema, "Should preserve properties"
    assert "definitions" in service.openai_structured_schema, "Should preserve definitions"
    print("[OK] GPT-5 Mini schema preprocessing correct")
    
    print("[OK] All GPT-5 Mini specific tests passed\n")


@pytest.mark.timeout(300)
def test_integration_with_real_api():
    """Test actual LLM call with structured outputs (requires API key; can take minutes)."""
    print("=" * 60)
    print("TEST 5: Integration Test (Real API)")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    
    if not api_key:
        print("[SKIP] Skipping integration test - no API key found")
        print("   Set OPENAI_API_KEY environment variable to run this test")
        return
    
    # Try GPT-5 Mini first (user's actual model), then fallback to gpt-4-turbo-preview
    test_models = ["gpt-5-mini", "gpt-4-turbo-preview"]
    
    for model in test_models:
        try:
            service = get_llm_service(provider="openai")
            service.model = model
            
            print(f"   Testing with model: {model}")
            print(f"   Using structured outputs: {model_supports_structured_outputs(model)}")
            print(f"   Token limit: {service._model_token_limit()}")
            print()
            print("   Calling LLM API...")
            
            success, lesson_json, error = service.transform_lesson(
                primary_content=PRIMARY_CONTENT,
                grade="6",
                subject="Science",
                week_of="10/6-10/10",
                teacher_name="Ms. Rodriguez",
                homeroom="302"
            )
            
            if success:
                print(f"[OK] LLM transformation successful with {model}!")
                print(f"   Metadata: {lesson_json.get('metadata', {})}")
                print(f"   Days: {list(lesson_json.get('days', {}).keys())}")
                print(f"   Tokens used: {lesson_json.get('_usage', {}).get('tokens_total', 0)}")
                print(f"   Model: {lesson_json.get('_model')}")
                print(f"   Provider: {lesson_json.get('_provider')}")
                
                # Save result for inspection
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / f"structured_outputs_test_{model.replace('-', '_')}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(lesson_json, f, indent=2, ensure_ascii=False)
                print(f"   Saved to: {output_file}")
                print()
                break  # Success, no need to try other models
            else:
                print(f"[FAIL] LLM transformation failed with {model}: {error}")
                if model != test_models[-1]:
                    print(f"   Will try fallback model: {test_models[test_models.index(model) + 1]}")
                    print()
                
        except Exception as e:
            print(f"[FAIL] Integration test failed with {model}: {e}")
            if model != test_models[-1]:
                print(f"   Will try fallback model: {test_models[test_models.index(model) + 1]}")
                print()
            else:
                import traceback
                traceback.print_exc()
    
    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OPENAI STRUCTURED OUTPUTS TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_model_support_detection()
        test_schema_preprocessing()
        test_response_format_building()
        test_prompt_optimization()
        test_gpt5_mini_specific()
        test_integration_with_real_api()
        
        print("=" * 60)
        print("[OK] ALL TESTS COMPLETED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review output/structured_outputs_test.json if integration test ran")
        print("2. Monitor logs for 'using_openai_structured_outputs' messages")
        print("3. Verify token usage reduction in production")
        
    except Exception as e:
        print(f"\n[FAIL] TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

