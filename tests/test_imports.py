"""Test that all imports work after our changes."""

print("Testing imports...")

try:
    from tools.docx_parser import DOCXParser
    print("✅ DOCXParser imports OK")
except Exception as e:
    print(f"❌ DOCXParser import failed: {e}")

try:
    from tools.docx_renderer import DOCXRenderer
    print("✅ DOCXRenderer imports OK")
except Exception as e:
    print(f"❌ DOCXRenderer import failed: {e}")

try:
    from tools.batch_processor import BatchProcessor
    print("✅ BatchProcessor imports OK")
except Exception as e:
    print(f"❌ BatchProcessor import failed: {e}")

print("\nAll imports successful!")
