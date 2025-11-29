
from pydantic import BaseModel, PrivateAttr
from sqlmodel import SQLModel, Field

class MyModel(SQLModel):
    id: int
    name: str
    _private: str = PrivateAttr(default="secret")

def _sanitize_value(value):
    """Recursively sanitize a value to remove ModelPrivateAttr objects."""
    # Check for ModelPrivateAttr
    if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
        print(f"SANITIZED: {type(value)}")
        return None
        
    # Handle lists
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
        
    # Handle dicts
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
        
    return value

try:
    # Test sanitizer with the descriptor
    descriptor = MyModel._private
    print(f"Testing sanitizer with descriptor: {type(descriptor)}")
    
    cleaned = _sanitize_value(descriptor)
    print(f"Sanitized descriptor: {cleaned}")
    
    # Test sanitizer with a dict containing descriptor
    data = {"safe": 1, "unsafe": descriptor}
    cleaned_data = _sanitize_value(data)
    print(f"Sanitized data: {cleaned_data}")

except Exception as e:
    print(f"Error in test: {e}")
