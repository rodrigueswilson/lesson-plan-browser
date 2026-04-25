from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict

class LeveledDefinitions(BaseModel):
    level_1: str = Field(..., description="WIDA Level 1: Entering (Picture/Simple)")
    level_2: str = Field(..., description="WIDA Level 2: Emerging (Basic)")
    level_3: str = Field(..., description="WIDA Level 3: Developing (Intermediate)")
    level_4: str = Field(..., description="WIDA Level 4: Expanding (Advanced)")
    level_5: str = Field(..., description="WIDA Level 5: Bridging (Complex)")
    level_6: str = Field(..., description="WIDA Level 6: Reaching (Mastery)")

class VocabularyTranslation(BaseModel):
    language_code: str = Field(..., pattern="^[a-z]{2}$", description="ISO 639-1 language code (en, pt, es)")
    translated_term: str = Field(..., min_length=1)
    definitions: LeveledDefinitions

class VocabularyAudio(BaseModel):
    language_code: str
    audio_url: str
    provider: str = "google_tts"

class EnrichedVocabularyItem(BaseModel):
    id: str
    base_term_en: str
    category: Optional[str] = Field(None, description="everyday, cross-disciplinary, technical")
    subject: Optional[str] = None
    grade_cluster: Optional[str] = None
    mw_definition_en: Optional[str] = None
    translations: List[VocabularyTranslation] = Field(default_factory=list)
    audio_references: List[VocabularyAudio] = Field(default_factory=list)

class LessonVocabularyBatch(BaseModel):
    lesson_id: str
    vocabulary_items: List[EnrichedVocabularyItem]
