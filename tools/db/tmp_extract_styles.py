import os

path = r'd:\LP\reference_docs\scraped\Unit_1__Adding__Subtracting_and_Working_With_Data\Tab_1\Unit_1__Adding__Subtracting_and_Working_With_Data\Tab_1\Unit_3__Measuring_Length\Tab_1\Unit_3__Adding_and_Subtracting_Within_20\Tab_1\Unit_5__Arithmetic_in_Base_Ten\Unit_5__Arithmetic_in_Base_Ten\Unit_5__Rational_Number_Arithmetic\Unit_5__Rational_Number_Arithmetic\Unit_7__Exponents_and_Scientific_Notation\Unit_7__Exponents_and_Scientific_Notation\Unit_1__Area_and_Surface_Area\Unit_1__Area_and_Surface_Area\Unit_6__More_Decimal_and_Fraction_Operations\Tab_1\Unit_5__Place_Value_Patterns_and_Decimal_Operations\Tab_1\Unit_7__Rational_Numbers\Unit_7__Rational_Numbers\Unit_7__Shapes_on_the_Coordinate_Plane\Tab_1\Unit_2__Area_and_Multiplication\Tab_1\originals\Unit_2__Area_and_Multiplication.html'

import re
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        file_size = os.path.getsize(path)
        f.seek(file_size // 2)
        content = f.read(100000)
        # Find any class definitions like .classname{props}
        matches = re.findall(r'\.[a-z0-9_-]+\{[^\}]+\}', content)
        for m in matches[:20]:
            print(m)
else:
    print(f"Path not found: {path}")
