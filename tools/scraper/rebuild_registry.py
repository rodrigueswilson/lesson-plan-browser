import os
import json
import yaml
import sys
from collections import defaultdict

# Add current path to sys.path so we can import organizer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from tools.scraper.organizer import guess_grade_and_subject, parse_unit_name

def rebuild_registry(search_dirs, output_file):
    print(f"Rebuilding registry from {search_dirs}...")
    
    # Nested dictionary with automatic factory
    def nested_dict():
        return defaultdict(nested_dict)
    
    registry = nested_dict()
    found_count = 0

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        for root, _, files in os.walk(s_dir):
            if 'index.md' in files:
                index_path = os.path.join(root, 'index.md')
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if '---' in content:
                        parts = content.split('---')
                        if len(parts) >= 3:
                            metadata = yaml.safe_load(parts[1])
                            doc_id = metadata.get('id')
                            title = metadata.get('title', os.path.basename(root))
                            
                            if doc_id:
                                # Determine hierarchy
                                grade, subject = guess_grade_and_subject(title, root)
                                unit_name = parse_unit_name(title, os.path.basename(root))
                                
                                # Fallback cleanup for unit name
                                if unit_name == os.path.basename(root) and not title.lower().startswith("unit"):
                                    safe_title = "".join([c if c.isalnum() or c in " _-" else "" for c in title]).strip()
                                    unit_name = safe_title.replace(" ", "_").strip("_")
                                    
                                registry[grade][subject][unit_name][doc_id] = title
                                found_count += 1
                except Exception as e:
                    print(f"Error parsing {index_path}: {e}")

    # Convert defaultdicts to regular dicts for JSON serialization
    def to_dict(d):
        if isinstance(d, defaultdict):
            d = {k: to_dict(v) for k, v in d.items()}
        return d
    
    final_dict = to_dict(registry)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, indent=2)
        
    print(f"Successfully wrote {found_count} unique IDs to {output_file}.")

if __name__ == "__main__":
    search = ["reference_docs/scraped", "reference_docs/curriculum"]
    out = "reference_docs/scraped_registry.json"
    rebuild_registry(search, out)
