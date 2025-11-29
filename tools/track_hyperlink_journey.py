"""
Track each hyperlink's journey from input files to output file.
Identifies why table links from input become paragraph links in output.

Works for both Daniela and Wilson lesson plans.
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser

# Configuration for different lesson plans
LESSON_PLANS = {
    'daniela': {
        'name': 'Daniela W43',
        'input_files': [
            r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx',
            r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Mrs. Grande Science 10_20- 10_24.docx'
        ],
        'output_file': r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Daniela_Silva_Weekly_W43_10-20-10-24_20251019_155023.docx'
    },
    'wilson': {
        'name': 'Wilson W43',
        'input_files': [
            r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Davies Lesson Plans.docx',
            r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\Lang Lesson Plans 10_20_25-10_24_25.docx',
            r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Lonesky Lesson Plans.docx',
        ],
        'output_file': r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_160328.docx'
    }
}


def extract_all_links(file_path, file_label):
    """Extract all hyperlinks from a file with metadata."""
    
    if not Path(file_path).exists():
        print(f"⚠️  File not found: {file_path}")
        return []
    
    try:
        parser = DOCXParser(file_path)
        hyperlinks = parser.extract_hyperlinks()
        
        # Add source file label
        for link in hyperlinks:
            link['source_file'] = file_label
        
        return hyperlinks
    except Exception as e:
        print(f"❌ Error extracting from {file_label}: {e}")
        return []


def create_link_signature(link):
    """Create a unique signature for a link to track it."""
    # Use text + URL as signature (truncated for comparison)
    text = link.get('text', '')[:50].strip().lower()
    url = link.get('url', '')[:100].strip().lower()
    return f"{text}|{url}"


def track_links(lesson_plan_key):
    """Track all hyperlinks from input to output."""
    
    config = LESSON_PLANS[lesson_plan_key]
    
    print("="*80)
    print(f"HYPERLINK JOURNEY TRACKING: {config['name']}")
    print("="*80)
    print()
    
    # Step 1: Extract from all input files
    print("Step 1: Extracting from input files...")
    print("-" * 80)
    
    all_input_links = []
    input_by_file = {}
    
    for i, input_file in enumerate(config['input_files'], 1):
        file_name = Path(input_file).name
        file_label = f"Input {i}: {file_name}"
        
        links = extract_all_links(input_file, file_label)
        
        if links:
            all_input_links.extend(links)
            input_by_file[file_label] = links
            
            table_links = [l for l in links if l.get('table_idx') is not None]
            para_links = [l for l in links if l.get('table_idx') is None]
            
            print(f"{file_label}:")
            print(f"  Total: {len(links)} (Table: {len(table_links)}, Paragraph: {len(para_links)})")
    
    print()
    print(f"Total input links: {len(all_input_links)}")
    
    input_table_links = [l for l in all_input_links if l.get('table_idx') is not None]
    input_para_links = [l for l in all_input_links if l.get('table_idx') is None]
    
    print(f"  Table links: {len(input_table_links)}")
    print(f"  Paragraph links: {len(input_para_links)}")
    print()
    
    # Step 2: Extract from output file
    print("Step 2: Extracting from output file...")
    print("-" * 80)
    
    output_links = extract_all_links(config['output_file'], "Output")
    
    if not output_links:
        print("❌ No links found in output")
        return
    
    output_table_links = [l for l in output_links if l.get('table_idx') is not None]
    output_para_links = [l for l in output_links if l.get('table_idx') is None]
    
    print(f"Total output links: {len(output_links)}")
    print(f"  Table links: {len(output_table_links)}")
    print(f"  Paragraph links: {len(output_para_links)}")
    print()
    
    # Step 3: Create link signatures for matching
    print("Step 3: Matching input to output...")
    print("-" * 80)
    print()
    
    # Create signature maps
    input_signatures = {}
    for link in all_input_links:
        sig = create_link_signature(link)
        if sig not in input_signatures:
            input_signatures[sig] = []
        input_signatures[sig].append(link)
    
    output_signatures = {}
    for link in output_links:
        sig = create_link_signature(link)
        if sig not in output_signatures:
            output_signatures[sig] = []
        output_signatures[sig].append(link)
    
    # Step 4: Track transformations
    print("Step 4: Tracking transformations...")
    print("-" * 80)
    print()
    
    # Categories
    table_to_table = []  # Input table → Output table
    table_to_para = []   # Input table → Output paragraph (PROBLEM!)
    para_to_para = []    # Input paragraph → Output paragraph (expected)
    para_to_table = []   # Input paragraph → Output table (unexpected)
    new_links = []       # Links only in output
    lost_links = []      # Links only in input
    
    # Match each input link to output
    for sig, input_links in input_signatures.items():
        if sig in output_signatures:
            # Link exists in both input and output
            for input_link in input_links:
                for output_link in output_signatures[sig]:
                    input_is_table = input_link.get('table_idx') is not None
                    output_is_table = output_link.get('table_idx') is not None
                    
                    if input_is_table and output_is_table:
                        table_to_table.append((input_link, output_link))
                    elif input_is_table and not output_is_table:
                        table_to_para.append((input_link, output_link))
                    elif not input_is_table and output_is_table:
                        para_to_table.append((input_link, output_link))
                    else:
                        para_to_para.append((input_link, output_link))
        else:
            # Link only in input (lost)
            lost_links.extend(input_links)
    
    # Find new links (only in output)
    for sig, output_links in output_signatures.items():
        if sig not in input_signatures:
            new_links.extend(output_links)
    
    # Step 5: Report findings
    print("="*80)
    print("TRANSFORMATION SUMMARY")
    print("="*80)
    print()
    
    print(f"✅ Table → Table: {len(table_to_table)} links (correct)")
    print(f"⚠️  Table → Paragraph: {len(table_to_para)} links (INVESTIGATE!)")
    print(f"✅ Paragraph → Paragraph: {len(para_to_para)} links (expected)")
    print(f"⚠️  Paragraph → Table: {len(para_to_table)} links (unexpected)")
    print(f"🆕 New links (only in output): {len(new_links)}")
    print(f"❌ Lost links (only in input): {len(lost_links)}")
    print()
    
    # Step 6: Investigate Table → Paragraph transformations
    if table_to_para:
        print("="*80)
        print(f"INVESTIGATING: TABLE → PARAGRAPH ({len(table_to_para)} links)")
        print("="*80)
        print()
        print("These links were in TABLES in input but became PARAGRAPHS in output.")
        print("This suggests they were NOT placed via coordinates.")
        print()
        
        for i, (input_link, output_link) in enumerate(table_to_para[:10], 1):
            print(f"{i}. '{input_link['text'][:50]}'")
            print(f"   INPUT:")
            print(f"     Source: {input_link['source_file']}")
            print(f"     Location: Table {input_link['table_idx']}, Row {input_link['row_idx']}, Cell {input_link['cell_idx']}")
            print(f"     Row label: '{input_link.get('row_label', 'N/A')[:40]}'")
            print(f"     Col header: '{input_link.get('col_header', 'N/A')}'")
            print(f"   OUTPUT:")
            print(f"     Location: Paragraph (table_idx = None)")
            print(f"     Context: {output_link.get('context_snippet', 'N/A')[:60]}")
            print()
        
        if len(table_to_para) > 10:
            print(f"... and {len(table_to_para) - 10} more")
            print()
    
    # Step 7: Investigate lost links
    if lost_links:
        print("="*80)
        print(f"INVESTIGATING: LOST LINKS ({len(lost_links)} links)")
        print("="*80)
        print()
        print("These links were in INPUT but NOT found in OUTPUT.")
        print()
        
        for i, link in enumerate(lost_links[:5], 1):
            is_table = link.get('table_idx') is not None
            print(f"{i}. '{link['text'][:50]}'")
            print(f"   Source: {link['source_file']}")
            print(f"   Type: {'Table' if is_table else 'Paragraph'}")
            if is_table:
                print(f"   Location: Table {link['table_idx']}, Row {link['row_idx']}, Cell {link['cell_idx']}")
            print()
        
        if len(lost_links) > 5:
            print(f"... and {len(lost_links) - 5} more")
            print()
    
    # Step 8: Investigate new links
    if new_links:
        print("="*80)
        print(f"INVESTIGATING: NEW LINKS ({len(new_links)} links)")
        print("="*80)
        print()
        print("These links are in OUTPUT but were NOT in INPUT.")
        print("They may have been generated or duplicated.")
        print()
        
        for i, link in enumerate(new_links[:5], 1):
            is_table = link.get('table_idx') is not None
            print(f"{i}. '{link['text'][:50]}'")
            print(f"   Type: {'Table' if is_table else 'Paragraph'}")
            if is_table:
                print(f"   Location: Table {link['table_idx']}, Row {link['row_idx']}, Cell {link['cell_idx']}")
            print()
        
        if len(new_links) > 5:
            print(f"... and {len(new_links) - 5} more")
            print()
    
    # Step 9: Final summary
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    
    if table_to_para:
        print(f"⚠️  FOUND ISSUE: {len(table_to_para)} table links became paragraph links")
        print(f"   This means they were NOT placed via coordinate placement")
        print(f"   They ended up in the 'Referenced Links' fallback section")
        print()
        print("   Possible reasons:")
        print("   1. Coordinate placement failed for these links")
        print("   2. Links were extracted as table links but renderer saw them as paragraphs")
        print("   3. Multi-slot processing issue")
        print()
    else:
        print(f"✅ NO ISSUES: All table links stayed as table links")
        print(f"   Coordinate placement worked perfectly")
        print()
    
    if lost_links:
        print(f"⚠️  {len(lost_links)} links were lost (not in output)")
    
    if new_links:
        print(f"🆕 {len(new_links)} new links appeared (not in input)")
    
    print()


def main():
    """Track hyperlinks for both lesson plans."""
    
    print("\n")
    print("="*80)
    print("HYPERLINK JOURNEY TRACKER")
    print("Tracking links from input to output for Daniela and Wilson")
    print("="*80)
    print("\n")
    
    # Track Daniela
    track_links('daniela')
    
    print("\n\n")
    
    # Track Wilson
    track_links('wilson')
    
    print("\n")
    print("="*80)
    print("TRACKING COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
