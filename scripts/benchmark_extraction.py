
import asyncio
import sys
import os
from pathlib import Path

# Add root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService
from backend.database import get_db

async def benchmark_extraction():
    db = get_db()
    processor = BatchProcessor(LLMService())
    processor.db = db
    
    test_files = [
        ("Template", "d:/LP/input/Lesson Plan Template SY'25-26.docx"),
        ("Davies (Variation)", "d:/LP/input/9_15-9_19 Davies Lesson Plans.docx"),
        ("Savoca (Multi-Subject)", "d:/LP/input/Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx"),
        ("Lang (Real usage)", "d:/LP/input/Lang Lesson Plans 9_15_25-9_19_25.docx")
    ]
    
    results = {}
    
    for label, path in test_files:
        print(f"\nBenchmarking {label}...")
        try:
            from tools.docx_parser import DOCXParser
            parser = DOCXParser(path)
            
            # Test a few slots to see what labels are captured
            # Subject: ELA usually exists
            content = await asyncio.to_thread(parser.extract_subject_content_for_slot, 1, "ELA")
            
            if "table_content" in content:
                monday = content["table_content"].get("Monday", {})
                labels = set(monday.keys())
                
                required = {"Objective:", "Anticipatory Set:", "Tailored Instruction:", "Assessment:", "Homework:", "Unit, Lesson #, Module:"}
                # Check for Misconception (singular or plural)
                misconception_found = "Misconception:" in labels or "Misconceptions:" in labels
                
                captured = required.intersection(labels)
                missing = required - labels
                
                print(f"  - Labels Captured: {len(captured)}/6")
                print(f"  - Misconception Found: {misconception_found}")
                if missing:
                     print(f"  - MISSING: {missing}")
                
                # Test the mapping logic
                mapped = processor._map_day_content_to_schema(monday, {"slot_number": 1})
                print(f"  - Schema Mapping Success: {bool(mapped)}")
                if mapped:
                    print(f"    - Mapped Keys: {list(mapped.keys())}")
            else:
                print("  - FAILED: No table content found.")
                
        except Exception as e:
            print(f"  - ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(benchmark_extraction())
