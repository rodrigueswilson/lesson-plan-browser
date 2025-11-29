"""Debug funds_of_knowledge strategy specifically."""

import json
from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter

# Load the strategy
with open('d:/LP/strategies_pack_v2/specialized/cultural_identity.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fok_strategy = data['strategies'][1]  # Second strategy
print("Original funds_of_knowledge:")
print(f"  ID: {fok_strategy['id']}")
print(f"  skill_weights: {fok_strategy['skill_weights']}")
print(f"  Sum: {sum(fok_strategy['skill_weights'].values())}")

# Convert to MD
j2m = JsonToMarkdownConverter()
md_content = j2m.convert_strategy(fok_strategy)

print("\nMarkdown skill_weights line:")
for line in md_content.split('\n'):
    if 'Skill Weights' in line:
        print(f"  {line}")

# Convert back
m2j = MarkdownToJsonConverter()
reconstructed = m2j.parse_strategy(md_content)

print("\nReconstructed funds_of_knowledge:")
print(f"  ID: {reconstructed.get('id')}")
print(f"  skill_weights: {reconstructed.get('skill_weights')}")
print(f"  Sum: {sum(reconstructed.get('skill_weights', {}).values())}")

# Check if they match
if fok_strategy['skill_weights'] == reconstructed.get('skill_weights'):
    print("\nSUCCESS: Weights match!")
else:
    print("\nFAILURE: Weights don't match!")
    print(f"  Difference: {set(fok_strategy['skill_weights'].items()) ^ set(reconstructed.get('skill_weights', {}).items())}")
