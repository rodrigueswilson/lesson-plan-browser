# Lesson output schema enums (extracted from lesson_schema_models for clarity).
# Re-exported from backend.lesson_schema_models for backward compatibility.

from __future__ import annotations

from enum import Enum


class ModelName(Enum):
    Station_Teaching = "Station Teaching"
    Parallel_Teaching = "Parallel Teaching"
    Team_Teaching = "Team Teaching"
    Alternative_Teaching = "Alternative Teaching"
    One_Teach_One_Assist = "One Teach One Assist"
    One_Teach_One_Observe = "One Teach One Observe"


# JSON-serializable by default (subclass str) for instructor library, json.dumps, etc.
class PatternId(str, Enum):
    subject_pronoun_omission = "subject_pronoun_omission"
    adjective_placement = "adjective_placement"
    past_tense_ed_dropping = "past_tense_ed_dropping"
    preposition_depend_on = "preposition_depend_on"
    false_cognate_actual = "false_cognate_actual"
    false_cognate_library = "false_cognate_library"
    default = "default"


class ProficiencyLevel(str, Enum):
    levels_1_2 = "levels_1_2"
    levels_3_4 = "levels_3_4"
    levels_5_6 = "levels_5_6"


class FrameType(str, Enum):
    frame = "frame"
    stem = "stem"
    open_question = "open_question"
