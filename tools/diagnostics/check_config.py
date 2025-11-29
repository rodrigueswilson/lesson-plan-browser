"""Check configuration."""

from backend.config import settings

print("Configuration Check:")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")
print(f"LLM_MODEL: {settings.LLM_MODEL}")
print(f"DOCX_TEMPLATE_PATH: {settings.DOCX_TEMPLATE_PATH}")
print(f"OUTPUT_DIR: {settings.OUTPUT_DIR}")
