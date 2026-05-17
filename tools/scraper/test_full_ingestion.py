import sqlite3
import json
import os
from table_extractor import RecursiveTableParser

def test_ingestion():
    db_path = r"d:\LP\data\curriculum.db"
    docx_path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Copy of Unit_2__Area_and_Multiplication.docx"
    unit_id = "Math_3_U2_1hBoK4uk" # Official Unit ID
    
    parser = RecursiveTableParser()
    
    print(f"Starting ingestion for {docx_path}...")
    count = parser.ingest_to_curriculum(docx_path, unit_id, subject="Math")
    print(f"Ingested {count} lessons.")

    assert count >= 1, "Expected at least one lesson ingested"

    # Verify Data
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 1. Check Lessons
    print("\n--- Lessons Check ---")
    lessons = conn.execute(
        "SELECT id, title, lesson_number, length(procedure_html) as pcount, "
        "length(narrative_html) as ncount, length(learning_intentions) as lcount "
        "FROM lessons WHERE unit_id = ? ORDER BY lesson_number",
        (unit_id,),
    ).fetchall()
    for l in lessons:
        print(
            f"Lesson {l['lesson_number']}: {l['title']} "
            f"(procedure {l['pcount']} chars, narrative {l['ncount']}, objectives {l['lcount']})"
        )

    assert lessons, "No lessons found for unit"
    any_content = any(
        (l["pcount"] or 0) > 0
        or (l["ncount"] or 0) > 0
        or (l["lcount"] or 0) > 0
        for l in lessons
    )
    assert any_content, "Expected at least one lesson with procedure, narrative, or learning_intentions content"
        
    # 2. Check Resources
    print("\n--- Resources (Links) Check ---")
    resources = conn.execute("""
        SELECT r.id, r.original_url, r.resource_type, json_extract(r.metadata, '$.text') as link_text, lr.lesson_id
        FROM resources r
        JOIN lesson_resources lr ON r.id = lr.resource_id
        JOIN lessons l ON lr.lesson_id = l.id
        WHERE l.unit_id = ?
    """, (unit_id,)).fetchall()
    
    print(f"Found {len(resources)} resources linked to lessons.")
    for r in resources[:10]:
        print(f"[{r['lesson_id']}] {r['link_text']}: {r['original_url']}")

    conn.close()

if __name__ == "__main__":
    test_ingestion()
