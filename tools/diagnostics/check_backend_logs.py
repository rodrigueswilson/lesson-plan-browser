"""
Check backend logs for debug output about vocabulary_cognates.
If backend is logging to a file, read it. Otherwise, we need to check console output.
"""
import sys
from pathlib import Path

# Check common log locations
log_files = [
    "logs/backend.log",
    "data/backend.log",
    "backend.log",
    "app.log",
]

print("Checking for backend log files...")
for log_file in log_files:
    path = Path(log_file)
    if path.exists():
        print(f"\n[OK] Found log file: {log_file}")
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Look for vocabulary_cognates related logs
            vocab_lines = [l for l in lines if 'vocabulary_cognates' in l.lower() or 'vocab_step' in l.lower() or 'create_lesson_step' in l.lower()]
            if vocab_lines:
                print(f"\nFound {len(vocab_lines)} relevant log lines:")
                for line in vocab_lines[-20:]:  # Last 20 lines
                    print(f"  {line.strip()}")
            else:
                print(f"  No vocabulary_cognates related logs found in {len(lines)} lines")
        break
else:
    print("[INFO] No log files found. Backend logs may be in console output only.")
    print("\nTo see debug output, check the backend console window where uvicorn is running.")
    print("Or restart the backend and watch the console output when generating steps.")

