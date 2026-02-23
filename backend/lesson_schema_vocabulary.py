"""
Vocabulary, sentence frames, and homework schema models for lesson plans.
Re-exported from lesson_schema_models for backward compatibility.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, RootModel

from backend.lesson_schema_enums import FrameType, ProficiencyLevel


class VocabularyCognate(BaseModel):
    english: str = Field(..., description="English word", min_length=2)
    portuguese: str = Field(..., description="Portuguese word", min_length=2)
    is_cognate: bool | None = Field(
        ..., description="Whether this is a true cognate pair (optional, can be null)"
    )
    relevance_note: str | None = Field(
        ...,
        description="Brief note on why this word pair is relevant to the lesson (optional, can be null)",
    )


class VocabularyCognates(RootModel[list[VocabularyCognate]]):
    root: list[VocabularyCognate] = Field(
        ...,
        description="List of exactly 6 English-Portuguese word pairs highly relevant to lesson objectives",
        examples=[
            [
                {
                    "english": "law",
                    "portuguese": "lei",
                    "is_cognate": False,
                    "relevance_note": "Core concept for understanding Roman legal systems",
                },
                {
                    "english": "system",
                    "portuguese": "sistema",
                    "is_cognate": True,
                    "relevance_note": "Essential for describing how Roman institutions worked",
                },
                {
                    "english": "banking",
                    "portuguese": "banco",
                    "is_cognate": False,
                    "relevance_note": "Key economic institution enabling trade growth",
                },
                {
                    "english": "economy",
                    "portuguese": "economia",
                    "is_cognate": True,
                    "relevance_note": "Central to understanding economic growth concepts",
                },
                {
                    "english": "trade",
                    "portuguese": "comércio",
                    "is_cognate": False,
                    "relevance_note": "Fundamental concept for lesson on economic systems",
                },
                {
                    "english": "peace",
                    "portuguese": "paz",
                    "is_cognate": False,
                    "relevance_note": "Important outcome of effective legal and economic systems",
                },
            ]
        ],
        max_length=6,
        min_length=6,
    )


class SentenceFrame(BaseModel):
    proficiency_level: ProficiencyLevel = Field(
        ..., description="WIDA proficiency level group"
    )
    english: str = Field(
        ..., description="English sentence frame/stem/question", min_length=2
    )
    portuguese: str = Field(
        ..., description="Portuguese sentence frame/stem/question", min_length=2
    )
    language_function: str = Field(
        ...,
        description="Target language function (e.g., explain, compare, describe, argue)",
        examples=["explain", "compare", "describe", "argue", "sequence", "justify"],
    )
    frame_type: FrameType = Field(
        ...,
        description="Type of frame: frame for Levels 1-2/3-4, stem or open_question for Levels 5-6",
    )


class SentenceFrames(RootModel[list[SentenceFrame]]):
    root: list[SentenceFrame] = Field(
        ...,
        description="List of exactly 8 sentence frames/stems/questions distributed by WIDA proficiency levels: 3 for Levels 1-2, 3 for Levels 3-4, and 2 for Levels 5-6 (1 stem + 1 open question)",
        examples=[
            [
                {
                    "proficiency_level": "levels_1_2",
                    "english": "This is ___",
                    "portuguese": "Isto é ___",
                    "language_function": "identify",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_1_2",
                    "english": "I see ___",
                    "portuguese": "Eu vejo ___",
                    "language_function": "describe",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_1_2",
                    "english": "It has ___",
                    "portuguese": "Tem ___",
                    "language_function": "describe",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "First ___, then ___",
                    "portuguese": "Primeiro ___, depois ___",
                    "language_function": "sequence",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "This shows ___ because ___",
                    "portuguese": "Isso mostra ___ porque ___",
                    "language_function": "explain",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "I think ___ because ___",
                    "portuguese": "Eu acho ___ porque ___",
                    "language_function": "justify",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_5_6",
                    "english": "Evidence suggests that ___",
                    "portuguese": "As evidências sugerem que ___",
                    "language_function": "argue",
                    "frame_type": "stem",
                },
                {
                    "proficiency_level": "levels_5_6",
                    "english": "How does ___ relate to ___?",
                    "portuguese": "Como ___ se relaciona com ___?",
                    "language_function": "analyze",
                    "frame_type": "open_question",
                },
            ]
        ],
        max_length=8,
        min_length=8,
    )


class Homework(BaseModel):
    original_content: str = Field(
        ...,
        description="Original homework from primary teacher (may be empty)",
        examples=["", "Read pages 45-50", "Complete worksheet"],
    )
    family_connection: str = Field(
        ...,
        description="Family-friendly Portuguese-English home activity",
        examples=[
            "Ask family: 'Como as leis ajudam nossa comunidade?' (How do laws help our community?) Discuss in Portuguese/English and share one example in class."
        ],
        min_length=30,
    )
