"""
Diagnostic logger for hyperlink cross-contamination debugging.

Records detailed JSON snapshots and logs at each stage of processing
to enable post-mortem analysis if issues persist.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DiagnosticLogger:
    """Records diagnostic information for hyperlink processing."""
    
    def __init__(self, output_dir: str = "logs/diagnostics"):
        """Initialize diagnostic logger.
        
        Args:
            output_dir: Directory to store diagnostic files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        self.session_log = []
        
        # Track stage counters to avoid overwriting
        self.stage_counters = {}
        
        logger.info(f"Diagnostic session started: {self.session_dir}")
    
    def log_stage(self, stage: str, data: Dict[str, Any]):
        """Log a processing stage with associated data.
        
        Args:
            stage: Stage name (e.g., "parser_extract", "batch_combine")
            data: Data to log
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "data": data
        }
        self.session_log.append(entry)
        
        # Increment counter for this stage to avoid overwriting
        if stage not in self.stage_counters:
            self.stage_counters[stage] = 0
        self.stage_counters[stage] += 1
        
        # Write to individual stage file with counter
        stage_file = self.session_dir / f"{stage}_{self.stage_counters[stage]:03d}.json"
        with open(stage_file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
    
    def log_hyperlinks_extracted(self, slot_number: int, subject: str, 
                                  hyperlinks: List[Dict], source_file: str):
        """Log hyperlinks extracted from parser.
        
        Args:
            slot_number: Slot number
            subject: Subject name
            hyperlinks: List of extracted hyperlinks
            source_file: Source DOCX file path
        """
        self.log_stage(f"01_parser_slot{slot_number}", {
            "slot_number": slot_number,
            "subject": subject,
            "source_file": source_file,
            "hyperlink_count": len(hyperlinks),
            "hyperlinks": [
                {
                    "text": h.get("text", "")[:100],
                    "url": h.get("url", "")[:100],
                    "has_source_slot": "_source_slot" in h,
                    "has_source_subject": "_source_subject" in h,
                    "source_slot": h.get("_source_slot"),
                    "source_subject": h.get("_source_subject")
                }
                for h in hyperlinks[:20]  # First 20 for brevity
            ]
        })
    
    def log_lesson_json_created(self, slot_number: int, subject: str, 
                                 lesson_json: Dict):
        """Log lesson JSON after LLM transformation.
        
        Args:
            slot_number: Slot number
            subject: Subject name
            lesson_json: Complete lesson JSON
        """
        hyperlinks = lesson_json.get("_hyperlinks", [])
        metadata = lesson_json.get("metadata", {})
        
        self.log_stage(f"02_lesson_json_slot{slot_number}", {
            "slot_number": slot_number,
            "subject": subject,
            "metadata_slot_number": metadata.get("slot_number"),
            "metadata_subject": metadata.get("subject"),
            "hyperlink_count": len(hyperlinks),
            "hyperlinks_with_slot_metadata": sum(
                1 for h in hyperlinks if "_source_slot" in h
            ),
            "hyperlinks_with_subject_metadata": sum(
                1 for h in hyperlinks if "_source_subject" in h
            ),
            "sample_hyperlinks": [
                {
                    "text": h.get("text", "")[:50],
                    "has_source_slot": "_source_slot" in h,
                    "source_slot": h.get("_source_slot"),
                    "has_source_subject": "_source_subject" in h,
                    "source_subject": h.get("_source_subject")
                }
                for h in hyperlinks[:10]
            ]
        })
    
    def log_before_render(self, slot_number: int, subject: str, 
                          lesson_json: Dict, render_type: str):
        """Log lesson JSON just before rendering.
        
        Args:
            slot_number: Slot number
            subject: Subject name
            lesson_json: Lesson JSON being rendered
            render_type: "single_slot" or "multi_slot"
        """
        hyperlinks = lesson_json.get("_hyperlinks", [])
        metadata = lesson_json.get("metadata", {})
        
        self.log_stage(f"03_before_render_slot{slot_number}", {
            "slot_number": slot_number,
            "subject": subject,
            "render_type": render_type,
            "metadata_slot_number": metadata.get("slot_number"),
            "metadata_subject": metadata.get("subject"),
            "hyperlink_count": len(hyperlinks),
            "all_hyperlinks_have_slot": all(
                "_source_slot" in h for h in hyperlinks
            ),
            "all_hyperlinks_have_subject": all(
                "_source_subject" in h for h in hyperlinks
            ),
            "hyperlink_slot_distribution": self._count_by_slot(hyperlinks),
            "sample_hyperlinks": [
                {
                    "text": h.get("text", "")[:50],
                    "source_slot": h.get("_source_slot"),
                    "source_subject": h.get("_source_subject")
                }
                for h in hyperlinks[:15]
            ]
        })
    
    def log_renderer_extracted_metadata(self, slot_number: Any, subject: Any,
                                         hyperlink_count: int, teacher: str):
        """Log metadata extracted by renderer.
        
        Args:
            slot_number: Extracted slot number (may be None)
            subject: Extracted subject (may be None)
            hyperlink_count: Number of hyperlinks
            teacher: Teacher name
        """
        self.log_stage("04_renderer_metadata_extracted", {
            "slot_number": slot_number,
            "slot_number_type": type(slot_number).__name__,
            "slot_number_is_none": slot_number is None,
            "subject": subject,
            "subject_is_none": subject is None,
            "hyperlink_count": hyperlink_count,
            "teacher": teacher,
            "filtering_will_activate": slot_number is not None
        })
    
    def log_filtering_context(self, current_slot_number: Any, 
                               current_subject: Any,
                               pending_count: int, cell: str):
        """Log filtering context in _fill_cell.
        
        Args:
            current_slot_number: Current slot number for filtering
            current_subject: Current subject for filtering
            pending_count: Number of pending hyperlinks
            cell: Cell identifier
        """
        self.log_stage("05_filtering_context", {
            "current_slot_number": current_slot_number,
            "current_slot_number_is_none": current_slot_number is None,
            "current_subject": current_subject,
            "current_subject_is_none": current_subject is None,
            "pending_hyperlinks_count": pending_count,
            "cell": cell,
            "filtering_active": current_slot_number is not None
        })
    
    def log_hyperlink_filtered(self, hyperlink_text: str, link_slot: int,
                                current_slot: int, reason: str):
        """Log a hyperlink being filtered out.
        
        Args:
            hyperlink_text: Hyperlink text
            link_slot: Hyperlink's source slot
            current_slot: Current rendering slot
            reason: Reason for filtering
        """
        self.log_stage("06_hyperlink_filtered", {
            "text": hyperlink_text[:50],
            "link_slot": link_slot,
            "current_slot": current_slot,
            "reason": reason
        })
    
    def log_hyperlink_placed(self, hyperlink_text: str, slot: int,
                              subject: str, cell: str, confidence: float):
        """Log a hyperlink being placed inline.
        
        Args:
            hyperlink_text: Hyperlink text
            slot: Slot number
            subject: Subject
            cell: Cell identifier
            confidence: Match confidence
        """
        self.log_stage("07_hyperlink_placed", {
            "text": hyperlink_text[:50],
            "slot": slot,
            "subject": subject,
            "cell": cell,
            "confidence": confidence
        })
    
    def log_unmatched_hyperlinks(self, hyperlinks: List[Dict]):
        """Log hyperlinks that fell back to Referenced Links section.
        
        Args:
            hyperlinks: List of unmatched hyperlinks
        """
        self.log_stage("08_unmatched_hyperlinks", {
            "count": len(hyperlinks),
            "hyperlinks": [
                {
                    "text": h.get("text", "")[:50],
                    "source_slot": h.get("_source_slot"),
                    "source_subject": h.get("_source_subject"),
                    "has_slot_metadata": "_source_slot" in h,
                    "has_subject_metadata": "_source_subject" in h
                }
                for h in hyperlinks
            ]
        })
    
    def _count_by_slot(self, hyperlinks: List[Dict]) -> Dict[str, int]:
        """Count hyperlinks by source slot.
        
        Args:
            hyperlinks: List of hyperlinks
            
        Returns:
            Dictionary mapping slot number to count
        """
        counts = {}
        for h in hyperlinks:
            slot = h.get("_source_slot", "no_metadata")
            counts[str(slot)] = counts.get(str(slot), 0) + 1
        return counts
    
    def finalize(self):
        """Write final session log."""
        session_file = self.session_dir / "session_log.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_log, f, indent=2, ensure_ascii=False)
        
        # Create summary
        summary = {
            "session_dir": str(self.session_dir),
            "total_stages": len(self.session_log),
            "stages": [entry["stage"] for entry in self.session_log]
        }
        
        summary_file = self.session_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Diagnostic session finalized: {self.session_dir}")
        print(f"\n📊 Diagnostic logs saved to: {self.session_dir}")
        print(f"   - Session log: session_log.json")
        print(f"   - Summary: summary.json")
        print(f"   - Individual stages: 01_parser_slot*.json, etc.")


# Global instance
_diagnostic_logger = None


def get_diagnostic_logger() -> DiagnosticLogger:
    """Get or create global diagnostic logger instance."""
    global _diagnostic_logger
    if _diagnostic_logger is None:
        _diagnostic_logger = DiagnosticLogger()
    return _diagnostic_logger


def finalize_diagnostics():
    """Finalize and save diagnostic logs, then reset for next run."""
    global _diagnostic_logger
    if _diagnostic_logger is not None:
        try:
            _diagnostic_logger.finalize()
        except Exception as e:
            logger.error(f"Error finalizing diagnostics: {e}")
        finally:
            # Always reset to None so next run gets fresh logger
            _diagnostic_logger = None
