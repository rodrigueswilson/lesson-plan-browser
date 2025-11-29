"""
Demo script to test performance tracking with mock data.
Run this to see the tracking system in action without real LLM calls.

Usage:
    python test_tracking_demo.py
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from backend.database import Database
from backend.llm_service import LLMService
from backend.performance_tracker import get_tracker
from tools.batch_processor import BatchProcessor


def create_mock_llm_service():
    """Create a mock LLM service that returns realistic data."""
    service = Mock(spec=LLMService)
    service.provider = "openai"
    service.model = "gpt-4-turbo-preview"
    
    def mock_transform(*args, **kwargs):
        """Simulate LLM transformation with token usage."""
        subject = kwargs.get("subject", "Math")
        grade = kwargs.get("grade", "6")
        
        lesson_json = {
            "metadata": {
                "week_of": kwargs.get("week_of", "10/6-10/10"),
                "grade": grade,
                "subject": subject,
            },
            "days": {
                day: {
                    "unit_lesson": f"{subject} - Unit 1 Lesson {i+1}",
                    "objective": {
                        "content_objective": f"Students will understand {subject.lower()} concepts",
                        "student_goal": f"I will learn {subject.lower()}",
                        "wida_objective": "Students will use language to explain mathematical concepts (ELD-MA.6-8.Explain.Speaking)"
                    },
                    "anticipatory_set": {
                        "original_content": f"Review {subject} concepts",
                        "bilingual_bridge": "Revisar conceitos (Portuguese bridge)"
                    },
                    "tailored_instruction": {
                        "original_content": f"Teach {subject} lesson",
                        "co_teaching_model": {
                            "model_name": "Station Teaching",
                            "rationale": "Allows for differentiated instruction"
                        },
                        "ell_support": [
                            {
                                "strategy_id": "visual_aids",
                                "strategy_name": "Visual Aids",
                                "implementation": "Use diagrams and charts"
                            }
                        ],
                        "special_needs_support": ["Extended time", "Simplified instructions"],
                        "materials": ["Textbook", "Worksheets", "Manipulatives"]
                    },
                    "misconceptions": {
                        "original_content": "Common errors",
                        "linguistic_note": {"pattern_id": "false_cognate", "note": "Watch for false cognates"}
                    },
                    "assessment": {
                        "primary_assessment": "Exit ticket",
                        "bilingual_overlay": {"instrument": "Oral assessment", "wida_mapping": "Speaking"}
                    },
                    "homework": {
                        "original_content": "Practice problems",
                        "family_connection": "Família pode ajudar (Family can help)"
                    }
                }
                for i, day in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday"])
            },
            # Add realistic token usage
            "_usage": {
                "tokens_input": 1200 + (hash(subject) % 500),  # Vary by subject
                "tokens_output": 700 + (hash(subject) % 300),
                "tokens_total": 1900 + (hash(subject) % 800)
            },
            "_model": "gpt-4-turbo-preview",
            "_provider": "openai"
        }
        return True, lesson_json, None
    
    service.transform_lesson = mock_transform
    return service


async def demo_tracking():
    """Run a demo of the performance tracking system."""
    print("=" * 70)
    print("Performance Tracking Demo - Mock Data Test")
    print("=" * 70)
    print()
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "demo.db"
        db = Database(str(db_path))
        
        print("✓ Database created")
        
        # Create test user
        user_id = db.create_user("Demo Teacher", "demo@example.com")
        print(f"✓ User created: {user_id[:8]}...")
        
        # Create test slots
        slots = [
            {"slot_number": 1, "subject": "Math", "grade": "6", "homeroom": "6A"},
            {"slot_number": 2, "subject": "Science", "grade": "7", "homeroom": "7B"},
            {"slot_number": 3, "subject": "English", "grade": "8", "homeroom": "8C"},
        ]
        
        for slot in slots:
            db.create_class_slot(user_id=user_id, **slot)
        
        print(f"✓ Created {len(slots)} class slots")
        print()
        
        # Patch get_db to use our test database
        with patch("backend.performance_tracker.get_db", return_value=db), \
             patch("tools.batch_processor.get_db", return_value=db):
            
            # Create mock LLM service
            mock_llm = create_mock_llm_service()
            
            # Create batch processor
            processor = BatchProcessor(mock_llm)
            
            # Mock file operations
            processor._resolve_primary_file = lambda *args, **kwargs: "mock_file.docx"
            
            mock_parser = Mock()
            mock_parser.is_no_school_day.return_value = False
            mock_parser.extract_subject_content.return_value = {
                "full_text": "Mock lesson content for testing"
            }
            
            mock_renderer = Mock()
            mock_renderer.render_consolidated_plan.return_value = "output/demo_plan.docx"
            
            with patch("tools.batch_processor.DOCXParser", return_value=mock_parser), \
                 patch("tools.batch_processor.DOCXRenderer", return_value=mock_renderer), \
                 patch("tools.batch_processor.get_file_manager") as mock_fm:
                
                mock_file_manager = Mock()
                mock_file_manager.get_output_path_with_timestamp.return_value = "output/demo_plan.docx"
                mock_file_manager.get_week_folder.return_value = Path(tmpdir) / "week"
                mock_fm.return_value = mock_file_manager
                
                print("Processing week with performance tracking...")
                print("-" * 70)
                
                # Process the week
                result = await processor.process_user_week(
                    user_id=user_id,
                    week_of="10/6-10/10",
                    provider="openai"
                )
            
            print()
            print("=" * 70)
            print("Processing Results")
            print("=" * 70)
            print(f"Success: {result['success']}")
            print(f"Processed Slots: {result['processed_slots']}")
            print(f"Total Time: {result['total_time_ms']:.2f}ms")
            print()
            
            if not result['success']:
                print(f"Errors: {result.get('errors')}")
                return
            
            plan_id = result['plan_id']
            
            # Get tracker and retrieve metrics
            tracker = get_tracker()
            metrics = tracker.get_plan_metrics(plan_id)
            
            print("=" * 70)
            print("Performance Metrics (Per Slot)")
            print("=" * 70)
            
            for i, metric in enumerate(metrics, 1):
                print(f"\nSlot {i}:")
                print(f"  Subject: {slots[i-1]['subject']}")
                print(f"  Duration: {metric['duration_ms']:.2f}ms")
                print(f"  Tokens Input: {metric['tokens_input']:,}")
                print(f"  Tokens Output: {metric['tokens_output']:,}")
                print(f"  Tokens Total: {metric['tokens_total']:,}")
                print(f"  Cost: ${metric['cost_usd']:.4f}")
                print(f"  Model: {metric['llm_model']}")
            
            # Get summary
            summary = tracker.get_plan_summary(plan_id)
            
            print()
            print("=" * 70)
            print("Summary Statistics")
            print("=" * 70)
            print(f"Total Operations: {summary['operation_count']}")
            print(f"Total Duration: {summary['total_duration_ms']:.2f}ms")
            print(f"Total Tokens: {summary['total_tokens']:,}")
            print(f"  - Input: {summary['total_tokens_input']:,}")
            print(f"  - Output: {summary['total_tokens_output']:,}")
            print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
            print(f"Average Duration: {summary['avg_duration_ms']:.2f}ms per operation")
            print()
            
            # Check weekly_plans table
            plans = db.get_user_plans(user_id)
            plan = plans[0]
            
            print("=" * 70)
            print("Database Record (weekly_plans table)")
            print("=" * 70)
            print(f"Plan ID: {plan['id'][:8]}...")
            print(f"Week: {plan['week_of']}")
            print(f"Status: {plan['status']}")
            print(f"Total Tokens: {plan['total_tokens']:,}")
            print(f"Total Cost: ${plan['total_cost_usd']:.4f}")
            print(f"Processing Time: {plan['processing_time_ms']:.2f}ms")
            print(f"Model: {plan['llm_model']}")
            print()
            
            # Export to CSV
            csv_path = Path(tmpdir) / "demo_metrics.csv"
            exported = tracker.export_to_csv(plan_id, str(csv_path))
            
            if exported:
                print("=" * 70)
                print("CSV Export")
                print("=" * 70)
                print(f"✓ Metrics exported to: {csv_path}")
                print(f"✓ File size: {csv_path.stat().st_size} bytes")
                
                # Show first few lines
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:4]  # Header + 3 rows
                    print("\nPreview (first 3 rows):")
                    print("-" * 70)
                    for line in lines:
                        # Truncate long lines
                        if len(line) > 70:
                            print(line[:67] + "...")
                        else:
                            print(line.rstrip())
            
            print()
            print("=" * 70)
            print("Demo Complete!")
            print("=" * 70)
            print()
            print("Key Features Demonstrated:")
            print("  ✓ Performance tracking for multiple slots")
            print("  ✓ Token usage capture from mock LLM")
            print("  ✓ Accurate cost calculations")
            print("  ✓ Database storage and retrieval")
            print("  ✓ Summary aggregation")
            print("  ✓ CSV export for analysis")
            print()
            print("All tracking data is stored in the database and can be")
            print("queried, exported, or visualized for research purposes.")
            print()


if __name__ == "__main__":
    print()
    print("Starting Performance Tracking Demo...")
    print()
    
    try:
        asyncio.run(demo_tracking())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
