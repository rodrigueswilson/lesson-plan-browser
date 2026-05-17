import lancedb
import json
import os

def test_search(query_text: str):
    db_path = "d:\\LP\\data\\lance_db"
    db = lancedb.connect(db_path)
    table = db.open_table("curriculum_fragments")
    
    # Simple keyword/vector search (LanceDB handles the embedding if configured, 
    # but here we just added content. For now we use full text search if enabled, 
    # or just filter. Since we haven't configured an embedding function in the table, 
    # let's just do a simple search or check the data.)
    
    print(f"Searching for: {query_text}")
    results = table.to_pandas()
    matches = results[results['content'].str.contains(query_text, case=False)]
    
    print(f"Found {len(matches)} matches:")
    for _, row in matches.head(5).iterrows():
        print(f"--- {row['type']} ({row['lesson_id']}) ---")
        print(row['content'][:200] + "...")
        print()

if __name__ == "__main__":
    test_search("multiplication")
    print("="*50)
    test_search("motion")
