from table_extractor import RecursiveTableParser
import re

parser = RecursiveTableParser()
docx_path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Unit_2__Area_and_Multiplication.docx"
lesson_pattern = re.compile(
    r"(?:LESSON\s+(\d+)|(\d+\.\d+\.\d+)\s+Teacher Guide)\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)

print("Streaming...")
stream = list(parser.parse_to_stream(docx_path))
print(f"Total Stream Items: {len(stream)}")

found_l1 = False
for i, item in enumerate(stream):
    if item.get("type") != "paragraph":
        continue
    content = item.get("text", "")
    if lesson_pattern.search(content) and "1" in content:
        print(f"\n--- FOUND LESSON 1 at stream item {i} ---")
        print(f"Content: {content[:200]}")
        found_l1 = True
        for j in range(i + 1, min(i + 21, len(stream))):
            next_item = stream[j]
            preview = ""
            if next_item.get("type") == "paragraph":
                preview = (next_item.get("text") or "")[:150].strip()
            elif next_item.get("type") == "property":
                preview = (next_item.get("key") or "")[:80]
            print(f"Item {j} ({next_item.get('type')}): {preview}")
        break

if not found_l1:
    print("\nLesson 1 not found in stream.")
