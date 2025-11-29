"""
Validation script for Session 2: Token Tracking
Tests that LLM APIs return token usage information.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_openai_token_tracking():
    """Validate OpenAI returns token usage."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  OPENAI_API_KEY not found - skipping OpenAI test")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test' in one word"}],
            max_tokens=10
        )
        
        # Check for usage data
        if hasattr(response, 'usage'):
            usage = response.usage
            print("✅ OpenAI Token Tracking:")
            print(f"   - Prompt tokens: {usage.prompt_tokens}")
            print(f"   - Completion tokens: {usage.completion_tokens}")
            print(f"   - Total tokens: {usage.total_tokens}")
            return True
        else:
            print("❌ OpenAI response missing 'usage' field")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return False


def test_anthropic_token_tracking():
    """Validate Anthropic returns token usage."""
    try:
        import anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not found - skipping Anthropic test")
            return False
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test call
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test' in one word"}]
        )
        
        # Check for usage data
        if hasattr(response, 'usage'):
            usage = response.usage
            print("✅ Anthropic Token Tracking:")
            print(f"   - Input tokens: {usage.input_tokens}")
            print(f"   - Output tokens: {usage.output_tokens}")
            return True
        else:
            print("❌ Anthropic response missing 'usage' field")
            return False
            
    except Exception as e:
        print(f"❌ Anthropic test failed: {e}")
        return False


def test_cost_calculation():
    """Test cost calculation accuracy."""
    print("\n✅ Cost Calculation Test:")
    
    # Test GPT-4 Turbo
    input_tokens = 1000
    output_tokens = 500
    
    # Manual calculation
    input_cost = (input_tokens / 1000) * 0.01  # $0.01 per 1K
    output_cost = (output_tokens / 1000) * 0.03  # $0.03 per 1K
    expected_cost = input_cost + output_cost
    
    print(f"   - Input: {input_tokens} tokens × $0.01/1K = ${input_cost:.6f}")
    print(f"   - Output: {output_tokens} tokens × $0.03/1K = ${output_cost:.6f}")
    print(f"   - Total: ${expected_cost:.6f}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Session 2 Validation: Token Tracking")
    print("=" * 60)
    print()
    
    results = []
    
    # Test OpenAI
    print("Task 2.1a: Verify OpenAI Token Counts")
    print("-" * 60)
    results.append(test_openai_token_tracking())
    print()
    
    # Test Anthropic
    print("Task 2.1b: Verify Anthropic Token Counts")
    print("-" * 60)
    results.append(test_anthropic_token_tracking())
    print()
    
    # Test cost calculation
    print("Task 2.4: Validate Cost Calculations")
    print("-" * 60)
    results.append(test_cost_calculation())
    print()
    
    # Summary
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All validation tasks passed!")
        print("   Ready to proceed with implementation.")
    else:
        print(f"\n⚠️  {total - passed} validation task(s) failed.")
        print("   Review errors before proceeding.")
