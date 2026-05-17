import os
import shutil

# The extremely long path
base = r'd:\LP\reference_docs\scraped\Unit_1__Adding__Subtracting_and_Working_With_Data\Tab_1\Unit_1__Adding__Subtracting_and_Working_With_Data\Tab_1\Unit_3__Measuring_Length\Tab_1\Unit_3__Adding_and_Subtracting_Within_20\Tab_1\Unit_5__Arithmetic_in_Base_Ten\Unit_5__Arithmetic_in_Base_Ten\Unit_5__Rational_Number_Arithmetic\Unit_5__Rational_Number_Arithmetic\Unit_7__Exponents_and_Scientific_Notation\Unit_7__Exponents_and_Scientific_Notation\Unit_1__Area_and_Surface_Area\Unit_1__Area_and_Surface_Area\Unit_6__More_Decimal_and_Fraction_Operations\Tab_1\Unit_5__Place_Value_Patterns_and_Decimal_Operations\Tab_1\Unit_7__Rational_Numbers\Unit_7__Rational_Numbers\Unit_7__Shapes_on_the_Coordinate_Plane\Tab_1\Unit_2__Area_and_Multiplication\Tab_1'

dest = r'd:\LP\temp_u2'
if not os.path.exists(dest):
    os.makedirs(dest)

def long_path(p):
    return "\\\\?\\" + os.path.abspath(p)

# Copy Tab_1.md
src_file = os.path.join(base, 'Tab_1.md')
shutil.copy(long_path(src_file), long_path(os.path.join(dest, 'Tab_1.md')))

# Copy originals folder
src_originals = os.path.join(base, 'originals')
dest_originals = os.path.join(dest, 'originals')
if not os.path.exists(dest_originals):
    os.makedirs(dest_originals)

for f in os.listdir(long_path(src_originals)):
    src_f = os.path.join(src_originals, f)
    shutil.copy(long_path(src_f), long_path(os.path.join(dest_originals, f)))

print("Done copying.")
