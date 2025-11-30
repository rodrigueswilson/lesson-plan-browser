# How the Code Determines Which Folder Will Store Files

## 📁 Step-by-Step Folder Determination Process

### 1. **Base Path Resolution**

The code first determines the base lesson plan path using this hierarchy:

```python
# In batch_processor.py (line 1587)
file_mgr = get_file_manager(base_path=user.get("base_path_override"))
```

**Priority Order:**
1. **User's `base_path_override`** (highest priority)
2. **Environment variable `LESSON_PLAN_BASE_PATH`** 
3. **Default path**: `F:/rodri/Documents/OneDrive/AS/Lesson Plan`

```python
# In file_manager.py (lines 26-31)
self.base_path = Path(
    base_path                                    # 1. User override
    or os.getenv(
        "LESSON_PLAN_BASE_PATH",                # 2. Environment variable
        r"F:/rodri/Documents/OneDrive/AS/Lesson Plan"  # 3. Default
    )
)
```

### 2. **Week Folder Calculation**

Once the base path is determined, the code calculates the specific week folder:

```python
# In batch_processor.py (line 1588)
week_folder = file_mgr.get_week_folder(week_of)  # week_of = "11-17-11-21"
```

**Week Folder Logic:**

#### Step A: Calculate Week Number
```python
# From "11-17-11-21" → week_num = 47
week_num = self._calculate_week_number(week_of)
year = datetime.now().strftime("%y")  # "25"
```

#### Step B: Try Current Year First
```python
folder_name = f"{year} W{week_num:02d}"  # "25 W47"
folder_path = self.base_path / folder_name  # "F:/.../Lesson Plan/25 W47"
```

#### Step C: If Not Found, Try Other Years
```python
for y in ["22", "23", "24", "25", "26", "27"]:
    folder_name = f"{y} W{week_num:02d}"  # "24 W47", "23 W47", etc.
    folder_path = self.base_path / folder_name
    if folder_path.exists():
        return folder_path
```

#### Step D: Fallback to Most Recent Week
```python
available_weeks = self.get_available_weeks(limit=1)
if available_weeks:
    return Path(most_recent["path"])
```

#### Step E: Final Fallback
```python
return self.base_path / f"{year} W{week_num:02d}"
```

### 3. **Final Output Path**

The final file path is constructed:

```python
# In batch_processor.py (lines 1595-1598)
week_num = self._get_week_num(week_of)                 # 47
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # "20251116_213107"
filename = f"{user['name'].replace(' ', '_')}_Weekly_W{week_num:02d}_{week_of.replace('/', '-')}_{timestamp}.docx"
output_path = str(week_folder / filename)
```

## 🎯 Example Scenarios

### **Scenario 1: User with Override**
```python
user = {
    "name": "Ms. Wilson",
    "base_path_override": "G:/Teachers/Wilson/Lesson Plans"
}
week_of = "11-17-11-21"

# Result:
# Base: G:/Teachers/Wilson/Lesson Plans
# Week: G:/Teachers/Wilson/Lesson Plans/25 W47
# File: G:/Teachers/Wilson/Lesson Plans/25 W47/Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
```

### **Scenario 2: User with No Override**
```python
user = {"name": "Ms. Wilson"}  # No base_path_override
week_of = "11-17-11-21"

# Result:
# Base: F:/rodri/Documents/OneDrive/AS/Lesson Plan (from environment/default)
# Week: F:/rodri/Documents/OneDrive/AS/Lesson Plan/25 W47
# File: F:/rodri/Documents/OneDrive/AS/Lesson Plan/25 W47/Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
```

### **Scenario 3: Week Folder Doesn't Exist**
```python
# If "25 W47" folder doesn't exist, the code:
# 1. Tries "24 W47", "23 W47", etc.
# 2. Falls back to most recent existing week folder
# 3. Creates the expected path if none exist

# Result: Files go to the most appropriate existing folder
```

## 📋 Objectives Files Use Same Logic

The objectives generation code uses the **exact same path**:

```python
# In the objectives method
docx_file = Path(docx_path)        # Full path to DOCX
output_dir = docx_file.parent       # Same week folder (e.g., "25 W47")
base_name = docx_file.stem          # Same filename base

# Objectives files:
# output_dir / f"{base_name}_Objectives.html"
# output_dir / f"{base_name}_Objectives.pdf"
```

## ✅ Key Points

1. **User-specific**: Each user can have their own base path
2. **Week-specific**: Files organized by ISO week numbers (W47, W48, etc.)
3. **Year-aware**: Handles multiple school years (22 W47, 23 W47, etc.)
4. **Flexible**: Falls back to existing folders if expected one doesn't exist
5. **Consistent**: Objectives files always use the same folder as DOCX

**Result**: Files are stored in the user's lesson plan structure, respecting their individual folder preferences and the existing week-based organization.
