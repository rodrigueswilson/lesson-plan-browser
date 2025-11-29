"""
Using Great Expectations for data quality validation.
Ensures consistency in slot data processing.
"""

from typing import Any, Dict, List
import pandas as pd

# Would need: pip install great-expectations
from great_expectations.core import ExpectationSuite, ExpectationConfiguration
from great_expectations.dataset import PandasDataset
from great_expectations.validator import Validator


class SlotDataValidator:
    """Validates slot data quality using Great Expectations."""
    
    def __init__(self):
        self.expectation_suite = ExpectationSuite(
            expectation_suite_name="slot_data_quality"
        )
        self._setup_expectations()
    
    def _setup_expectations(self):
        """Define data quality expectations."""
        
        # Slot metadata expectations
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_table_row_count_to_be_between",
                kwargs={"min_value": 1, "max_value": 10}
            )
        )
        
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "slot_number"}
            )
        )
        
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={"column": "slot_number", "min_value": 1, "max_value": 10}
            )
        )
        
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "subject"}
            )
        )
        
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_match_regex",
                kwargs={
                    "column": "subject",
                    "regex": r"^(ELA|Math|Science|Social Studies|ELA/SS|ELA/Math)$"
                }
            )
        )
        
        # Content completeness expectations
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "grade"}
            )
        )
        
        self.expectation_suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_set",
                kwargs={
                    "column": "grade",
                    "value_set": ["K", "1", "2", "3", "4", "5"]
                }
            )
        )
    
    def validate_slots(self, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a list of slots."""
        if not slots:
            return {"success": False, "error": "No slots to validate"}
        
        # Convert to DataFrame
        df = pd.DataFrame(slots)
        dataset = PandasDataset(df)
        
        # Run validation
        validator = Validator(
            dataset=dataset,
            expectation_suite=self.expectation_suite
        )
        
        results = validator.validate()
        
        return {
            "success": results.success,
            "statistics": results.get_statistics(),
            "results": results.results,
            "validation_log": results.validation_log
        }
    
    def validate_processed_content(self, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processed lesson plan content."""
        issues = []
        
        # Check metadata completeness
        metadata = processed_content.get("metadata", {})
        required_metadata = ["teacher_name", "grade", "subject", "week_of"]
        
        for field in required_metadata:
            if not metadata.get(field):
                issues.append(f"Missing required metadata: {field}")
        
        # Check daily structure
        days = processed_content.get("days", {})
        required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in required_days:
            if day not in days:
                issues.append(f"Missing day: {day}")
                continue
            
            day_content = days[day]
            
            # Check if it's multi-slot structure
            if "slots" in day_content:
                # Validate each slot
                for slot in day_content["slots"]:
                    if not slot.get("slot_number"):
                        issues.append(f"Missing slot number in {day}")
                    
                    # Check for at least some content
                    content_fields = [
                        "unit_lesson", "objective", "anticipatory_set",
                        "tailored_instruction", "assessment"
                    ]
                    
                    has_content = any(slot.get(field) for field in content_fields)
                    if not has_content:
                        issues.append(f"No content found for slot {slot.get('slot_number')} on {day}")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "validated_at": pd.Timestamp.now().isoformat()
        }


# Usage example:
def validate_batch_process(slots: List[Dict[str, Any]], result: Dict[str, Any]) -> bool:
    """Validate entire batch process."""
    validator = SlotDataValidator()
    
    # Validate input slots
    slot_validation = validator.validate_slots(slots)
    if not slot_validation["success"]:
        print(f"❌ Slot validation failed: {slot_validation['statistics']}")
        return False
    
    # Validate output content
    if result.get("success") and result.get("combined_plan"):
        content_validation = validator.validate_processed_content(result["combined_plan"])
        if not content_validation["success"]:
            print(f"❌ Content validation failed: {content_validation['issues']}")
            return False
    
    print("✅ All validations passed")
    return True
