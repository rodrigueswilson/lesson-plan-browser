"""
Mock LLM for testing without API calls.
Simulates various LLM response scenarios for testing retry logic and JSON repair.
"""

import json
from typing import Optional, List


class MockLLM:
    """Mock LLM that returns pre-configured responses."""
    
    def __init__(self, responses: Optional[List[str]] = None):
        """
        Initialize mock LLM with optional response sequence.
        
        Args:
            responses: List of responses to return in sequence.
                      If None, returns valid minimal JSON.
        """
        self.responses = responses or []
        self.call_count = 0
        self.prompts_received = []
    
    def generate(self, prompt: str) -> str:
        """
        Return pre-configured response based on call count.
        
        Args:
            prompt: The prompt sent to the LLM (stored for inspection)
            
        Returns:
            Pre-configured response or default valid JSON
        """
        self.prompts_received.append(prompt)
        
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        
        # Default: return valid minimal JSON
        self.call_count += 1
        return VALID_MINIMAL_JSON
    
    def reset(self):
        """Reset call counter and prompt history."""
        self.call_count = 0
        self.prompts_received = []
    
    def get_call_count(self) -> int:
        """Get number of times generate was called."""
        return self.call_count
    
    def get_last_prompt(self) -> Optional[str]:
        """Get the last prompt received."""
        return self.prompts_received[-1] if self.prompts_received else None


# Test Scenarios
# ==============

# Helper function to create a minimal day
def _create_minimal_day(unit_name="Unit One"):
    return {
        "unit_lesson": unit_name,
        "objective": {
            "content_objective": "Students will learn about the topic (minimum 30 characters required)",
            "student_goal": "I will explain the concepts using evidence and examples",
            "wida_objective": "Students will use language to explain concepts (ELD-SS.6-8.Explain.Reading/Writing) using appropriate scaffolds"
        },
        "anticipatory_set": {
            "original_content": "Review previous lesson and activate prior knowledge through discussion",
            "bilingual_bridge": "Preview key vocabulary in both languages and connect to prior learning"
        },
        "tailored_instruction": {
            "original_content": "Introduce main concepts through direct instruction and guided practice activities",
            "co_teaching_model": {
                "model_name": "Team Teaching",
                "rationale": "Collaborative instruction supports all learners effectively",
                "wida_context": "Mixed proficiency levels requiring differentiated support",
                "phase_plan": [
                    {
                        "phase_name": "Input",
                        "minutes": 20,
                        "bilingual_teacher_role": "Support with L1 clarification and vocabulary",
                        "primary_teacher_role": "Lead instruction and content delivery"
                    },
                    {
                        "phase_name": "Practice",
                        "minutes": 20,
                        "bilingual_teacher_role": "Circulate and provide scaffolding",
                        "primary_teacher_role": "Monitor and guide practice activities"
                    }
                ],
                "implementation_notes": ["Plan together and coordinate transitions"]
            },
            "ell_support": [
                {
                    "strategy_id": "visual_aids",
                    "strategy_name": "Visual Aids",
                    "implementation": "Use images, diagrams, and graphic organizers to support comprehension",
                    "proficiency_levels": "Levels 1-4"
                },
                {
                    "strategy_id": "sentence_frames",
                    "strategy_name": "Sentence Frames",
                    "implementation": "Provide sentence frames and starters for structured language output",
                    "proficiency_levels": "Levels 2-3"
                },
                {
                    "strategy_id": "cognate_awareness",
                    "strategy_name": "Cognate Awareness",
                    "implementation": "Highlight cognates between L1 and English to build vocabulary connections",
                    "proficiency_levels": "Levels 2-5"
                }
            ],
            "special_needs_support": ["Visual supports and modified materials"],
            "materials": ["Handouts", "Visuals", "Manipulatives"]
        },
        "misconceptions": {
            "original_content": "Students may confuse concepts or have incomplete understanding",
            "linguistic_note": {
                "pattern_id": "default",
                "note": "Common language transfer issue that may affect comprehension",
                "prevention_tip": "Use explicit instruction and contrastive examples"
            }
        },
        "assessment": {
            "primary_assessment": "Exit ticket or formative assessment",
            "bilingual_overlay": {
                "instrument": "Written response or performance task",
                "wida_mapping": "Explain + ELD-SS.6-8.Writing + Levels 2-5",
                "supports_by_level": {
                    "levels_1_2": "Sentence frames provided with word bank",
                    "levels_3_4": "Sentence starters and scaffolds",
                    "levels_5_6": "Independent writing with rubric"
                },
                "scoring_lens": "Focus on understanding and content mastery",
                "constraints_honored": "No new materials beyond existing resources"
            }
        },
        "homework": {
            "original_content": "Review notes and complete practice problems",
            "family_connection": "Discuss concepts with family and share learning"
        }
    }


# Valid JSON - should pass validation
VALID_MINIMAL_JSON = json.dumps({
    "metadata": {
        "week_of": "10/6-10/10",
        "grade": "7",
        "subject": "Social Studies"
    },
    "days": {
        "monday": _create_minimal_day("Unit One Lesson One"),
        "tuesday": _create_minimal_day("Unit One Lesson Two"),
        "wednesday": _create_minimal_day("Unit One Lesson Three"),
        "thursday": _create_minimal_day("Unit One Lesson Four"),
        "friday": _create_minimal_day("Unit One Lesson Five")
    }
})

# Invalid JSON - trailing comma
INVALID_TRAILING_COMMA = json.dumps({
    "metadata": {
        "week_of": "10/6-10/10",
        "grade": "7",
        "subject": "Social Studies",
    }
}).replace('},\n}', ',\n}')  # Force trailing comma

# Invalid JSON - wrapped in markdown
INVALID_MARKDOWN_WRAPPED = f'''```json
{VALID_MINIMAL_JSON}
```'''

# Invalid JSON - missing closing brace
INVALID_MISSING_BRACE = VALID_MINIMAL_JSON[:-1]

# Invalid JSON - with comments
INVALID_WITH_COMMENTS = VALID_MINIMAL_JSON.replace(
    '"metadata"',
    '/* This is metadata */ "metadata"'
)

# Invalid JSON - missing required field (subject)
MISSING_REQUIRED_FIELD = json.dumps({
    "metadata": {
        "week_of": "10/6-10/10",
        "grade": "7"
        # Missing "subject"
    },
    "days": {}
})

# Invalid JSON - wrong data type
WRONG_DATA_TYPE = json.dumps({
    "metadata": {
        "week_of": "10/6-10/10",
        "grade": 7,  # Should be string, not int
        "subject": "Social Studies"
    },
    "days": {}
})

# Completely malformed JSON
COMPLETELY_MALFORMED = "This is not JSON at all! Just random text."

# Empty response
EMPTY_RESPONSE = ""


# Pre-configured test sequences
# ==============================

def create_retry_sequence_success():
    """
    Sequence that fails twice then succeeds.
    Tests retry logic with eventual success.
    """
    return MockLLM([
        INVALID_TRAILING_COMMA,  # First attempt - repairable
        INVALID_MARKDOWN_WRAPPED,  # Second attempt - repairable
        VALID_MINIMAL_JSON  # Third attempt - success
    ])


def create_retry_sequence_failure():
    """
    Sequence that fails all attempts.
    Tests retry exhaustion.
    """
    return MockLLM([
        MISSING_REQUIRED_FIELD,  # First attempt - schema error
        MISSING_REQUIRED_FIELD,  # Second attempt - schema error
        MISSING_REQUIRED_FIELD  # Third attempt - schema error
    ])


def create_immediate_success():
    """
    Sequence that succeeds immediately.
    Tests happy path.
    """
    return MockLLM([VALID_MINIMAL_JSON])


def create_repair_then_success():
    """
    Sequence that needs repair then succeeds.
    Tests JSON repair functionality.
    """
    return MockLLM([
        INVALID_MARKDOWN_WRAPPED,  # Needs repair
        VALID_MINIMAL_JSON  # Success after feedback
    ])


def create_schema_error_then_success():
    """
    Sequence with schema error then success.
    Tests validation retry with feedback.
    """
    return MockLLM([
        MISSING_REQUIRED_FIELD,  # Schema error
        VALID_MINIMAL_JSON  # Fixed after feedback
    ])


# Utility functions
# =================

def get_all_test_scenarios():
    """
    Get all test scenarios for comprehensive testing.
    
    Returns:
        Dict mapping scenario name to response string
    """
    return {
        "valid_minimal": VALID_MINIMAL_JSON,
        "trailing_comma": INVALID_TRAILING_COMMA,
        "markdown_wrapped": INVALID_MARKDOWN_WRAPPED,
        "missing_brace": INVALID_MISSING_BRACE,
        "with_comments": INVALID_WITH_COMMENTS,
        "missing_required": MISSING_REQUIRED_FIELD,
        "wrong_type": WRONG_DATA_TYPE,
        "malformed": COMPLETELY_MALFORMED,
        "empty": EMPTY_RESPONSE,
    }


def create_custom_sequence(scenario_names: List[str]) -> MockLLM:
    """
    Create a custom sequence from scenario names.
    
    Args:
        scenario_names: List of scenario names from get_all_test_scenarios()
        
    Returns:
        MockLLM configured with the specified sequence
    """
    scenarios = get_all_test_scenarios()
    responses = [scenarios[name] for name in scenario_names]
    return MockLLM(responses)


if __name__ == '__main__':
    # Demo usage
    print("Mock LLM Test Scenarios")
    print("=" * 60)
    
    # Test 1: Immediate success
    print("\nTest 1: Immediate Success")
    llm = create_immediate_success()
    response = llm.generate("Generate a lesson plan")
    print(f"Response length: {len(response)} characters")
    print(f"Call count: {llm.get_call_count()}")
    
    # Test 2: Retry sequence
    print("\nTest 2: Retry Sequence (2 failures, then success)")
    llm = create_retry_sequence_success()
    for i in range(3):
        response = llm.generate(f"Attempt {i+1}")
        print(f"Attempt {i+1}: {response[:50]}...")
    print(f"Total calls: {llm.get_call_count()}")
    
    # Test 3: Custom sequence
    print("\nTest 3: Custom Sequence")
    llm = create_custom_sequence(["markdown_wrapped", "trailing_comma", "valid_minimal"])
    for i in range(3):
        response = llm.generate(f"Custom attempt {i+1}")
        print(f"Attempt {i+1}: {response[:50]}...")
    
    print("\n" + "=" * 60)
    print("Mock LLM ready for testing!")
