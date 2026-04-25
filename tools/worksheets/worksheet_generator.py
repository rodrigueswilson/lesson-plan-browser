import sqlite3
import json
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import sys

class WorksheetGenerator:
    def __init__(self, db_path, template_dir, output_dir):
        self.db_path = db_path
        self.template_dir = template_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template('worksheet_template.html')

    def get_lesson_data(self, lesson_id, target_level=3):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Join lesson, unit, and intro info
        query = """
            SELECT 
                l.id as lesson_id, l.title as lesson_title, l.lesson_number, 
                l.learning_intentions, l.daily_instructional_task,
                u.id as unit_id, u.title as unit_title, u.unit_number, u.subject, u.grade,
                ui.essential_questions
            FROM lessons l
            JOIN units u ON l.unit_id = u.id
            LEFT JOIN units_intro ui ON u.id = ui.unit_id
            WHERE l.id = ?
        """
        c.execute(query, (lesson_id,))
        lesson = c.fetchone()
        if not lesson:
            return None
        
        # Get EN and PT Vocabulary for this lesson
        # We'll fetch the leveled definition too
        def_col = f"level_{target_level}_def"
        vocab_query = f"""
            SELECT 
                vi.base_term_en as term_en,
                vt_en.translated_term as label_en, 
                vt_en.{def_col} as def_en,
                vt_pt.translated_term as label_pt,
                vt_pt.{def_col} as def_pt
            FROM lesson_vocabulary lv
            JOIN vocabulary_items vi ON lv.vocab_item_id = vi.id
            LEFT JOIN vocabulary_translations vt_en ON vi.id = vt_en.vocab_item_id AND vt_en.language_code = 'en'
            LEFT JOIN vocabulary_translations vt_pt ON vi.id = vt_pt.vocab_item_id AND vt_pt.language_code = 'pt'
            WHERE lv.lesson_id = ?
        """
        c.execute(vocab_query, (lesson_id,))
        vocab_rows = c.fetchall()
        
        bilingual_vocab = []
        for row in vocab_rows:
            bilingual_vocab.append({
                "en": row["label_en"],
                "pt": row["label_pt"],
                "def_en": row["def_en"],
                "def_pt": row["def_pt"]
            })
        
        # Get Standards
        c.execute("""
            SELECT s.code, s.description
            FROM lesson_standards ls
            JOIN standards s ON ls.standard_code = s.code
            WHERE ls.lesson_id = ?
        """, (lesson_id,))
        standards = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        # Translate main headers if possible (simplified for prototype)
        data = {
            "subject": lesson["subject"],
            "grade": lesson["grade"],
            "unit_number": lesson["unit_number"],
            "unit_title": lesson["unit_title"],
            "lesson_number": lesson["lesson_number"],
            "lesson_title": lesson["lesson_title"],
            "qr_content": f"STUDENT_ID|{lesson_id}",
            "content_instruction": "Answer the following questions based on today's lesson goals.",
            "content_items": [
                {"question": intent} for intent in json.loads(lesson["learning_intentions"] or "[]")
            ],
            "bilingual_vocabulary": bilingual_vocab, # New field
            "sentence_frames": [
                {"text": f"One thing I learned about <b>{lesson['lesson_title']}</b> is <span class='blank'></span>."}
            ],
            "exit_ticket_instruction": "Describe one new fact you learned today using one of our vocabulary words.",
            "standards": standards
        }

        # Subject-specific logic
        if lesson["subject"] == "Math":
            data["content_instruction"] = "Solve the problems below using the strategies we practiced."
        else:
            data["content_instruction"] = "Use information from the text to answer these questions."

        return data

    def generate(self, lesson_id, output_filename=None):
        data = self.get_lesson_data(lesson_id)
        if not data:
            print(f"Lesson {lesson_id} not found.")
            return None
            
        html_out = self.template.render(data)
        
        if not output_filename:
            output_filename = f"Worksheet_{lesson_id.replace('|', '_')}.pdf"
            
        pdf_path = os.path.join(self.output_dir, output_filename)
        HTML(string=html_out, base_url=self.template_dir).write_pdf(pdf_path)
        print(f"Successfully generated BILINGUAL worksheet: {pdf_path}")
        return pdf_path

if __name__ == "__main__":
    db = r"d:\LP\data\curriculum.db"
    tdir = r"d:\LP\tools\worksheets"
    odir = r"d:\LP\output\worksheets"
    
    gen = WorksheetGenerator(db, tdir, odir)
    
    if len(sys.argv) > 1:
        lesson_id = sys.argv[1]
        gen.generate(lesson_id)
    else:
        # Math Unit 2 Lesson 1 (Area)
        gen.generate("Math_3_U2_1hBoK4uk_L1", "Math_G3_U2_L1_Area_Bilingual.pdf")
        # ELA Unit 2 Lesson 1 (Maps)
        gen.generate("ELA_3_U2_1gVaamRd_L1", "ELA_G3_U2_L1_Maps_Bilingual.pdf")
