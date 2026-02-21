
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.file_manager import FileManager
from tools.docx_parser import DOCXParser

def test_matching():
    fm = FileManager()
    week_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W51")
    
    print(f"Checking folder: {week_folder}")
    print(f"Exists: {week_folder.exists()}")
    
    all_files = list(week_folder.glob("*.docx"))
    print(f"Total files: {len(all_files)}")
    for f in all_files:
        skipped = fm._should_skip_file(f.name)
        print(f"  - {f.name} (Skipped: {skipped})")
        
    test_cases = [
        ("Donna Savoca", "Social Studies"),
        ("Kelsey Lang", "ELA"),
        ("Caitlin Davies", "Math")
    ]
    
    for teacher, subject in test_cases:
        print(f"\nMatching '{teacher}' / '{subject}':")
        # Test just like BatchProcessor does
        last_name = teacher.split()[-1]
        patterns = [teacher, last_name]
        
        found = None
        for p in patterns:
            res = fm.find_primary_teacher_file(week_folder, p, subject)
            print(f"  Pattern '{p}' -> {res}")
            if res:
                found = res
                break
        
        if found:
            print(f"  [OK] Found: {Path(found).name}")
            try:
                parser = DOCXParser(found)
                print(f"  [OK] Parsed Document. Tables: {len(parser.doc.tables)}")
            except Exception as e:
                print(f"  [FAILED] Could not parse DOCX: {e}")
        else:
            print(f"  [FAILED] No match")

if __name__ == "__main__":
    test_matching()
