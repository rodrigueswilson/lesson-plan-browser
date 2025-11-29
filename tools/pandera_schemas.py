"""
Using Pandera for schema validation of slot data.
Lightweight alternative to Great Expectations.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

# Would need: pip install pandera
import pandera as pa
from pandera.typing import Series, DataFrame


class SlotSchema(pa.DataFrameModel):
    """Schema for slot configuration data."""
    
    slot_number: Series[int] = pa.Field(ge=1, le=10, coerce=True)
    subject: Series[str] = pa.Field(
        nullable=False,
        isin=["ELA", "Math", "Science", "Social Studies", "ELA/SS", "ELA/Math"]
    )
    grade: Series[str] = pa.Field(
        nullable=False,
        isin=["K", "1", "2", "3", "4", "5"]
    )
    homeroom: Series[str] = pa.Field(nullable=True)
    primary_teacher_name: Series[str] = pa.Field(nullable=False)
    primary_teacher_first_name: Series[str] = pa.Field(nullable=True)
    primary_teacher_last_name: Series[str] = pa.Field(nullable=True)
    
    class Config:
        strict = True
        coerce = True


class ProcessedSlotSchema(pa.DataFrameModel):
    """Schema for processed slot content."""
    
    slot_number: Series[int] = pa.Field(ge=1, le=10)
    subject: Series[str] = pa.Field(nullable=False)
    has_content: Series[bool] = pa.Field()
    word_count: Series[int] = pa.Field(ge=0)
    bilingual_sections: Series[int] = pa.Field(ge=0)
    
    class Config:
        strict = False


class SlotValidator:
    """Validates slot data using Pandera schemas."""
    
    @staticmethod
    def validate_slot_config(slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate slot configuration data."""
        try:
            df = pd.DataFrame(slots)
            validated_df = SlotSchema.validate(df)
            
            return {
                "success": True,
                "validated_count": len(validated_df),
                "validated_slots": validated_df.to_dict("records")
            }
        except pa.errors.SchemaErrors as e:
            return {
                "success": False,
                "errors": e.failure_cases.to_dict("records"),
                "error_count": len(e.failure_cases)
            }
    
    @staticmethod
    def validate_processed_content(processed_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate processed slot content."""
        
        # Transform to validation format
        validation_data = []
        for slot in processed_slots:
            content = slot.get("transformed_content", {}).get("days", {})
            
            # Count content across all days
            total_word_count = 0
            has_content = False
            bilingual_sections = 0
            
            for day_content in content.values():
                if isinstance(day_content, dict):
                    for section, text in day_content.items():
                        if text and isinstance(text, str):
                            total_word_count += len(text.split())
                            has_content = True
                            # Check if content appears bilingual (contains common Portuguese words)
                            if any(word in text.lower() for word in ['o', 'a', 'os', 'as', 'de', 'da', 'do']):
                                bilingual_sections += 1
            
            validation_data.append({
                "slot_number": slot.get("slot_metadata", {}).get("slot_number", 0),
                "subject": slot.get("slot_metadata", {}).get("subject", ""),
                "has_content": has_content,
                "word_count": total_word_count,
                "bilingual_sections": bilingual_sections
            })
        
        try:
            df = pd.DataFrame(validation_data)
            validated_df = ProcessedSlotSchema.validate(df)
            
            # Additional quality checks
            quality_issues = []
            
            # Check for empty slots
            empty_slots = validated_df[~validated_df["has_content"]]
            if not empty_slots.empty:
                quality_issues.append(f"Slots with no content: {empty_slots['slot_number'].tolist()}")
            
            # Check for low word count (possible processing errors)
            low_word_slots = validated_df[validated_df["word_count"] < 10]
            if not low_word_slots.empty:
                quality_issues.append(f"Slots with suspiciously low word count: {low_word_slots['slot_number'].tolist()}")
            
            # Check bilingual content
            non_bilingual = validated_df[validated_df["bilingual_sections"] == 0]
            if not non_bilingual.empty:
                quality_issues.append(f"Slots with no apparent bilingual content: {non_bilingual['slot_number'].tolist()}")
            
            return {
                "success": True,
                "validated_count": len(validated_df),
                "quality_issues": quality_issues,
                "statistics": {
                    "total_word_count": validated_df["word_count"].sum(),
                    "avg_word_count": validated_df["word_count"].mean(),
                    "slots_with_content": validated_df["has_content"].sum(),
                    "slots_bilingual": (validated_df["bilingual_sections"] > 0).sum()
                }
            }
            
        except pa.errors.SchemaErrors as e:
            return {
                "success": False,
                "errors": e.failure_cases.to_dict("records"),
                "error_count": len(e.failure_cases)
            }


# Example usage in BatchProcessor:
class EnhancedBatchProcessor(BatchProcessor):
    """Enhanced BatchProcessor with validation."""
    
    def __init__(self, llm_service):
        super().__init__(llm_service)
        self.validator = SlotValidator()
    
    async def process_user_week(self, user_id: str, week_of: str, **kwargs) -> Dict[str, Any]:
        """Process with validation."""
        
        # Get slots
        slots = self.db.get_user_slots(user_id)
        
        # Validate input
        validation_result = self.validator.validate_slot_config(slots)
        if not validation_result["success"]:
            return {
                "success": False,
                "error": f"Slot validation failed: {validation_result['errors']}",
                "validation_details": validation_result
            }
        
        # Process normally
        result = await super().process_user_week(user_id, week_of, **kwargs)
        
        # Validate output if successful
        if result.get("success") and result.get("processed_slots"):
            # This would need access to processed slot data
            # For demonstration, assume we have it
            pass
        
        return result
