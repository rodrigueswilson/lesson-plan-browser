import json
import os
import re

def analyze_curriculum(registry_path, output_json_path):
    if not os.path.exists(registry_path):
        print(f"Error: Registry file not found at {registry_path}")
        return

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    report = {}
    gaps_found = False

    print("\n--- Curriculum Gap Analysis Report ---\n")

    for grade, subjects in registry.items():
        if grade == "scraped_ids": continue
        
        for subject, units in subjects.items():
            unit_numbers = []
            for unit_key in units.keys():
                # Extract numeric unit number using regex
                match = re.search(r'Unit\s*(\d+)', unit_key, re.I)
                if match:
                    unit_numbers.append(int(match.group(1)))
            
            if not unit_numbers:
                continue
                
            unit_numbers.sort()
            max_unit = max(unit_numbers)
            all_units = set(range(1, max_unit + 1))
            missing_units = sorted(list(all_units - set(unit_numbers)))
            
            if missing_units:
                gaps_found = True
                if grade not in report: report[grade] = {}
                report[grade][subject] = missing_units
                
                missing_str = ", ".join([f"Unit {u}" for u in missing_units])
                print(f"MISSING in [{grade} - {subject}]: {missing_str}")
            else:
                print(f"COMPLETE sequence in [{grade} - {subject}] (Units 1 to {max_unit})")

    if not gaps_found:
        print("\nNo gaps detected in the sequential unit numbering.")
    
    # Save to JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nGap report saved to: {output_json_path}")

if __name__ == "__main__":
    reg = "reference_docs/scraped_registry.json"
    out = "reference_docs/curriculum_gaps.json"
    analyze_curriculum(reg, out)
