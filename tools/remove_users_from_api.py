"""Remove user/slot/schedule routes from api.py (moved to routers.users)."""
from pathlib import Path

api_path = Path(__file__).resolve().parent.parent / "backend" / "api.py"
lines = api_path.read_text(encoding="utf-8").splitlines()

start_marker = '@app.get("/api/users", response_model=list[UserResponse]'
end_marker = "# Lesson Plan and Steps Endpoints"

start_i = None
end_i = None
for i, line in enumerate(lines):
    if start_marker in line and start_i is None:
        start_i = i
    if line.strip() == end_marker and start_i is not None:
        end_i = i
        break

if start_i is None or end_i is None:
    raise SystemExit("Could not find start or end marker")

new_lines = lines[:start_i] + [""] + lines[end_i:]
api_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"Removed lines {start_i + 1}-{end_i} from api.py")
