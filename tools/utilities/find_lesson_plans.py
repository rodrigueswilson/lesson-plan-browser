"""Find all lesson plan files in the directory tree."""
from pathlib import Path

def find_lesson_plans(root_dir):
    """Recursively find all .docx files."""
    root = Path(root_dir)
    
    if not root.exists():
        print(f"❌ Directory not found: {root}")
        return []
    
    print(f"Searching in: {root}\n")
    
    # Find all .docx files recursively
    all_docx = list(root.rglob('*.docx'))
    
    # Filter out temp files
    lesson_plans = [f for f in all_docx if not f.name.startswith('~')]
    
    # Group by directory
    by_dir = {}
    for file in lesson_plans:
        dir_name = file.parent.name
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(file)
    
    # Print organized results
    print(f"Found {len(lesson_plans)} .docx files in {len(by_dir)} directories:\n")
    
    for dir_name, files in sorted(by_dir.items()):
        print(f"📁 {dir_name}/ ({len(files)} files)")
        for file in sorted(files):
            print(f"   - {file.name}")
        print()
    
    return lesson_plans

if __name__ == '__main__':
    root_dir = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan'
    files = find_lesson_plans(root_dir)
    
    print(f"\n{'='*80}")
    print(f"Total: {len(files)} lesson plan files found")
    print(f"{'='*80}")
