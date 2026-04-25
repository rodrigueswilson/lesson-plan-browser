import zipfile
import os

path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Copy of Unit_2__Area_and_Multiplication.docx"

with zipfile.ZipFile(path) as docx:
    print(f"{'Filename':<50} | {'Size':>10}")
    print("-" * 65)
    for info in docx.infolist():
        print(f"{info.filename:<50} | {info.file_size:>10}")
