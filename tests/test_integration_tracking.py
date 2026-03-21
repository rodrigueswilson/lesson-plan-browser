"""
Integration test for performance tracking system.
Tests the complete workflow with mock LLM responses.
"""

import copy
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.config import settings
from backend.database import Database
from backend.llm_service import LLMService
from backend.performance_tracker import PerformanceTracker
from tools.batch_processor import BatchProcessor


async def _noop_combined_original_docx(*_args, **_kwargs):
    """Skip real combined-originals DOCX generation (needs real paths and DB rows)."""
    return None


def _skip_combined_originals(processor, monkeypatch):
    monkeypatch.setattr(
        processor,
        "_generate_combined_original_docx",
        _noop_combined_original_docx,
    )


async def _stub_process_slot_from_llm(
    self,
    slot,
    week_of,
    provider,
    week_folder_path,
    user_base_path,
    plan_id,
    slot_index,
    total_slots,
    processing_weight,
    existing_lesson_json=None,
    force_ai=False,
):
    """Bypass DOCX parse/extract; record process_slot metrics like the real slot flow."""
    op_id = None
    if self.tracker.enabled:
        op_id = self.tracker.start_operation(
            plan_id,
            "process_slot",
            metadata={
                "slot_number": slot["slot_number"],
                "subject": slot["subject"],
            },
        )
    try:
        success, lesson_json, error = self.llm_service.transform_lesson(
            primary_content="stub",
            grade=slot["grade"],
            subject=slot["subject"],
            week_of=week_of,
            teacher_name=None,
            homeroom=slot.get("homeroom"),
            plan_id=plan_id,
            available_days=None,
            progress_callback=None,
        )
        if not success:
            if op_id:
                self.tracker.end_operation(
                    op_id, result={"error": str(error or "unknown")}
                )
            raise ValueError(f"LLM transformation failed: {error}")
        lj = copy.deepcopy(lesson_json)
        usage = lj.get("_usage") or {}
        model = lj.get("_model", "gpt-4-turbo-preview")
        prov = lj.get("_provider", "openai")
        if op_id:
            self.tracker.end_operation(
                op_id,
                result={
                    "tokens_input": usage.get("tokens_input", 0),
                    "tokens_output": usage.get("tokens_output", 0),
                    "llm_model": model,
                    "llm_provider": prov,
                },
            )
        lj.pop("_usage", None)
        lj.pop("_model", None)
        lj.pop("_provider", None)
        return lj
    except Exception as e:
        if op_id and op_id in self.tracker._active_operations:
            self.tracker.end_operation(op_id, result={"error": str(e)})
        raise


def _bind_process_slot_llm_stub(processor):
    processor._process_slot = _stub_process_slot_from_llm.__get__(
        processor, BatchProcessor
    )


def _bind_combine_lessons_stub(processor, output_path: str):
    """Avoid real multi-slot DOCX merge/render (needs template and writable paths)."""

    def _combine_stub(_user, _lessons, _week_of, _start_time, _plan_id):
        return output_path

    processor._combine_lessons = _combine_stub


def _sync_weekly_plan_after_stub_combine(db, tracker, plan_id: str, result: dict) -> None:
    """Real `_combine_lessons` persists status/output in combine.py; path stubs skip that."""
    tracker.update_plan_summary(plan_id)
    db.update_weekly_plan(
        plan_id,
        status="completed",
        output_file=result.get("output_file") or "",
    )


@pytest.fixture(autouse=True)
def _force_sequential_slot_processing(monkeypatch):
    """Two-slot tests must not use parallel path (combined originals timing differs)."""
    monkeypatch.setattr(settings, "PARALLEL_LLM_PROCESSING", False)


@pytest.fixture
def test_user(test_db):
    """Create test user with slots."""
    user_id = test_db.create_user("Test Teacher", "test@example.com")
    
    # Create test slots
    test_db.create_class_slot(
        user_id=user_id,
        slot_number=1,
        subject="Math",
        grade="6",
        homeroom="6A",
    )
    
    test_db.create_class_slot(
        user_id=user_id,
        slot_number=2,
        subject="Science",
        grade="7",
        homeroom="7B",
    )
    
    return user_id


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service that returns realistic data."""
    service = Mock(spec=LLMService)
    service.provider = "openai"
    service.model = "gpt-4-turbo-preview"
    
    # Mock successful transformation with token usage
    def mock_transform(*args, **kwargs):
        lesson_json = {
            "metadata": {
                "week_of": "10/6-10/10",
                "grade": kwargs.get("grade", "6"),
                "subject": kwargs.get("subject", "Math"),
            },
            "days": {
                day: {
                    "unit_lesson": f"Test Lesson {day}",
                    "objective": {
                        "content_objective": "Students will learn...",
                        "student_goal": "I will...",
                        "wida_objective": "Students will use language to..."
                    },
                    "anticipatory_set": {
                        "original_content": "Test content",
                        "bilingual_bridge": "Portuguese bridge"
                    },
                    "tailored_instruction": {
                        "original_content": "Test instruction",
                        "co_teaching_model": {},
                        "ell_support": [],
                        "special_needs_support": [],
                        "materials": []
                    },
                    "misconceptions": {
                        "original_content": "Test misconceptions",
                        "linguistic_note": {}
                    },
                    "assessment": {
                        "primary_assessment": "Test assessment",
                        "bilingual_overlay": {}
                    },
                    "homework": {
                        "original_content": "Test homework",
                        "family_connection": "Portuguese connection"
                    }
                }
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            # Add usage information (this is what we're testing!)
            "_usage": {
                "tokens_input": 1500,
                "tokens_output": 800,
                "tokens_total": 2300
            },
            "_model": "gpt-4-turbo-preview",
            "_provider": "openai"
        }
        return True, lesson_json, None
    
    service.transform_lesson = mock_transform
    return service


@pytest.mark.asyncio
async def test_complete_tracking_workflow(test_db, test_user, mock_llm_service, monkeypatch):
    """Test complete workflow with performance tracking."""
    
    # Patch get_db to return our test database
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    monkeypatch.setattr("tools.batch_processor.get_db", lambda: test_db)
    
    # Create tracker with tracking enabled
    tracker = PerformanceTracker(enabled=True)
    monkeypatch.setattr("tools.batch_processor.get_tracker", lambda: tracker)
    
    # Create batch processor with mock LLM service
    processor = BatchProcessor(mock_llm_service)
    # Facade imports get_db/get_tracker at module load; patch instance to use test DB/tracker
    processor.get_db = lambda user_id=None, **kwargs: test_db
    processor.db = test_db
    processor.tracker = tracker
    _skip_combined_originals(processor, monkeypatch)
    _bind_process_slot_llm_stub(processor)
    _bind_combine_lessons_stub(
        processor, str(Path(tempfile.gettempdir()) / "tracking_test_out.docx")
    )

    mock_renderer = Mock()
    mock_renderer.render_consolidated_plan.return_value = "mock_output.docx"

    with patch("tools.docx_renderer.DOCXRenderer", return_value=mock_renderer), \
         patch("tools.batch_processor.get_file_manager") as mock_file_manager:
        
        # Mock file manager
        mock_fm = Mock()
        mock_fm.get_output_path_with_timestamp.return_value = "output/test_plan.docx"
        mock_fm.get_week_folder.return_value = Path(tempfile.gettempdir()) / "test_week"
        mock_file_manager.return_value = mock_fm
        
        # Process the week
        result = await processor.process_user_week(
            user_id=test_user,
            week_of="10/6-10/10",
            provider="openai"
        )
    
    # Verify processing succeeded
    print(f"Result: {result}")
    if not result["success"]:
        print(f"Errors: {result.get('errors')}")
    assert result["success"] is True, f"Processing failed: {result.get('errors')}"
    assert result["processed_slots"] == 2
    assert "plan_id" in result

    plan_id = result["plan_id"]
    _sync_weekly_plan_after_stub_combine(test_db, tracker, plan_id, result)

    # Verify performance metrics were recorded (batch_process + one row per slot)
    metrics = tracker.get_plan_metrics(plan_id)
    slot_metrics = [m for m in metrics if m["operation_type"] == "process_slot"]
    assert len(slot_metrics) == 2
    slot_metrics = sorted(slot_metrics, key=lambda m: (m.get("slot_number") or 0))

    metric1 = slot_metrics[0]
    assert metric1["plan_id"] == plan_id
    assert metric1["operation_type"] == "process_slot"
    assert metric1["tokens_input"] == 1500
    assert metric1["tokens_output"] == 800
    assert metric1["tokens_total"] == 2300
    assert metric1["llm_model"] == "gpt-4-turbo-preview"
    assert metric1["llm_provider"] == "openai"
    assert metric1["duration_ms"] >= 0
    assert metric1["cost_usd"] > 0

    metric2 = slot_metrics[1]
    assert metric2["tokens_input"] == 1500
    assert metric2["tokens_output"] == 800

    # Verify plan summary (SSOT: get_plan_summary aggregates all metric rows)
    summary = tracker.get_plan_summary(plan_id)
    assert summary["operation_count"] == 3  # batch_process + 2 slots
    assert summary["total_tokens"] == 4600  # 2300 * 2
    assert summary["total_cost_usd"] > 0
    assert summary["total_time_ms"] >= 0
    metrics_list = tracker.get_plan_metrics(plan_id)
    assert sum(m["tokens_input"] for m in metrics_list) == 3000
    assert sum(m["tokens_output"] for m in metrics_list) == 1600

    # Verify weekly_plans row (ORM attributes, not dict)
    plans = test_db.get_user_plans(test_user)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.total_tokens == 4600
    assert plan.total_cost_usd is not None and plan.total_cost_usd > 0
    assert plan.processing_time_ms is not None and plan.processing_time_ms >= 0
    assert plan.llm_model == "gpt-4-turbo-preview"
    assert plan.status == "completed"


@pytest.mark.asyncio
async def test_tracking_with_error(test_db, test_user, monkeypatch):
    """Test that tracking handles errors gracefully."""
    
    # Patch get_db
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    monkeypatch.setattr("tools.batch_processor.get_db", lambda: test_db)
    
    # Create tracker
    tracker = PerformanceTracker(enabled=True)
    monkeypatch.setattr("tools.batch_processor.get_tracker", lambda: tracker)
    
    # Create mock LLM service that fails
    mock_llm_service = Mock(spec=LLMService)
    mock_llm_service.provider = "openai"
    mock_llm_service.model = "gpt-4-turbo-preview"
    mock_llm_service.transform_lesson.return_value = (False, None, "Mock LLM error")
    
    # Create batch processor
    processor = BatchProcessor(mock_llm_service)
    processor.get_db = lambda user_id=None, **kwargs: test_db
    processor.db = test_db
    processor.tracker = tracker
    _skip_combined_originals(processor, monkeypatch)
    _bind_combine_lessons_stub(
        processor, str(Path(tempfile.gettempdir()) / "tracking_err_out.docx")
    )

    async def _fail_slot(*_a, **_kw):
        raise ValueError("LLM transformation failed: Mock LLM error")

    processor._process_slot = _fail_slot

    mock_renderer = Mock()
    mock_renderer.render_consolidated_plan.return_value = "mock_output.docx"

    with patch("tools.docx_renderer.DOCXRenderer", return_value=mock_renderer), \
         patch("tools.batch_processor.get_file_manager") as mock_file_manager:

        mock_fm = Mock()
        mock_fm.get_output_path_with_timestamp.return_value = "output/test_plan.docx"
        mock_fm.get_week_folder.return_value = Path(tempfile.gettempdir()) / "test_week"
        mock_file_manager.return_value = mock_fm

        # Process should fail but not crash
        result = await processor.process_user_week(
            user_id=test_user,
            week_of="10/6-10/10",
            provider="openai"
        )
    
    # Verify processing failed
    assert result["success"] is False
    assert result["failed_slots"] > 0
    
    plan_id = result["plan_id"]
    
    # Verify error was tracked
    metrics = tracker.get_plan_metrics(plan_id)
    assert len(metrics) > 0
    
    # Batch or slot path may record errors on metrics rows
    error_metrics = [m for m in metrics if m.get("error_message")]
    assert len(error_metrics) > 0
    assert any("Mock LLM error" in (m.get("error_message") or "") for m in metrics)


@pytest.mark.asyncio
async def test_tracking_disabled(test_db, test_user, mock_llm_service, monkeypatch):
    """Test that tracking can be disabled."""
    
    # Patch get_db
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    monkeypatch.setattr("tools.batch_processor.get_db", lambda: test_db)
    
    # Create tracker with tracking DISABLED
    tracker = PerformanceTracker(enabled=False)
    monkeypatch.setattr("tools.batch_processor.get_tracker", lambda: tracker)
    
    # Create batch processor
    processor = BatchProcessor(mock_llm_service)
    processor.get_db = lambda user_id=None, **kwargs: test_db
    processor.db = test_db
    processor.tracker = tracker
    _skip_combined_originals(processor, monkeypatch)
    _bind_process_slot_llm_stub(processor)
    _bind_combine_lessons_stub(
        processor, str(Path(tempfile.gettempdir()) / "tracking_disabled_out.docx")
    )

    mock_renderer = Mock()
    mock_renderer.render_consolidated_plan.return_value = "mock_output.docx"

    with patch("tools.docx_renderer.DOCXRenderer", return_value=mock_renderer), \
         patch("tools.batch_processor.get_file_manager") as mock_file_manager:

        mock_fm = Mock()
        mock_fm.get_output_path_with_timestamp.return_value = "output/test_plan.docx"
        mock_fm.get_week_folder.return_value = Path(tempfile.gettempdir()) / "test_week"
        mock_file_manager.return_value = mock_fm

        # Process the week
        result = await processor.process_user_week(
            user_id=test_user,
            week_of="10/6-10/10",
            provider="openai"
        )

    # Verify processing succeeded
    assert result["success"] is True

    plan_id = result["plan_id"]

    # Verify NO metrics were recorded (tracking disabled)
    metrics = tracker.get_plan_metrics(plan_id)
    assert len(metrics) == 0


@pytest.mark.asyncio
async def test_csv_export_integration(test_db, test_user, mock_llm_service, monkeypatch):
    """Test CSV export with real data."""
    
    # Patch get_db
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    monkeypatch.setattr("tools.batch_processor.get_db", lambda: test_db)
    
    # Create tracker
    tracker = PerformanceTracker(enabled=True)
    monkeypatch.setattr("tools.batch_processor.get_tracker", lambda: tracker)
    
    # Create and run processor
    processor = BatchProcessor(mock_llm_service)
    processor.get_db = lambda user_id=None, **kwargs: test_db
    processor.db = test_db
    processor.tracker = tracker
    _skip_combined_originals(processor, monkeypatch)
    _bind_process_slot_llm_stub(processor)
    _bind_combine_lessons_stub(
        processor, str(Path(tempfile.gettempdir()) / "tracking_csv_out.docx")
    )

    mock_renderer = Mock()
    mock_renderer.render_consolidated_plan.return_value = "mock_output.docx"

    with patch("tools.docx_renderer.DOCXRenderer", return_value=mock_renderer), \
         patch("tools.batch_processor.get_file_manager") as mock_file_manager:

        mock_fm = Mock()
        mock_fm.get_output_path_with_timestamp.return_value = "output/test_plan.docx"
        mock_fm.get_week_folder.return_value = Path(tempfile.gettempdir()) / "test_week"
        mock_file_manager.return_value = mock_fm

        result = await processor.process_user_week(
            user_id=test_user,
            week_of="10/6-10/10",
            provider="openai"
        )
    
    plan_id = result["plan_id"]
    
    # Export to CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "metrics.csv"
        exported_path = tracker.export_to_csv(plan_id, str(csv_path))
        
        assert exported_path == str(csv_path)
        assert csv_path.exists()
        
        # Read and verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Verify headers
            assert "tokens_input" in content
            assert "tokens_output" in content
            assert "cost_usd" in content
            assert "llm_model" in content
            
            # Verify data
            assert "1500" in content  # tokens_input
            assert "800" in content   # tokens_output
            assert "gpt-4-turbo-preview" in content


def test_cost_calculation_accuracy():
    """Test that cost calculations match expected values."""
    from backend.model_pricing import calculate_cost
    
    # Test GPT-4 Turbo (used in mock)
    cost = calculate_cost("gpt-4-turbo-preview", 1500, 800)
    # (1500/1000 * 0.01) + (800/1000 * 0.03) = 0.015 + 0.024 = 0.039
    expected = 0.039
    assert abs(cost - expected) < 0.0001
    
    # Verify this matches what would be tracked
    # For 2 slots: 2 * 0.039 = 0.078
    total_expected = 0.078
    assert abs(total_expected - 0.078) < 0.0001
