"""Check which strategies have invalid skill_weights."""

import json
from pathlib import Path

files = list(Path('d:/LP/strategies_pack_v2').rglob('*.json'))

print("Strategies with skill_weights not summing to 1.0:")
print("=" * 70)

for f in files:
    if f.name == '_index.json':
        continue
    
    data = json.load(open(f, encoding='utf-8'))
    
    for s in data.get('strategies', []):
        weights = s.get('skill_weights', {})
        total = sum(weights.values())
        
        if abs(total - 1.0) > 0.01 and abs(total) > 0.01:
            print(f"{f.name}: {s['id']}")
            print(f"  Sum: {total:.2f}")
            print(f"  Weights: {weights}")
            print()
