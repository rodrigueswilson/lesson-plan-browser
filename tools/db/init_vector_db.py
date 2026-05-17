import os
import lancedb
import pyarrow as pa

def init_db(db_path: str):
    db = lancedb.connect(db_path)
    
    # Define schema for curriculum fragments
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("unit_id", pa.string()),
        pa.field("lesson_id", pa.string(), nullable=True),
        pa.field("content", pa.string()),
        pa.field("type", pa.string()), # narrative, procedure, objective, etc.
        pa.field("metadata", pa.string()) # JSON string for flexibility
    ])
    
    if "curriculum_fragments" not in db.table_names():
        db.create_table("curriculum_fragments", schema=schema)
        print("Created table: curriculum_fragments")
    else:
        print("Table 'curriculum_fragments' already exists")

if __name__ == "__main__":
    db_dir = os.path.join("d:\\LP", "data", "lance_db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    init_db(db_dir)
