import os
import shutil
import yaml
import re
import argparse

def guess_grade_and_subject(title, parent_path):
    title_lower = title.lower()
    path_lower = parent_path.lower()
    
    grade = "Uncategorized_Grade"
    subject = "Uncategorized_Subject"
    
    # 1. Subject Guesses
    if "ela " in path_lower or "story " in title_lower or "reading" in path_lower or "literature" in title_lower:
        subject = "ELA"
    elif "math" in path_lower or "geometry" in title_lower or "addition" in title_lower or "subtracting" in title_lower or "fractions" in title_lower or "perimeter" in title_lower or "length" in title_lower or "numbers" in title_lower or "multiplication" in title_lower or "division" in title_lower:
        subject = "Math"
        
    # 2. Grade Guesses checks parent path closely
    if "second_grade" in path_lower or "grade 2" in path_lower or "grade_2" in path_lower:
        grade = "Grade 2"
        # Usually ELA is tagged with this specific path signature
        if "ela" not in path_lower and "math" not in path_lower and "geometry" not in path_lower:
            subject = "ELA" 
    elif "third_grade" in path_lower or "grade 3" in path_lower or "grade_3" in path_lower:
        grade = "Grade 3"
        if "ela" not in path_lower and "math" not in path_lower and "geometry" not in path_lower:
            subject = "ELA"

    # Math specifics
    if subject == "Math" or subject == "Uncategorized_Subject":
        if "story problems" in title_lower or "numbers to 99" in title_lower or "within 100" in title_lower or "120 units" in title_lower or "geometry and time" in title_lower:
            grade = "Grade 1"
            subject = "Math"
        elif "working with data" in title_lower or "within 1,000" in title_lower or "within 1000" in title_lower or "geometry, time and money" in title_lower or "number line" in title_lower:
            grade = "Grade 2"
            subject = "Math"
        elif "operations to fractions" in title_lower or "fractions as number" in title_lower or "shapes and perimeter" in title_lower or "area and multiplication" in title_lower or "introducing multiplication" in title_lower:
            grade = "Grade 3"
            subject = "Math"
            
    return grade, subject

def parse_unit_name(title, dir_name):
    match = re.search(r'(Unit\s+\d+)(?:\s*[:\-]\s*(.*))?', title, re.IGNORECASE)
    if match:
        unit_num = match.group(1).title()
        unit_title = match.group(2) if match.group(2) else ""
        safe_title = "".join([c if c.isalnum() or c in " _-" else "" for c in unit_title]).strip()
        if safe_title:
            return f"{unit_num}_{safe_title.replace(' ', '_')}"
        return unit_num
    
    return dir_name

def organize_files(source_dir, dest_dir):
    print(f"Scanning {source_dir}...")
    # topdown=False ensures we process deeply nested children before their parents
    for root, dirs, files in os.walk(source_dir, topdown=False):
        if 'index.md' in files:
            index_path = os.path.join(root, 'index.md')
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if '---' in content:
                    parts = content.split('---')
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        title = metadata.get('title', os.path.basename(root))
                        
                        grade, subject = guess_grade_and_subject(title, root)
                        unit_name = parse_unit_name(title, os.path.basename(root))
                        
                        if unit_name == os.path.basename(root) and not title.lower().startswith("unit"):
                            safe_title = "".join([c if c.isalnum() or c in " _-" else "" for c in title]).strip()
                            unit_name = safe_title.replace(" ", "_").strip("_")
                            
                        target_path = os.path.join(dest_dir, grade, subject, unit_name)
                        
                        print(f"Moving: '{title}' -> {target_path}")
                        os.makedirs(target_path, exist_ok=True)
                        
                        # Move all contents to target
                        for item in os.listdir(root):
                            s = os.path.join(root, item)
                            d = os.path.join(target_path, item)
                            
                            if os.path.abspath(s) == os.path.abspath(d): 
                                continue
                            
                            if os.path.exists(d):
                                if os.path.isdir(d):
                                    shutil.rmtree(d)
                                else:
                                    os.remove(d)
                            shutil.move(s, d)
            except Exception as e:
                print(f"Error processing {root}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="reference_docs/scraped")
    parser.add_argument("--dest", default="reference_docs/curriculum")
    args = parser.parse_args()
    
    organize_files(args.source, args.dest)
    print("Done organizing.")
