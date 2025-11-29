"""
Test robust DOCX parser with all teacher formats.
"""

from tools.docx_parser_robust import DOCXParser

# Test files
test_files = [
    ("Davies", r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41\10_6-10_10 Davies Lesson Plans.docx", "Math"),
    ("Lang", r"d:\LP\input\Lang Lesson Plans 9_15_25-9_19_25.docx", "Math"),
    ("Savoca", r"d:\LP\input\Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx", "Math"),
    ("Piret", r"d:\LP\input\Piret Lesson Plans 9_22_25-9_26_25.docx", "ELA"),
]

print("="*80)
print("ROBUST DOCX PARSER TEST")
print("="*80)
print()

for teacher_name, file_path, subject in test_files:
    print(f"\n{'='*80}")
    print(f"TESTING: {teacher_name}")
    print(f"File: {file_path}")
    print(f"Extracting: {subject}")
    print(f"{'='*80}\n")
    
    try:
        # Create parser
        parser = DOCXParser(file_path)
        
        # Validate structure
        validation = parser.validate_structure()
        print(f"📊 Document Structure:")
        print(f"   Total tables: {validation['total_tables']}")
        print(f"   Subjects found: {validation['subjects_found']}")
        print(f"   Subjects: {', '.join(validation['subjects'])}")
        print(f"   Format types: {validation['format_types']}")
        print(f"   Valid: {'✅' if validation['is_valid'] else '❌'}")
        print()
        
        # Show warnings
        if validation['warnings']:
            print(f"⚠️  Warnings ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"   - {warning}")
            print()
        
        # Extract subject content
        content = parser.extract_subject_content(subject)
        
        if content['found']:
            print(f"✅ {subject} Content Extracted:")
            print(f"   Format: {content['format_type']}")
            print(f"   Teacher: {content['metadata'].get('teacher_name', 'N/A')}")
            print(f"   Grade: {content['metadata'].get('grade', 'N/A')}")
            print(f"   Week: {content['metadata'].get('week', 'N/A')}")
            print(f"   Table size: {content['metadata'].get('rows', 0)} rows x {content['metadata'].get('columns', 0)} cols")
            print()
            
            # Show sample content
            print(f"   Sample content (first 200 chars):")
            print(f"   {content['full_text'][:200]}...")
            print()
            
            # Show days found
            if content['table_content']:
                days = list(content['table_content'].keys())
                print(f"   Days found: {', '.join(days)}")
                
                # Show components for first day
                if days:
                    first_day = days[0]
                    components = list(content['table_content'][first_day].keys())
                    print(f"   Components ({first_day}): {', '.join(components[:5])}...")
            
        else:
            print(f"❌ {subject} Not Found")
            if content.get('warnings'):
                for warning in content['warnings']:
                    print(f"   - {warning}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
