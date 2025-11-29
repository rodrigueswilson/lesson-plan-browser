"""
Calculate the optimal table width for a letter-size page with 0.5-inch margins.
"""

# Standard US Letter page dimensions
PAGE_WIDTH_INCHES = 8.5
PAGE_HEIGHT_INCHES = 11.0

# Margins
LEFT_MARGIN = 0.5
RIGHT_MARGIN = 0.5
TOP_MARGIN = 0.5
BOTTOM_MARGIN = 0.5

# Calculate available width
available_width_inches = PAGE_WIDTH_INCHES - LEFT_MARGIN - RIGHT_MARGIN

# Conversion factors
EMU_PER_INCH = 914400  # English Metric Units
DXA_PER_INCH = 1440    # Twentieths of a point (used in Word XML)
TWIPS_PER_INCH = 1440  # Same as DXA

# Convert to different units
available_width_emus = int(available_width_inches * EMU_PER_INCH)
available_width_dxa = int(available_width_inches * DXA_PER_INCH)

print("=" * 70)
print("TABLE WIDTH CALCULATION FOR 0.5-INCH MARGINS")
print("=" * 70)
print(f"\nPage Dimensions:")
print(f"  Page width: {PAGE_WIDTH_INCHES} inches")
print(f"  Left margin: {LEFT_MARGIN} inches")
print(f"  Right margin: {RIGHT_MARGIN} inches")

print(f"\nAvailable Width for Table:")
print(f"  {available_width_inches} inches")
print(f"  {available_width_emus:,} EMUs")
print(f"  {available_width_dxa:,} DXA (Word XML format)")

print(f"\nCurrent Template Tables:")
print(f"  Current width: ~10.03 inches (9,175,750 EMUs)")
print(f"  Exceeds margins by: {10.03 - available_width_inches:.2f} inches")

print(f"\nRecommendation:")
print(f"  Set table width to: {available_width_inches} inches")
print(f"  In python-docx: table.width = {available_width_emus}")
print(f"  In Word XML: <w:tblW w:w=\"{available_width_dxa}\" w:type=\"dxa\"/>")

print("\n" + "=" * 70)
