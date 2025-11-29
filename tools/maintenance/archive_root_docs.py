"""
Archive root-level documentation files according to Phase 4 rules.

This script identifies and moves documentation files from root to archive directories.
"""
import shutil
from pathlib import Path

# Files that should stay active (do NOT archive)
ACTIVE_FILES = {
    'FUTURE_SESSION_PLAN.md',  # Active planning document
    'decluttering_plan.md',     # The plan itself - keep active
    'README.md',                # Main README
}

def categorize_file(filename: str) -> tuple[str, str] | None:
    """Return (category, archive_subdir) or None if should stay active."""
    
    if filename in ACTIVE_FILES:
        return None
    
    # Session summaries → sessions/
    if filename.startswith('SESSION_') or filename.startswith('NEXT_SESSION_'):
        return ('session', 'sessions')
    
    # Fix documentation → fixes/
    if '_FIX' in filename and not filename.startswith('FIXES_NEEDED'):
        return ('fix', 'fixes')
    
    # Implementation plans and completions → implementations/
    if '_PLAN' in filename or '_COMPLETE' in filename:
        return ('implementation', 'implementations')
    
    # Analysis documents → analysis/
    if '_ANALYSIS' in filename or '_DIAGNOSIS' in filename or '_FINDINGS' in filename:
        return ('analysis', 'analysis')
    
    return None

def archive_root_docs():
    """Archive root-level documentation files."""
    
    root = Path(__file__).resolve().parent.parent.parent
    archive_base = root / 'docs' / 'archive'
    
    files_to_archive = {
        'sessions': [],
        'fixes': [],
        'implementations': [],
        'analysis': [],
        'keep_active': []
    }
    
    # Find all markdown files at root
    root_md_files = list(root.glob('*.md'))
    
    print(f"Found {len(root_md_files)} markdown files at root level\n")
    
    for md_file in sorted(root_md_files):
        category = categorize_file(md_file.name)
        
        if category is None:
            files_to_archive['keep_active'].append(md_file.name)
            continue
        
        cat_type, subdir = category
        files_to_archive[subdir].append(md_file.name)
    
    # Print summary
    print("=" * 60)
    print("ARCHIVING PLAN")
    print("=" * 60)
    print(f"\nKeep Active: {len(files_to_archive['keep_active'])} files")
    for name in sorted(files_to_archive['keep_active']):
        print(f"  - {name}")
    
    print(f"\nArchive to sessions/: {len(files_to_archive['sessions'])} files")
    print(f"Archive to fixes/: {len(files_to_archive['fixes'])} files")
    print(f"Archive to implementations/: {len(files_to_archive['implementations'])} files")
    print(f"Archive to analysis/: {len(files_to_archive['analysis'])} files")
    
    return files_to_archive

if __name__ == '__main__':
    archive_root_docs()

