"""Check if files are valid DOCX (ZIP) files."""
from pathlib import Path
import zipfile

folder = Path(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43')
input_files = [f for f in folder.glob('*.docx') if not f.name.startswith('Daniela_Silva_Weekly')]

print("=" * 80)
print("FILE FORMAT CHECK")
print("=" * 80)

for file in sorted(input_files):
    print(f"\n📄 {file.name}")
    
    # Check if it's a valid ZIP (DOCX is ZIP-based)
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            files_in_zip = zip_ref.namelist()
            has_document_xml = 'word/document.xml' in files_in_zip
            print(f"   ✅ Valid ZIP file")
            print(f"   ✅ Has word/document.xml: {has_document_xml}")
            print(f"   Files in archive: {len(files_in_zip)}")
    except zipfile.BadZipFile:
        print(f"   ❌ NOT a valid ZIP file (corrupted or wrong format)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
