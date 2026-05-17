import re
paths = [
    r"d:\LP\reference_docs\curriculum\Grade 3\ELA\Copy_of_03_-_Third_Grade_Unit_Description_and_Summary_of_Key_Learning\Grade_3_Unit_2\Grade_3_Unit_2.md",
    r"d:\LP\reference_docs\curriculum\Grade 3\ELA\Copy_of_03_-_Third_Grade_Unit_Description_and_Summary_of_Key_Learning\Grade_3_Unit_3\Grade_3_Unit_3.md",
    r"d:\LP\reference_docs\curriculum\Grade 3\Math\Unit 2_Area_and_Multiplication\Tab_1\Tab_1.md"
]
for p in paths:
    m = re.search(r'Unit[\s_]*(\d+)', p, re.IGNORECASE)
    print(f"{p} -> {m.group(1) if m else 'None'}")
