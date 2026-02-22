"""
Shared prompt text fragments for LLM prompts. Used by prompt_builder.
"""

JSON_SYNTAX_RULES = """
## CRITICAL: JSON SYNTAX RULES (MUST FOLLOW)

Before generating any JSON, you MUST follow these syntax rules:

1. **ALL property names MUST be in double quotes**
   - CORRECT: {"key": "value"}
   - INCORRECT: {key: "value"} or {'key': "value"}

2. **ALL string values MUST be in double quotes**
   - CORRECT: {"name": "John"}
   - INCORRECT: {"name": John} or {"name": 'John'}

3. **NO unquoted property names**
   - The error "Expecting property name enclosed in double quotes" means you used an unquoted key
   - Example: {key: value} is INVALID - must be {"key": value}

4. **Proper escaping of special characters**
   - Quotes inside strings: "He said \\"hello\\"" (CRITICAL: ALL quotes inside string values must be escaped)
   - Example: "wida_mapping": "Target \\"levels\\": 1-4" (NOT "Target "levels": 1-4")
   - The error "Expecting ',' delimiter" often means you have an unescaped quote inside a string
   - Newlines: "Line 1\\nLine 2"
   - Backslashes: "Path: C:\\\\Users"

5. **NO trailing commas**
   - CORRECT: {"a": 1, "b": 2}
   - INCORRECT: {"a": 1, "b": 2,}

6. **NO comments**
   - CORRECT: {"key": "value"}
   - INCORRECT: {"key": "value"} // comment

CRITICAL: Your JSON must be valid JSON syntax. Invalid JSON will cause parsing errors.
Remember: ALL keys must be quoted. {key: value} is INVALID.
"""
