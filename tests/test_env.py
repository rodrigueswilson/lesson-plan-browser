import os
from dotenv import load_dotenv

load_dotenv()

print("Environment variables check:")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'NOT SET')}")
print(f"GPT5_API_KEY: {'SET' if os.getenv('GPT5_API_KEY') else 'NOT SET'}")
print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
print(f"LLM_API_KEY: {'SET' if os.getenv('LLM_API_KEY') else 'NOT SET'}")
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'NOT SET')}")

# Test LLM service initialization
try:
    from backend.llm_service import get_llm_service
    llm = get_llm_service()
    print(f"\nLLM Service initialized successfully!")
    print(f"Provider: {llm.provider}")
    print(f"Model: {llm.model}")
    print(f"API Key: {'SET' if llm.api_key else 'NOT SET'}")
except Exception as e:
    print(f"\nLLM Service initialization FAILED: {e}")
