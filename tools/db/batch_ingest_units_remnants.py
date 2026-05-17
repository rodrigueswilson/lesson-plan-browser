import os
import subprocess
import sys
import glob

python_exe = r"d:\LP\.venv\Scripts\python.exe"
extract_script = r"d:\LP\tools\db\extract_curriculum.py"

def ingest(grade, subject, unit_paths):
    for unit_path in unit_paths:
        if os.path.exists(unit_path):
            print(f"Ingesting (Grade {grade} {subject}): {unit_path}")
            # Try to infer subject from path if it's 'Uncategorized'
            inferred_subject = subject
            if subject == "Uncategorized":
                if "Math" in unit_path: inferred_subject = "Math"
                elif "ELA" in unit_path: inferred_subject = "ELA"
            
            subprocess.run([python_exe, extract_script, unit_path, str(grade), inferred_subject], check=True)
        else:
            print(f"WARNING: Path not found: {unit_path}")

# --- DYNAMIC INGESTION OF UNCATEGORIZED REMNANTS ---
print("Scanning for remnants in Uncategorized_Grade...")
remnant_pattern = r"d:\LP\reference_docs\curriculum\Uncategorized_Grade\**\Tab_1.md"
remnant_paths = glob.glob(remnant_pattern, recursive=True)

print(f"Found {len(remnant_paths)} remnant units to ingest.")

# We'll tag these as Grade 0 (Unknown) for now, or Grade 4/5 if we want to guess
# Let's use Grade 0 to signify 'RefStore Remnant'
ingest(0, "Uncategorized", remnant_paths)

print("Final remnants ingestion complete.")
