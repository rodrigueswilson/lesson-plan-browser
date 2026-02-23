"""
Support and assessment overlay schema models for lesson plans.
Re-exported from lesson_schema_models for backward compatibility.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SupportsByLevel(BaseModel):
    levels_1_2: str = Field(
        ...,
        description="Supports for WIDA Levels 1-2 (Entering/Emerging)",
        examples=[
            "Sentence frame provided, word bank with vocabulary pairs (**law** → *lei*, **system** → *sistema*), allow L1 draft then translate"
        ],
        min_length=20,
    )
    levels_3_4: str = Field(
        ...,
        description="Supports for WIDA Levels 3-4 (Developing/Expanding)",
        examples=[
            "Sentence starter provided, vocabulary pair chart reference (**law** → *lei*, **system** → *sistema*), bilingual dictionary allowed"
        ],
        min_length=20,
    )
    levels_5_6: str = Field(
        ...,
        description="Supports for WIDA Levels 5-6 (Bridging/Reaching)",
        examples=[
            "Open response, optional sentence frames, focus on academic vocabulary"
        ],
        min_length=20,
    )


class BilingualOverlay(BaseModel):
    instrument: str = Field(
        ...,
        description="Assessment instrument type and format",
        examples=[
            "Written exit ticket (1-2 sentences)",
            "Oral presentation (3-5 minutes)",
            "Multiple choice quiz (10 questions)",
        ],
        min_length=10,
    )
    wida_mapping: str = Field(
        ...,
        description="Key Language Use + ELD domain + proficiency levels",
        examples=["Explain + ELD-SS.6-8.Writing + Levels 2-5"],
        pattern=".*(Explain|Narrate|Inform|Argue).*ELD.*Level",
    )
    supports_by_level: SupportsByLevel = Field(
        ..., description="Level-banded supports using only available materials"
    )
    scoring_lens: str = Field(
        ...,
        description="Language-focused scoring criteria aligned to primary rubric",
        examples=[
            "Accept responses showing understanding of cause-effect relationship; credit use of academic vocabulary (**law** → *lei*, **banking** → *banco*, **peace** → *paz*); allow code-switching if meaning is clear"
        ],
        min_length=30,
    )
    constraints_honored: str = Field(
        ...,
        description="Confirmation that no new materials or task changes introduced",
        examples=["No new materials; uses existing exit ticket format"],
        min_length=15,
    )
