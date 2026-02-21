from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, RootModel


class OriginalObjective(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content_objective: str = Field(
        ...,
        description='Original content objective from primary teacher',
        examples=[
            'Students will be able to explain how systems of law and banking enabled growth in trade, wealth, and peace'
        ],
    )


class OriginalAnticipatorySet(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original_content: str = Field(
        ...,
        description='Original anticipatory set from primary teacher',
        examples=['Students will respond to an everybody writes.'],
    )


class OriginalMaterial(RootModel[str]):
    root: str = Field(
        ...,
        examples=[
            'Bilingual vocabulary chart (poster paper)',
            'Cornell Notes template (handout)',
        ],
    )


class OriginalMaterials(RootModel[List[str]]):
    root: List[str] = Field(
        ...,
        description='List of materials extracted from the lesson plan',
    )


class OriginalAssessment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    primary_assessment: str = Field(
        ...,
        description='Original assessment from primary teacher (verbatim)',
        examples=['Exit Ticket', 'Quiz on Roman systems', 'Presentation'],
    )


class OriginalHomework(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original_content: str = Field(
        ...,
        description='Original homework from primary teacher',
        examples=['Read pages 45-50', 'Complete worksheet'],
    )


class OriginalInstruction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    activities: str = Field(
        ...,
        description='Main instructional activities and procedures from the lesson plan',
    )


class OriginalTailoredInstruction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str = Field(
        ...,
        description='Original tailored instruction or differentiated steps for students',
    )


class OriginalMisconceptions(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: str = Field(
        ...,
        description='Original common misconceptions or pitfalls noted by the teacher',
    )


class OriginalHyperlink(BaseModel):
    text: str
    url: str


class OriginalHyperlinks(RootModel[List[OriginalHyperlink]]):
    root: List[OriginalHyperlink]


class OriginalDayPlanSingleSlot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    unit_lesson: str = Field(
        ...,
        description='Unit, Lesson number, and Module identifier',
        examples=['Unit One Lesson Seven', 'Module 3 Lesson 12', 'No School'],
    )
    
    objective: Optional[OriginalObjective] = None
    anticipatory_set: Optional[OriginalAnticipatorySet] = None
    instruction: Optional[OriginalInstruction] = None
    tailored_instruction: Optional[OriginalTailoredInstruction] = None
    misconceptions: Optional[OriginalMisconceptions] = None
    materials: Optional[OriginalMaterials] = None
    assessment: Optional[OriginalAssessment] = None
    homework: Optional[OriginalHomework] = None
    hyperlinks: Optional[OriginalHyperlinks] = None


class OriginalDayPlan(RootModel[OriginalDayPlanSingleSlot]):
    root: OriginalDayPlanSingleSlot
