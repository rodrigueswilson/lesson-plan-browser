"""Remove plans/lesson-steps/lesson-mode/user-plans/status from api.py (moved to routers.plans)."""
from pathlib import Path

api_path = Path(__file__).resolve().parent.parent / "backend" / "api.py"
lines = api_path.read_text(encoding="utf-8").splitlines()

start_marker = "# Lesson Plan and Steps Endpoints"
end_marker = '"/api/process-week"'

start_i = None
end_i = None
for i, line in enumerate(lines):
    if line.strip() == start_marker and start_i is None:
        start_i = i
    if end_marker in line and start_i is not None:
        end_i = i
        break

if start_i is None or end_i is None:
    raise SystemExit(f"Could not find markers: start_i={start_i}, end_i={end_i}")

new_lines = lines[:start_i] + [""] + lines[end_i:]
api_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"Removed lines {start_i + 1}-{end_i} from api.py")
