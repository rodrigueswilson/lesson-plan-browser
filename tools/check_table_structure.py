"""
Check if table structure (rows x columns) is consistent between input and output.
If yes, we can use row_index + column_index as a reliable placement hint!
"""

from docx import Document
from pathlib import Path

INPUT_FILE = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Davies Lesson Plans.docx'
OUTPUT_FILE = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_133850.docx'

def analyze_table_structure(file_path, label):
    """Analyze table structure."""
    
    doc = Document(file_path)
    
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}\n")
    
    # Find the daily plans table (has MONDAY in it)
    daily_table = None
    for idx, table in enumerate(doc.tables):
        if table.rows and table.rows[0].cells:
            for cell in table.rows[0].cells:
                if 'MONDAY' in cell.text.upper():
                    daily_table = table
                    print(f"Found daily plans table at index {idx}")
                    break
            if daily_table:
                break
    
    if not daily_table:
        print("No daily plans table found!")
        return None
    
    # Analyze structure
    num_rows = len(daily_table.rows)
    num_cols = len(daily_table.rows[0].cells) if daily_table.rows else 0
    
    print(f"\nTable dimensions: {num_rows} rows x {num_cols} columns")
    
    # Show row labels
    print(f"\nRow structure:")
    for row_idx, row in enumerate(daily_table.rows):
        if row.cells:
            first_cell = row.cells[0].text.strip()
            print(f"  Row {row_idx}: {first_cell[:50]}")
    
    # Show column headers
    print(f"\nColumn headers:")
    if daily_table.rows:
        for col_idx, cell in enumerate(daily_table.rows[0].cells):
            print(f"  Col {col_idx}: {cell.text.strip()[:30]}")
    
    return {
        'num_rows': num_rows,
        'num_cols': num_cols,
        'row_labels': [row.cells[0].text.strip() if row.cells else "" for row in daily_table.rows],
        'col_headers': [cell.text.strip() for cell in daily_table.rows[0].cells] if daily_table.rows else []
    }


def compare_structures(input_struct, output_struct):
    """Compare input and output table structures."""
    
    print(f"\n\n{'='*80}")
    print("STRUCTURE COMPARISON")
    print(f"{'='*80}\n")
    
    print(f"Dimensions:")
    print(f"  Input:  {input_struct['num_rows']} rows x {input_struct['num_cols']} cols")
    print(f"  Output: {output_struct['num_rows']} rows x {output_struct['num_cols']} cols")
    
    if input_struct['num_rows'] == output_struct['num_rows']:
        print(f"  ✓ Same number of rows")
    else:
        print(f"  ✗ Different number of rows")
    
    if input_struct['num_cols'] == output_struct['num_cols']:
        print(f"  ✓ Same number of columns")
    else:
        print(f"  ✗ Different number of columns")
    
    # Compare row labels
    print(f"\n\nRow labels comparison:")
    max_rows = max(len(input_struct['row_labels']), len(output_struct['row_labels']))
    
    matching_rows = 0
    for i in range(max_rows):
        input_label = input_struct['row_labels'][i] if i < len(input_struct['row_labels']) else "N/A"
        output_label = output_struct['row_labels'][i] if i < len(output_struct['row_labels']) else "N/A"
        
        match = "✓" if input_label == output_label else "✗"
        if input_label == output_label:
            matching_rows += 1
        
        print(f"  Row {i}: {match}")
        print(f"    Input:  {input_label[:50]}")
        print(f"    Output: {output_label[:50]}")
    
    match_pct = (matching_rows / max_rows * 100) if max_rows > 0 else 0
    print(f"\n  Matching rows: {matching_rows}/{max_rows} ({match_pct:.1f}%)")
    
    # Compare column headers
    print(f"\n\nColumn headers comparison:")
    max_cols = max(len(input_struct['col_headers']), len(output_struct['col_headers']))
    
    matching_cols = 0
    for i in range(max_cols):
        input_header = input_struct['col_headers'][i] if i < len(input_struct['col_headers']) else "N/A"
        output_header = output_struct['col_headers'][i] if i < len(output_struct['col_headers']) else "N/A"
        
        match = "✓" if input_header == output_header else "✗"
        if input_header == output_header:
            matching_cols += 1
        
        print(f"  Col {i}: {match} Input: '{input_header[:20]}' | Output: '{output_header[:20]}'")
    
    match_pct = (matching_cols / max_cols * 100) if max_cols > 0 else 0
    print(f"\n  Matching columns: {matching_cols}/{max_cols} ({match_pct:.1f}%)")
    
    # Conclusion
    print(f"\n\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}\n")
    
    if (input_struct['num_rows'] == output_struct['num_rows'] and 
        input_struct['num_cols'] == output_struct['num_cols'] and
        matching_rows / max_rows >= 0.8 and
        matching_cols / max_cols >= 0.8):
        print("✓ STRUCTURE IS CONSISTENT!")
        print("\n  → We CAN use row_index + column_index as placement hints")
        print("  → Links can be placed by their exact (row, col) position")
        print("  → This would be MORE RELIABLE than fuzzy text matching")
    else:
        print("✗ STRUCTURE IS NOT CONSISTENT")
        print("\n  → Cannot rely on row_index + column_index")
        print("  → Must use text-based matching")


def main():
    print("="*80)
    print("TABLE STRUCTURE ANALYSIS")
    print("="*80)
    print("\nChecking if input and output tables have the same structure...")
    
    input_struct = analyze_table_structure(INPUT_FILE, "INPUT TABLE (Davies)")
    output_struct = analyze_table_structure(OUTPUT_FILE, "OUTPUT TABLE (Davies)")
    
    if input_struct and output_struct:
        compare_structures(input_struct, output_struct)
    else:
        print("\n✗ Could not analyze table structures")


if __name__ == '__main__':
    main()
