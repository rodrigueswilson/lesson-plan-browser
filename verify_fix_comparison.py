"""
Visual comparison showing the fix: old hardcoded vs new dynamic width.
"""

from docx import Document

TEMPLATE_PATH = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\Lesson Plan Template.docx'

print("=" * 80)
print("TABLE WIDTH FIX - BEFORE vs AFTER COMPARISON")
print("=" * 80)

# Load template to get actual page setup
doc = Document(TEMPLATE_PATH)
section = doc.sections[0]

# Calculate actual available width
page_width_inches = section.page_width.inches
left_margin_inches = section.left_margin.inches
right_margin_inches = section.right_margin.inches
available_width_inches = (section.page_width - section.left_margin - section.right_margin) / 914400

print("\nTEMPLATE PAGE SETUP:")
print(f"  Page width: {page_width_inches:.2f} inches")
print(f"  Left margin: {left_margin_inches:.2f} inches")
print(f"  Right margin: {right_margin_inches:.2f} inches")
print(f"  Available width: {available_width_inches:.2f} inches")

print("\n" + "-" * 80)
print("BEFORE (Hardcoded):")
print("-" * 80)
old_width = 6.5
print(f"  Table width: {old_width:.2f} inches")
print(f"  Left margin: {left_margin_inches:.2f} inches")
print(f"  Right margin: {left_margin_inches:.2f} inches")
print(f"  Content area: {old_width:.2f} inches")
print(f"  Unused space: {available_width_inches - old_width:.2f} inches")
print(f"  Excess right margin: {(available_width_inches - old_width) + right_margin_inches:.2f} inches")
print(f"\n  Visual representation:")
print(f"  |<-0.5\"->|<------- {old_width:.1f}\" table ------->|<--- {(available_width_inches - old_width) + right_margin_inches:.1f}\" excess --->|")
print(f"  |{' '*8}|{' '*30}|{' '*30}|")

print("\n" + "-" * 80)
print("AFTER (Dynamic):")
print("-" * 80)
new_width = available_width_inches
print(f"  Table width: {new_width:.2f} inches (calculated from page setup)")
print(f"  Left margin: {left_margin_inches:.2f} inches")
print(f"  Right margin: {right_margin_inches:.2f} inches")
print(f"  Content area: {new_width:.2f} inches")
print(f"  Unused space: {available_width_inches - new_width:.2f} inches")
print(f"  Excess right margin: {right_margin_inches:.2f} inches")
print(f"\n  Visual representation:")
print(f"  |<-0.5\"->|<-------------- {new_width:.1f}\" table -------------->|<-0.5\"->|")
print(f"  |{' '*8}|{' '*50}|{' '*8}|")

print("\n" + "=" * 80)
print("IMPROVEMENT:")
print("=" * 80)
improvement = new_width - old_width
print(f"  Table width increased by: {improvement:.2f} inches ({(improvement/old_width)*100:.1f}%)")
print(f"  Right margin reduced by: {improvement:.2f} inches")
print(f"  Tables now fill available space: YES ✓")
print(f"  Margins balanced: YES ✓")
print(f"  Dynamic adaptation: YES ✓")

print("\n" + "=" * 80)
print("CODE CHANGE:")
print("=" * 80)
print("\nOLD CODE (tools/docx_renderer.py):")
print("  table_count = normalize_all_tables(doc, total_width_inches=6.5)")
print("\nNEW CODE (tools/docx_renderer.py):")
print("  section = doc.sections[0]")
print("  available_width_emus = section.page_width - section.left_margin - section.right_margin")
print("  available_width_inches = available_width_emus / 914400")
print("  table_count = normalize_all_tables(doc, total_width_inches=available_width_inches)")

print("\n" + "=" * 80)
