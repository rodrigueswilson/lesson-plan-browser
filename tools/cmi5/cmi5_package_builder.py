import sqlite3
import json
import os
import zipfile
from jinja2 import Environment, FileSystemLoader
import sys

class CMI5PackageBuilder:
    def __init__(self, db_path, template_dir, output_dir):
        self.db_path = db_path
        self.template_dir = template_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def get_lesson_data(self, lesson_id, target_level=3):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Core lesson and unit info
        query = """
            SELECT 
                l.id as lesson_id, l.title as lesson_title, l.lesson_number, 
                l.learning_intentions, l.daily_instructional_task,
                u.id as unit_id, u.title as unit_title, u.unit_number, u.subject, u.grade
            FROM lessons l
            JOIN units u ON l.unit_id = u.id
            WHERE l.id = ?
        """
        c.execute(query, (lesson_id,))
        lesson = c.fetchone()
        if not lesson:
            return None
        
        # Bilingual Vocabulary
        def_col = f"level_{target_level}_def"
        vocab_query = f"""
            SELECT 
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
        
        conn.close()
        
        return {
            "lesson_id": lesson["lesson_id"],
            "lesson_title": lesson["lesson_title"],
            "lesson_description": f"Interactive lesson for {lesson['subject']} Grade {lesson['grade']} Unit {lesson['unit_number']}",
            "grade": lesson["grade"],
            "unit_number": lesson["unit_number"],
            "unit_title": lesson["unit_title"],
            "learning_intentions": json.loads(lesson["learning_intentions"] or "[]"),
            "daily_instructional_task": lesson["daily_instructional_task"],
            "bilingual_vocabulary": bilingual_vocab
        }

    def build_package(self, lesson_id):
        data = self.get_lesson_data(lesson_id)
        if not data:
            print(f"Lesson {lesson_id} not found.")
            return None
            
        # 1. Render content
        html_template = self.env.get_template('lesson_reader_template.html')
        html_content = html_template.render(data)
        
        # 2. Render manifest (cmi5.xml)
        cmi5_template = self.env.get_template('cmi5.xml')
        cmi5_xml = cmi5_template.render(data)
        
        # 3. Create ZIP package
        safe_id = lesson_id.replace("|", "_").replace(" ", "_")
        zip_filename = f"LMS_Package_{safe_id}.zip"
        zip_path = os.path.join(self.output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Main content as index.html
            zf.writestr('index.html', html_content)
            # CMI5 manifest
            zf.writestr('cmi5.xml', cmi5_xml)
            # Add a dummy cmi5.xsd for completeness
            zf.writestr('cmi5.xsd', '<!-- cmi5 schema placeholder -->')
            
        print(f"Successfully generated CMI5 package: {zip_path}")
        return zip_path

    def build_unit_packages(self, unit_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM lessons WHERE unit_id = ?", (unit_id,))
        lesson_ids = [row[0] for row in c.fetchall()]
        conn.close()
        
        print(f"Batch generating {len(lesson_ids)} packages for Unit {unit_id}...")
        for lid in lesson_ids:
            self.build_package(lid)

if __name__ == "__main__":
    db = r"d:\LP\data\curriculum.db"
    tdir = r"d:\LP\tools\cmi5\templates"
    odir = r"d:\LP\output\packages"
    
    builder = CMI5PackageBuilder(db, tdir, odir)
    
    if len(sys.argv) > 1:
        # Check if arg is a unit_id or lesson_id (simple check)
        arg = sys.argv[1]
        if "_U" in arg and "_L" not in arg:
            builder.build_unit_packages(arg)
        else:
            builder.build_package(arg)
    else:
        # Demo: Batch generate Math Unit 2
        builder.build_unit_packages("Math_3_U2_1hBoK4uk")
