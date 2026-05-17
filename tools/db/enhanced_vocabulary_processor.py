import sqlite3
import json
import uuid
from typing import List, Dict, Any
import sys
import os

# Import Pydantic models from the backend
# Ensure d:\LP is in the path
sys.path.append(r"d:\LP")
from backend.vocabulary_schema_models import (
    LeveledDefinitions, 
    VocabularyTranslation, 
    VocabularyAudio, 
    EnrichedVocabularyItem
)

# --- Mock Services (Replace with real APIs once keys are available) ---

class DictionaryService:
    def get_definition(self, term: str) -> str:
        return f"MW definition for '{term}': A standardized term used in curriculum context."

class TranslationService:
    def translate(self, text: str, target_lang: str) -> str:
        en_to_pt = {
            "area": "área",
            "multiplication": "multiplicação",
            "fraction": "fração",
            "map": "mapa",
            "globe": "globo",
            "force": "força",
            "motion": "movimento",
            "mass": "massa",
            "perimeter": "perímetro",
            "square": "quadrado",
            "bar graph": "gráfico de barras"
        }
        if target_lang == "pt":
            return en_to_pt.get(text.lower(), f"{text} (traduzido)")
        return text

class TTSService:
    def generate_audio_url(self, text: str, lang: str) -> str:
        return f"https://storage.nps.edu/audio/{lang}/{text.replace(' ', '_')}.mp3"

# --- Core Processor ---

class EnhancedVocabularyProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.dict_service = DictionaryService()
        self.trans_service = TranslationService()
        self.tts_service = TTSService()

    def generate_leveled_defs(self, term: str, lang: str) -> LeveledDefinitions:
        """Generate 6 levels of definitions using Pydantic model."""
        if term.lower() in ["area", "área"]:
            if lang == "en":
                return LeveledDefinitions(
                    level_1="The space inside a shape. (Picture: colored box)",
                    level_2="Area is the measure of how much surface a shape covers.",
                    level_3="Area is calculated by counting square units or multiplying length by width.",
                    level_4="The number of square units needed to cover a flat surface.",
                    level_5="Area is a quantity that expresses the extent of a two-dimensional figure.",
                    level_6="Area is the amount of 2D space inside a closed boundary (A=L x W)."
                )
            else:
                return LeveledDefinitions(
                    level_1="O espaço dentro de uma forma. (Imagem: caixa colorida)",
                    level_2="Área é a medida de quanta superfície uma forma cobre.",
                    level_3="A área é calculada contando unidades quadradas ou multiplicando o comprimento pela largura.",
                    level_4="O número de unidades quadradas necessárias para cobrir uma superfície plana.",
                    level_5="Área é uma quantidade que expressa a extensão de uma figura bidimensional.",
                    level_6="Área é a quantidade de espaço 2D dentro de um limite fechado (A=C x L)."
                )
        
        # Generic fallback
        return LeveledDefinitions(
            level_1=f"Level 1: {term} basics.",
            level_2=f"Level 2: {term} explained simply.",
            level_3=f"Level 3: {term} intermediate use.",
            level_4=f"Level 4: {term} advanced concept.",
            level_5=f"Level 5: {term} technical details.",
            level_6=f"Level 6: {term} mastery."
        )

    def process_all(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, base_term_en, subject, grade_cluster FROM vocabulary_items")
        items = c.fetchall()
        
        for item_id, term_en, subject, grade_cluster in items:
            print(f"Processing '{term_en}'...")
            
            # Use Pydantic to manage the word data
            enriched_item = EnrichedVocabularyItem(
                id=item_id,
                base_term_en=term_en,
                subject=subject,
                grade_cluster=grade_cluster,
                mw_definition_en=self.dict_service.get_definition(term_en)
            )

            # Process English (en)
            en_trans = VocabularyTranslation(
                language_code="en",
                translated_term=term_en,
                definitions=self.generate_leveled_defs(term_en, "en")
            )
            enriched_item.translations.append(en_trans)

            # Process Portuguese (pt)
            term_pt = self.trans_service.translate(term_en, "pt")
            pt_trans = VocabularyTranslation(
                language_code="pt",
                translated_term=term_pt,
                definitions=self.generate_leveled_defs(term_pt, "pt")
            )
            enriched_item.translations.append(pt_trans)

            # Audio
            for lang in ["en", "pt"]:
                text = term_en if lang == "en" else term_pt
                enriched_item.audio_references.append(VocabularyAudio(
                    language_code=lang,
                    audio_url=self.tts_service.generate_audio_url(text, lang)
                ))

            # --- Save Pydantic models to SQL ---
            
            # update mw_definition
            c.execute("UPDATE vocabulary_items SET mw_definition_en = ? WHERE id = ?", 
                      (enriched_item.mw_definition_en, enriched_item.id))
            
            # Clear old entries to avoid UNIQUE constraint issues on re-run
            c.execute("DELETE FROM vocabulary_translations WHERE vocab_item_id = ?", (item_id,))
            c.execute("DELETE FROM vocabulary_audio WHERE vocab_item_id = ?", (item_id,))

            for trans in enriched_item.translations:
                c.execute("""
                    INSERT INTO vocabulary_translations 
                    (vocab_item_id, language_code, translated_term, level_1_def, level_2_def, level_3_def, level_4_def, level_5_def, level_6_def)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (enriched_item.id, trans.language_code, trans.translated_term, 
                      trans.definitions.level_1, trans.definitions.level_2, trans.definitions.level_3, 
                      trans.definitions.level_4, trans.definitions.level_5, trans.definitions.level_6))
            
            for audio in enriched_item.audio_references:
                c.execute("""
                    INSERT INTO vocabulary_audio (vocab_item_id, language_code, audio_url, provider)
                    VALUES (?, ?, ?, ?)
                """, (enriched_item.id, audio.language_code, audio.audio_url, audio.provider))
                
        conn.commit()
        conn.close()
        print(f"Validated and enriched {len(items)} terms with Pydantic.")

if __name__ == "__main__":
    db = r"d:\LP\data\curriculum.db"
    EnhancedVocabularyProcessor(db).process_all()
