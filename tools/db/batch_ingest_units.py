import os
import subprocess
import sys

python_exe = r"d:\LP\.venv\Scripts\python.exe"
extract_script = r"d:\LP\tools\db\extract_curriculum.py"

def ingest(grade, subject, unit_paths):
    for unit_path in unit_paths:
        if os.path.exists(unit_path):
            print(f"Ingesting (Grade {grade} {subject}): {unit_path}")
            subprocess.run([python_exe, extract_script, unit_path, str(grade), subject], check=True)
        else:
            print(f"WARNING: Path not found: {unit_path}")

# --- GRADE 1 ---
g1_math_base = r"d:\LP\reference_docs\curriculum\Grade 1\Math"
g1_math_units = [
    os.path.join(g1_math_base, "Unit 2_Add_and_Subtract_Within_100", "Tab_1", "Tab_1.md"),
    os.path.join(g1_math_base, "Unit 4_Numbers_to_99", "Tab_1", "Tab_1.md"),
    os.path.join(g1_math_base, "Unit 5_Adding_Within_100", "Tab_1", "Tab_1.md"),
    os.path.join(g1_math_base, "Unit 6_Length_Measurements_Within_120_Units", "Tab_1", "Tab_1.md"),
    os.path.join(g1_math_base, "Unit 7_Geometry_and_Time", "Tab_1", "Tab_1.md"),
]
ingest(1, "Math", g1_math_units)

# --- GRADE 2 ---
g2_math_base = r"d:\LP\reference_docs\curriculum\Grade 2\Math"
g2_math_units = [
    os.path.join(g2_math_base, "Unit 1_Adding_Subtracting_and_Working_With_Data", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 2_Add_and_Subtract_Within_100", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 3_Measuring_Length", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 4_Addition_and_Subtraction_on_the_Number_Line", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 5_Numbers_to_1000", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 6_Geometry_Time_and_Money", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 7_Adding_and_Subtracting_within_1000", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 8_Equal_Groups", "Tab_1", "Tab_1.md"),
    os.path.join(g2_math_base, "Unit 9_Putting_It_All_Together", "Tab_1", "Tab_1.md"),
]
ingest(2, "Math", g2_math_units)

# Grade 2 ELA
g2_ela_base = r"d:\LP\reference_docs\curriculum\Grade 2\ELA\Copy_of_02_-_Second_Grade_Unit_Description_and_Summary_of_Key_Learning"
g2_ela_units = [
    os.path.join(g2_ela_base, f"Grade_2_Unit_{i}", f"Grade_2_Unit_{i}.md")
    for i in range(1, 11)
]
ingest(2, "ELA", g2_ela_units)

# Grade 3 ELA
g3_ela_base = r"d:\LP\reference_docs\curriculum\Grade 3\ELA\Copy_of_03_-_Third_Grade_Unit_Description_and_Summary_of_Key_Learning"
g3_ela_units = [
    os.path.join(g3_ela_base, f"Grade_3_Unit_{i}", f"Grade_3_Unit_{i}.md")
    for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
]
ingest(3, "ELA", g3_ela_units)

print("Batch ingestion complete.")
