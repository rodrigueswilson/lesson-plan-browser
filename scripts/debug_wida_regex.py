
import re

def test_regex():
    bad_json = '{"days": {"monday": {"assessment": {"bilingual_overlay": {"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"}}}}}'
    
    # Refined regex: Look for wida_mapping followed by anything until a quote followed by } or ,
    # Or until the next field "property":
    pattern = r'("wida_mapping"\s*:\s*")(.+?)(")(?=\s*[,}])'
    
    matches = list(re.finditer(pattern, bad_json, re.IGNORECASE))
    print(f"Found {len(matches)} matches")
    
    fixed_string = bad_json
    for match in reversed(matches):
        prefix, content, suffix = match.groups()
        print(f"Prefix: {prefix}")
        print(f"Content: {content}")
        print(f"Suffix: {suffix}")
        
        escaped_content = re.sub(r'(?<!\\)"', r'\\"', content)
        print(f"Escaped Content: {escaped_content}")
        
        fixed_match = prefix + escaped_content + suffix
        fixed_string = fixed_string[:match.start()] + fixed_match + fixed_string[match.end():]
        
    print(f"Fixed String: {fixed_string}")
    
    try:
        import json
        json.loads(fixed_string)
        print("Success: Valid JSON!")
    except Exception as e:
        print(f"Failure: {e}")

if __name__ == "__main__":
    test_regex()
