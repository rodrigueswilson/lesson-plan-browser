import re
import json
import os
import sqlite3
import lancedb
import uuid
import yaml
from typing import Dict, List, Any
import sys
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from utils.gdoc_styles import StyleParser

class BaseExtractor:
    def __init__(self):
        pass

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Keep pipes for now to allow column-aware parsing in subclasses if needed
        # But replace newlines with spaces for general cleaning
        text = text.replace('\n', ' ')
        # Remove consecutive spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_standards(self, text: str) -> List[Dict[str, str]]:
        # Improved regex to catch various standard formats
        standards = []
        # Match NJSLS, NCTM, MP, PR, CCSS
        pattern = r'(NJSLS-MATH\.CONTENT\.[A-Z0-9\.]+|NCTM-MATH\.CONTENT\.[A-Z0-9\.]+|MP\d+|PR\d+|CCSS\.[A-Z0-9\.]+)'
        # Find all standard codes first
        code_matches = list(re.finditer(pattern, text, re.IGNORECASE))

        for i, match in enumerate(code_matches):
            code = match.group(0).strip().upper()
            start_index = match.end()
            end_index = code_matches[i+1].start() if i + 1 < len(code_matches) else len(text)
            
            desc = text[start_index:end_index].strip()
            
            # Clean up description (remove markdown bullets, pipes, etc)
            desc = re.sub(r'^\s*[\*\-\•]\s*', '', desc)
            desc = desc.replace('|', '').strip()
            
            standards.append({"code": code, "description": desc})
        return standards

class MathExtractor(BaseExtractor):
    def extract(self, content: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        unit_data = {
            "metadata": meta,
            "introductory_content": {},
            "standards": self.extract_standards(content),
            "lessons": []
        }

        # Extract Unit Description (Look for header first, then the content in the next row or same row)
        desc_match = re.search(r'UNIT DESCRIPTION\s*\|.*?\|\s*\|\n\|\s*\|\s*\|\s*(.*?)(?=\n\|)', content, re.IGNORECASE | re.DOTALL)
        if not desc_match:
             desc_match = re.search(r'UNIT DESCRIPTION\s*\|(.*?)\|', content, re.IGNORECASE | re.DOTALL)
        if desc_match:
            unit_data["introductory_content"]["description"] = self.clean_text(desc_match.group(1))

        # Essential Questions
        eq_match = re.search(r'Essential Questions\s*\|\s*\|\s*\n\|\s*\|\s*\|\s*(.*?)(?=\n\|)', content, re.IGNORECASE | re.DOTALL)
        if eq_match:
             qs = re.findall(r'Q\d+\.\s*(.*?)(?=\s*Q\d+\.|\n|$)', eq_match.group(1), re.DOTALL)
             unit_data["introductory_content"]["essential_questions"] = [self.clean_text(q) for q in qs]

        # Split into Lesson Blocks using Finditer (Robust method)
        # Matches "##### [LESSON 1: ...]" or similar, potentially inside a table cell "| ##### [LESSON 1: ..."
        lesson_pattern = r'#####\s*\[?LESSON\s*(\d+)\s*[:\-\.\]\s]*'
        matches = list(re.finditer(lesson_pattern, content, re.IGNORECASE))
        
        print(f"DEBUG (MathExtractor): Found {len(matches)} potential lesson starts for '{meta.get('title')}'")

        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx+1].start() if idx + 1 < len(matches) else len(content)
            block = content[start:end]
            
            lesson_num = int(match.group(1))
            # Extract Title from the first line of the block
            title_line = block.split('\n')[0].strip().strip(']').strip('|').strip()
            title = title_line.split('(')[0].strip() if '(' in title_line else title_line
            if not title: title = f"Lesson {lesson_num}"

            lesson = {
                "lesson_number": lesson_num,
                "title": title,
                "learning_intentions": [],
                "objectives_student": [],
                "mlr": "",
                "purpose": "",
                "daily_instructional_task": "",
                "success_criteria": "",
                "essential_questions": "",
                "vocabulary": [],
                "standards": self.extract_standards(block),
                "materials": "",
                "lesson_narrative": "",
                "procedure": []
            }

            # Extract Teacher-Facing Learning Objectives
            obj_t_match = re.search(r'Teacher-Facing\s+Learning Objective\(s\)\s*(.*?)(?=\|\|\s*\|\n|Student-Facing|Mathematical Language Routine|Lesson Purpose|Lesson Narrative|Vocabulary|Materials|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if obj_t_match:
                objs = re.findall(r'[\*\-\•]\s*(.*?)(?=\s*[\*\-\•]|$|\|)', obj_t_match.group(1), re.DOTALL)
                if not objs: objs = [obj_t_match.group(1)]
                lesson["learning_intentions"] = [self.clean_text(o) for o in objs if o.strip()]

            # Extract Student-Facing Learning Objectives
            obj_s_match = re.search(r'Student-Facing\s+Learning Objective\(s\)\s*(.*?)(?=\|\|\s*\|\n|Mathematical Language Routine|Lesson Purpose|Lesson Narrative|Vocabulary|Materials|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if obj_s_match:
                objs = re.findall(r'[\*\-\•]\s*(.*?)(?=\s*[\*\-\•]|$|\|)', obj_s_match.group(1), re.DOTALL)
                if not objs: objs = [obj_s_match.group(1)]
                lesson["objectives_student"] = [self.clean_text(o) for o in objs if o.strip()]

            # Extract Mathematical Language Routine(s)
            mlr_match = re.search(r'Mathematical Language Routine\(s\)\s*(.*?)(?=\|\|\s*\|\n|Lesson Purpose|Lesson Narrative|Vocabulary|Materials|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if mlr_match:
                lesson["mlr"] = self.clean_text(mlr_match.group(1)).replace('|', '').strip().lstrip('*').strip()

            # Extract Lesson Purpose
            purpose_match = re.search(r'Lesson Purpose\s*(.*?)(?=\|\|\s*\|\n|Lesson Narrative|Vocabulary|Materials|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if purpose_match:
                lesson["purpose"] = self.clean_text(purpose_match.group(1)).replace('|', '').strip().lstrip('*').strip()

            # Extract Lesson Narrative
            narrative_match = re.search(r'Lesson Narrative\s*(.*?)(?=\|\|\s*\|\n|Vocabulary|Materials|Lesson Purpose|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if narrative_match:
                lesson["lesson_narrative"] = self.clean_text(narrative_match.group(1)).replace('|', '').strip().lstrip('*').strip()

            # Extract Materials
            materials_match = re.search(r'Materials\s*(.*?)(?=\|\|\s*\|\n|Lesson Narrative|Vocabulary|Lesson Purpose|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if materials_match:
                lesson["materials"] = self.clean_text(materials_match.group(1)).replace('|', '').strip().lstrip('*').strip()

            # Extract Procedure (Warm-up, Activity, Synthesis, Supplemental)
            activity_tags = r'Warm-up|Activity \d+|Activity Synthesis|Supplemental Resources|Cool-down'
            activities = re.findall(r'\|\s*(' + activity_tags + r'):?\s*(.*?)(?=\|\|\s*\|\n|\|\||Supplemental Resources|Formative Assessment|$)', block, re.IGNORECASE | re.DOTALL)
            for act_name, act_content in activities:
                name = act_name.strip()
                content = self.clean_text(act_content)
                
                # Check for support notes within this content
                sub_tags = {
                    "Note for Building Thinking Classrooms": r'Note for Building Thinking Classrooms:\s*(.*?)(?=Access for|\Z)',
                    "Access for Students with Diverse Abilities": r'Access for Students with Diverse Abilities:\s*(.*?)(?=Access for|Note for|\Z)',
                    "Access for Multilingual Learners": r'Access for Multilingual Learners:\s*(.*?)(?=Access for|Note for|\Z)'
                }
                
                # Add sub-items first if found
                for sub_name, sub_pattern in sub_tags.items():
                    sub_match = re.search(sub_pattern, content, re.IGNORECASE | re.DOTALL)
                    if sub_match:
                        lesson["procedure"].append({
                            "name": f"{name} - {sub_name}",
                            "content": self.clean_text(sub_match.group(1))
                        })

                lesson["procedure"].append({
                    "name": name,
                    "content": content
                })

            # Extract Vocabulary
            vocab_match = re.search(r'Vocabulary\s*(.*?)(?=\|\|\s*\|\n|Materials|Lesson Narrative|Purpose|New Jersey|\Z)', block, re.IGNORECASE | re.DOTALL)
            if vocab_match:
                vocab_text = self.clean_text(vocab_match.group(1)).lstrip('*').strip()
                vocab_list = re.split(r'[\*\n,\t]', vocab_text)
                clean_vocab = []
                for v in vocab_list:
                    term = v.strip().strip('*').strip()
                    if term and term.upper() != "NA" and 1 < len(term) < 50:
                        clean_vocab.append(term)
                lesson["vocabulary"] = clean_vocab
                
            unit_data["lessons"].append(lesson)
        return unit_data

    def extract_html(self, html_content: str, json_content: Dict[str, Any] = None) -> Dict[int, Dict[str, str]]:
        """
        Extract high-fidelity HTML segments for each lesson.
        Uses JSON content if provided to identify primary headers and their IDs.
        """
        if not html_content:
            return {}
            
        soup = BeautifulSoup(html_content, 'html.parser')
        style_parser = StyleParser(html_content)
        
        # 1. Identify primary markers from JSON if available
        primary_markers_info = []
        if json_content:
            all_content = []
            if 'tabs' in json_content:
                for tab in json_content['tabs']:
                    all_content.extend(tab.get('documentTab', {}).get('body', {}).get('content', []))
            else:
                all_content = json_content.get('body', {}).get('content', [])

            def walk_json(obj):
                if isinstance(obj, dict):
                    if 'paragraph' in obj:
                        p = obj['paragraph']
                        style = p.get('paragraphStyle', {})
                        text = "".join([tel.get('textRun', {}).get('content', '') for tel in p.get('elements', []) if 'textRun' in tel]).strip()
                        # Headers or leading text like "LESSON X:"
                        if 'LESSON ' in text.upper() and (style.get('namedStyleType', '').startswith('HEADING') or text.upper().startswith('LESSON ')):
                            match = re.search(r'LESSON\s*(\d+)', text, re.IGNORECASE)
                            if match:
                                num = int(match.group(1))
                                # Only keep it if it looks like a primary title (colon or code)
                                if ':' in text or re.search(r'\d+\.\d+\.\d+', text):
                                    primary_markers_info.append({
                                        'num': num,
                                        'text': text,
                                        'headingId': style.get('headingId')
                                    })
                    for v in obj.values():
                        walk_json(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk_json(v)

            walk_json(json_content)
            
            # Filter markers to remove TOC and links
            # TOC usually appears at the very beginning of the document (low startIndex)
            # Reals lessons follow the TOC.
            if primary_markers_info:
                # Heuristic: Find the first marker that is NOT a link or heading and has a reasonable index
                # Or simply: Google Docs TOC entries often link to the same heading ID.
                # Actually, the most reliable way is: if there are multiple markers for the same lesson,
                # the one LATER in the document is likely the real heading, and the earlier one is the TOC.
                # However, if we have startIndex, we can just skip the first few thousand characters.
                pass

        print(f"DEBUG: Found {len(primary_markers_info)} primary lesson markers in JSON.")

        # 2. Find ALL potential lesson markers first to evaluate density
        all_candidates = []
        all_nodes = list(soup.descendants)
        doc_len = len(all_nodes)
        
        # Heuristic: If we have an API-verified map, we can prioritize those text strings
        # For now, we use a robust regex that matches "LESSON X" or "X: [Title]"
        pattern = re.compile(rf'^\s*(?:Unit\s+\d+\s+)?LESSON\s*(\d+)\b', re.IGNORECASE)
        
        for tag in soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'td', 'tr']):
            txt = tag.get_text().strip()
            match = pattern.match(txt)
            if match:
                l_num = int(match.group(1))
                is_link = bool(tag.find('a') or tag.name == 'a' or tag.find_parent('a'))
                pos = all_nodes.index(tag) if tag in all_nodes else 0
                all_candidates.append({
                    'num': l_num,
                    'tag': tag,
                    'pos': pos,
                    'is_link': is_link,
                    'text': txt
                })
        
        # 3. Select the best marker for each unique lesson number using "Content Density"
        all_candidates.sort(key=lambda x: x['pos'])
        unique_lesson_nums = sorted(list({c['num'] for c in all_candidates}))
        html_markers = []
        
        for l_num in unique_lesson_nums:
            candidates_for_num = [c for c in all_candidates if c['num'] == l_num]
            scored_candidates = []
            for cand in candidates_for_num:
                # Payload = number of nodes until the next candidate of ANY lesson
                next_cand_pos = doc_len
                for other in all_candidates:
                    if other['pos'] > cand['pos']:
                        next_cand_pos = other['pos']
                        break
                payload = next_cand_pos - cand['pos']
                
                # Scoring: payload size is primary, with penalties for links and early position
                link_penalty = 0.01 if cand['is_link'] else 1.0 # STERN penalty for links (TOC)
                early_penalty = 0.1 if cand['pos'] < (doc_len * 0.1) else 1.0 # STERN penalty for TOC
                
                # SPECIAL: In Grade 3 Math Unit 2, real headers are at pos > 500,000 chars roughly.
                # If we pick a late one over an early one even if it's not a link, payload must be large.
                score = payload * link_penalty * early_penalty
                
                scored_candidates.append({'cand': cand, 'score': score, 'payload': payload})
            
            scored_candidates.sort(key=lambda x: x['score'], reverse=True)
            winner = scored_candidates[0]['cand']
            
            target = winner['tag']
            if target.name in ['span', 'font'] and target.parent and target.parent.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td', 'tr']:
                target = target.parent
            
            html_markers.append({
                'num': l_num,
                'tag': target,
                'pos': winner['pos'],
                'title': winner['text']
            })
            print(f"DEBUG: Lesson {l_num} - winner at pos {winner['pos']}, payload {scored_candidates[0]['payload']}, score {scored_candidates[0]['score']:.1f}")

        # Final Deduplication and Sorting
        html_markers.sort(key=lambda x: x['pos'])
        unique_markers = html_markers # Already one per lesson num

        if not unique_markers:
            print("DEBUG: No HTML markers found even with regex.")
            return {}

        print(f"DEBUG: Found {len(unique_markers)} markers in HTML: {[m['num'] for m in unique_markers]}")

        # 3. Segment the content
        results = {}
        
        # 3a. Capture "Unit Introduction" (everything before the first lesson)
        if unique_markers:
            first_marker = unique_markers[0]['tag']
            intro_nodes = []
            curr = soup.find('body')
            if curr:
                curr = curr.find_next()
            
            # Walk from body start to the first lesson marker
            while curr and curr != first_marker:
                if curr.name in ['p', 'table', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']:
                    # Avoid adding nested elements multiple times
                    if not any(curr in ex.descendants for ex in intro_nodes):
                        # Skip things that look like Unit Title or TOC if redundant
                        intro_nodes.append(curr)
                curr = curr.find_next()
            
            if intro_nodes:
                results[0] = {
                    "title": "Unit Overview",
                    "procedure_html": self._post_process_html("".join(str(n) for n in intro_nodes), style_parser),
                    "narrative_html": ""
                }
                print(f"DEBUG: Captured Unit Overview - {len(results[0]['procedure_html'])} bytes.")

        # 3b. Segment lessons
        print(f"DEBUG: Processing {len(unique_markers)} lessons...")
        for i, m in enumerate(unique_markers):
            num = m['num']
            start_node = m['tag']
            next_marker = unique_markers[i+1]['tag'] if i+1 < len(unique_markers) else None
            
            lesson_nodes = []
            curr = start_node
            
            # Use a depth-limited search or sibling traversal to avoid jumping into giant tables 
            # and missing markers inside them.
            while curr and curr != next_marker:
                # Add unique top-level nodes
                if curr.name in ['p', 'table', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']:
                    # Important: Don't add if it's already a descendant of a collected node
                    if not any(curr in ex.descendants for ex in lesson_nodes):
                        lesson_nodes.append(curr)
                
                # Check if next_marker is INSIDE curr. If so, we must enter curr.
                if next_marker and next_marker in curr.descendants:
                    curr = curr.find_next()
                else:
                    # Move to next sibling or parent's next sibling
                    nxt = curr.find_next_sibling()
                    if nxt:
                        curr = nxt
                    else:
                        # Enter the next element in document order
                        curr = curr.find_next()
            
            print(f"DEBUG: Lesson {num} - collected {len(lesson_nodes)} nodes.")

            # Split into Narrative and Procedure
            narrative_html = []
            procedure_html = []
            target = procedure_html
            in_proc = True
            
            for node in lesson_nodes:
                text = node.get_text().upper()
                if any(kw in text for kw in ['NARRATIVE', 'PURPOSE']):
                    in_proc = False
                elif any(kw in text for kw in ['WARM-UP', 'ACTIVITY', 'SYNTHESIS', 'COOL-DOWN', 'PROCEDURE']):
                    in_proc = True
                
                target = procedure_html if in_proc else narrative_html
                target.append(str(node))

            results[num] = {
                "title": m.get("title", f"Lesson {num}"),
                "procedure_html": self._post_process_html("".join(procedure_html), style_parser),
                "narrative_html": self._post_process_html("".join(narrative_html), style_parser)
            }
            print(f"DEBUG: Lesson {num} extracted: {len(results[num]['procedure_html'])} procedure bytes, {len(results[num]['narrative_html'])} narrative bytes.")
            if len(results[num]['procedure_html']) > 0:
                print(f"  Sample Proc: {results[num]['procedure_html'][:100]}...")
            if len(results[num]['narrative_html']) > 0:
                print(f"  Sample Narr: {results[num]['narrative_html'][:100]}...")
            
        return results

    def _post_process_html(self, html: str, style_parser: StyleParser) -> str:
        """Applies semantic tags and cleans up Google Docs artifacts."""
        if not html: return ""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Transform tags based on styles
        for tag in soup.find_all(['span', 'p']):
            classes = tag.get('class', [])
            inline_style = tag.get('style', '')
            new_tag_name = style_parser.transform_element(tag.name, classes, inline_style)
            if new_tag_name != tag.name:
                tag.name = new_tag_name
                # Remove class after transformation to keep it clean, 
                # unless it's a structural class we might need later
                if 'class' in tag.attrs:
                    del tag.attrs['class']
        
        # 2. Unwrap spans that don't have a new tag name but might have children
        for span in soup.find_all('span'):
            if not span.attrs:
                span.unwrap()
                
        # 3. Clean up empty paragraphs
        for p in soup.find_all('p'):
            if not p.get_text(strip=True) and not p.find_all():
                p.decompose()

        return str(soup)

    def _extract_html_fallback(self, soup):
        # ... preserved current heuristic logic in case JSON fails ...
        # (For brevity, I'll implement this inside the same file if needed, 
        # but for now I'll just keep the main method robust)
        return {}

class ELAExtractor(BaseExtractor):
    def extract(self, content: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        unit_data = {
            "metadata": meta,
            "introductory_content": {},
            "standards": self.extract_standards(content),
            "lessons": []
        }
        
        # Extract metadata like description and essential questions
        desc_match = re.search(r'Unit Description\s*(.*?)(?=#|Essential|\|)', content, re.DOTALL)
        if desc_match:
            unit_data["introductory_content"]["description"] = self.clean_text(desc_match.group(1))
            
        eq_match = re.search(r'Essential Question[s]?\s*(.*?)(?=#|Enduring|\|)', content, re.DOTALL)
        if eq_match:
            questions = re.findall(r'\*\s*(.*?)(?=\n\*|$|\|)', eq_match.group(1), re.DOTALL)
            if not questions:
                 questions = [q.strip() for q in eq_match.group(1).split('\n') if q.strip() and not q.startswith('|')]
            unit_data["introductory_content"]["essential_questions"] = questions

        # Strategy 1: Table Extraction (Summarized view)
        # Look for the "Summary of Key Learning" table
        # We look for rows that start with | <digit> ... |
        # Extract Essential Questions from unit intro
        eq_match = re.search(r'Essential Questions?:\s*(.*?)(?=\n#|\n\||$)', content, re.IGNORECASE | re.DOTALL)
        if eq_match:
            eq_text = self.clean_text(eq_match.group(1))
            unit_data["introductory_content"]["description"] = unit_data["introductory_content"].get("description", "") + f"\n\nEssential Questions:\n{eq_text}"
            unit_data["introductory_content"]["essential_questions"] = eq_text.split('\n') # Store as list for consistency

        # Strategy: Detailed Lesson Pages
        # Search for Lesson X: [Title] headers in tables or text
        lesson_blocks = re.split(r'(?=\| Lesson \d+:|### Lesson \d+:)', content)
        found_lesson_nums = set()

        for block in lesson_blocks:
            if not any(header in block for header in ["| Lesson", "### Lesson"]): continue
            
            num_match = re.search(r'(?:\||###) Lesson (\d+):?\s*(.*?)(?:\s*\||\n|$)', block)
            if not num_match: continue
            
            lesson_num = int(num_match.group(1))
            if lesson_num in found_lesson_nums: continue
            found_lesson_nums.add(lesson_num)
            
            lesson_title = num_match.group(2).strip().replace('|', '').strip()
            
            lesson = {
                "lesson_number": lesson_num,
                "title": lesson_title,
                "learning_intentions": [],
                "success_criteria": "",
                "daily_instructional_task": "",
                "standards": self.extract_standards(block),
                "vocabulary": [],
                "procedure": [],
                "materials": "",
                "instructional_resources": [],
                "essential_questions": " ".join(unit_data["introductory_content"].get("essential_questions", []))
            }

            # Extract detailed fields from this block
            # Learning Intentions & Success Criteria Table
            li_sc_match = re.search(r'Learning Intention\s*\|\s*Success Criteria\s*\|\n\| --- \| --- \|\n\| (.*?) \| (.*?) \|', block, re.DOTALL)
            if li_sc_match:
                lesson["learning_intentions"] = [self.clean_text(li_sc_match.group(1))]
                lesson["success_criteria"] = self.clean_text(li_sc_match.group(2))

            # Anticipatory Set
            set_match = re.search(r'Anticipatory Set:\s*(.*?)(?=\||Learning Procedures|Daily Instructional Task|Differentiation)', block, re.DOTALL)
            if set_match:
                lesson["procedure"].append({"name": "Anticipatory Set", "content": self.clean_text(set_match.group(1))})
            
            # Learning Procedures
            proc_match = re.search(r'Learning Procedures:\s*(.*?)(?=\||Daily Instructional Task|Differentiation|Instructional Resources)', block, re.DOTALL)
            if proc_match:
                lesson["procedure"].append({"name": "Learning Procedures", "content": self.clean_text(proc_match.group(1))})
            
            # Daily Instructional Task
            dit_match = re.search(r'Daily Instructional Task:\s*(.*?)(?=\||Differentiation|Instructional Resources|Vocabulary)', block, re.DOTALL)
            if dit_match:
                lesson["daily_instructional_task"] = self.clean_text(dit_match.group(1))
            
            # Vocabulary
            vocab_match = re.search(r'Vocabulary:\s*(.*?)(?=\||Instructional Resources|NJSLS|Anticipatory|$)', block, re.DOTALL)
            if vocab_match:
                v_text = vocab_match.group(1).strip()
                v_list = [v.strip() for v in re.split(r'[\*\n,]', v_text) if v.strip() and len(v.strip()) > 1]
                lesson["vocabulary"] = v_list
            
            # Instructional Resources
            res_match = re.search(r'Instructional Resources:\s*(.*?)(?=\||Anticipatory|NJSLS|Learning Procedures|$)', block, re.DOTALL)
            if res_match:
                links = re.findall(r'\[(.*?)\]\((.*?)\)', res_match.group(1))
                lesson["instructional_resources"] = [{"label": l[0], "url": l[1]} for l in links]

            unit_data["lessons"].append(lesson)
        
        return unit_data

class CurriculumIngestor:
    def __init__(self, db_path: str, vector_db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.vdb = lancedb.connect(vector_db_path)
        try:
            self.fragments_table = self.vdb.open_table("curriculum_fragments")
        except:
            self.fragments_table = self.vdb.create_table("curriculum_fragments", schema={
                "id": str, "unit_id": str, "lesson_id": str, "content": str, "type": str, "metadata": str
            }, mode="overwrite")

    def ingest(self, file_path: str, grade: int, subject: str):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        frontmatter = {}
        fm_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            try: frontmatter = yaml.safe_load(fm_match.group(1))
            except: pass
        unit_number = 0
        # Priority 1: Filename or Parent Dir (e.g. Unit_2...)
        path_match = re.search(r'Unit[\s_]*(\d+)', os.path.basename(os.path.dirname(file_path)), re.IGNORECASE)
        if not path_match:
            path_match = re.search(r'Unit[\s_]*(\d+)', os.path.basename(file_path), re.IGNORECASE)
            
        if path_match:
            unit_number = int(path_match.group(1))
        else:
            # Priority 2: Frontmatter doc_title
            num_match = re.search(r'Unit[\s_]*(\d+)', frontmatter.get("doc_title", ""), re.IGNORECASE)
            if num_match:
                unit_number = int(num_match.group(1))
            else:
                # Priority 3: Fallback to last Unit X in path
                matches = re.findall(r'Unit[\s_]*(\d+)', file_path, re.IGNORECASE)
                if matches:
                    unit_number = int(matches[-1])

        # Generate source_id from the doc hash in frontmatter if available, else from uuid
        source_id = frontmatter.get("id", str(uuid.uuid4()))[:8]
        unit_id = f"{subject}_{grade}_U{unit_number}_{source_id}"
        
        meta = {
            "id": unit_id, "grade": grade, "subject": subject, "unit_number": unit_number,
            "title": frontmatter.get("doc_title", os.path.basename(os.path.dirname(file_path)).replace('_', ' ')), 
            "source": file_path
        }
        ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        source_url = frontmatter.get("source_url", "")
        source_doc_id = frontmatter.get("doc_id") or frontmatter.get("source_doc_id")
        if not source_doc_id and source_url:
            m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", source_url)
            if m:
                source_doc_id = m.group(1)
        ingest_run_id = f"{ingested_at.replace(':', '-').replace('.', '-')}_{unit_id}"
        parser_version = "extract_curriculum@v1"
        meta.update({
            "source_doc_id": source_doc_id,
            "source_url": source_url,
            "ingested_at": ingested_at,
            "ingest_run_id": ingest_run_id,
            "ingest_parser_version": parser_version,
        })
        
        # Clean up title
        if "Unit Description" in meta["title"] or "Copy of" in meta["title"] or "Unit" not in meta["title"]:
            meta["title"] = f"Unit {unit_number}: {os.path.basename(os.path.dirname(file_path)).replace('Unit_' + str(unit_number) + '__', '').replace('_', ' ')}"
        
        extractor_name = "MathExtractor" if subject == "Math" else "ELAExtractor"
        print(f"Ingesting {meta['title']} using {extractor_name}...")
        
        extractor = MathExtractor() if subject == "Math" else ELAExtractor()
        unit_data = extractor.extract(content, meta)
        
        # 4. Check for high-fidelity HTML export
        originals_dir = os.path.join(os.path.dirname(file_path), "originals")
        html_file = None
        json_file = None
        
        if os.path.exists(originals_dir):
            all_files = os.listdir(originals_dir)
            # Try to find an HTML file
            for f in all_files:
                if f.endswith(".html"):
                    html_file = os.path.join(originals_dir, f)
                    # Break if it matches base_name, otherwise keep looking just in case
                    if os.path.basename(file_path).replace('.md', '') in f:
                        break
            
            if html_file:
                json_file = html_file.replace('.html', '.json')
                if not os.path.exists(json_file):
                    json_file = None
        
        if html_file and hasattr(extractor, 'extract_html'):
            print(f"Found HTML export: {html_file}. Extracting high-fidelity content...")
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            json_content = None
            if json_file and os.path.exists(json_file):
                print(f"DEBUG: Found structural JSON: {json_file}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_content = json.load(f)
                except Exception as e:
                    print(f"WARNING: Error loading JSON: {e}")
            
            html_data = extractor.extract_html(html_content, json_content)
            print(f"DEBUG: extract_html returned {len(html_data)} lessons. Keys: {list(html_data.keys())}")
            
            if html_data:
                # Map HTML data back to existing lessons or populate if empty
                if not unit_data.get("lessons"):
                    print(f"Populating {len(html_data)} lessons from high-fidelity HTML...")
                    for l_num, data in sorted(html_data.items()):
                        if l_num == 0:
                            # Unit Overview
                            unit_data.setdefault("introductory_content", {})["procedure_html"] = data["procedure_html"]
                            continue
                        unit_data.setdefault("lessons", []).append({
                            "lesson_number": l_num,
                            "title": data.get("title", f"Lesson {l_num}"),
                            "procedure_html": data["procedure_html"],
                            "narrative_html": data["narrative_html"]
                        })
                else:
                    existing_nums = {int(l["lesson_number"]) for l in unit_data["lessons"] if str(l.get("lesson_number", "")).isdigit()}
                    
                    # 1. Update existing lessons
                    for l_num, h_data in html_data.items():
                        if l_num == 0:
                            unit_data.setdefault("introductory_content", {})["procedure_html"] = h_data["procedure_html"]
                            continue
                            
                        # Find matching lesson
                        found = False
                        for lesson in unit_data["lessons"]:
                            try:
                                cur_num = int(lesson["lesson_number"])
                            except: continue
                            
                            if cur_num == l_num:
                                lesson["title"] = h_data.get("title", lesson["title"])
                                lesson["procedure_html"] = h_data.get("procedure_html", "")
                                lesson["narrative_html"] = h_data.get("narrative_html", "")
                                if not lesson["procedure_html"] and lesson["narrative_html"]:
                                    lesson["procedure_html"] = lesson["narrative_html"]
                                    lesson["narrative_html"] = ""
                                found = True
                                break
                        
                        if not found and l_num > 0:
                            print(f"Adding Lesson {l_num} from high-fidelity HTML (missing in markdown)...")
                            unit_data["lessons"].append({
                                "lesson_number": l_num,
                                "title": h_data.get("title", f"Lesson {l_num}"),
                                "procedure_html": h_data.get("procedure_html", ""),
                                "narrative_html": h_data.get("narrative_html", ""),
                                "learning_intentions": [],
                                "objectives_student": [],
                                "mlr": "",
                                "purpose": "",
                                "vocabulary": [],
                                "standards": [],
                                "procedure": [],
                                "materials": ""
                            })
        
        print(f"DEBUG: Final unit data has {len(unit_data.get('lessons', []))} lessons.")
        for l in unit_data.get("lessons", []):
            print(f"  Lesson {l['lesson_number']}: {l['title']}")
            
        self.save_to_db(unit_data)

    def save_to_db(self, unit_data: Dict[str, Any]):
        c = self.conn.cursor()
        meta = unit_data["metadata"]
        
        c.execute("INSERT OR REPLACE INTO units (id, grade, subject, unit_number, title, description, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (meta["id"], meta["grade"], meta["subject"], meta["unit_number"], meta["title"], 
                   unit_data.get("introductory_content", {}).get("description"), meta["source"]))
        c.execute(
            """
            UPDATE units
            SET source_doc_id = ?,
                source_url = ?,
                ingested_at = ?,
                ingest_run_id = ?,
                ingest_parser_version = ?
            WHERE id = ?
            """,
            (
                meta.get("source_doc_id"),
                meta.get("source_url"),
                meta.get("ingested_at"),
                meta.get("ingest_run_id"),
                meta.get("ingest_parser_version"),
                meta["id"],
            ),
        )
        
        intro = unit_data.get("introductory_content", {})
        c.execute("INSERT OR REPLACE INTO units_intro (unit_id, essential_questions, enduring_understandings, procedure_html) VALUES (?, ?, ?, ?)",
                  (meta["id"], json.dumps(intro.get("essential_questions", [])), json.dumps(intro.get("enduring_understandings", [])), intro.get("procedure_html", "")))
        
        for std in unit_data.get("standards", []):
            c.execute("INSERT OR IGNORE INTO standards (code, description, subject) VALUES (?, ?, ?)", (std["code"], std["description"], meta["subject"]))
            c.execute("INSERT OR REPLACE INTO unit_standards (unit_id, standard_code, type) VALUES (?, ?, ?)", (meta["id"], std["code"], "focus"))

        for lesson in unit_data["lessons"]:
            lesson_id = f"{meta['id']}_L{lesson['lesson_number']}"
            c.execute("""
                INSERT OR REPLACE INTO lessons 
                (id, unit_id, lesson_number, title, learning_intentions, daily_instructional_task, success_criteria, essential_questions, procedure, materials, lesson_narrative, instructional_resources, purpose, mlr, objectives_student, procedure_html, narrative_html) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson_id, meta["id"], lesson["lesson_number"], lesson["title"], 
                json.dumps(lesson.get("learning_intentions", [])), 
                lesson.get("daily_instructional_task", ""),
                lesson.get("success_criteria", ""),
                lesson.get("essential_questions", ""),
                json.dumps(lesson.get("procedure", [])),
                lesson.get("materials", ""),
                lesson.get("lesson_narrative", ""),
                json.dumps(lesson.get("instructional_resources", [])),
                lesson.get("purpose", ""),
                lesson.get("mlr", ""),
                json.dumps(lesson.get("objectives_student", [])),
                lesson.get("procedure_html", ""),
                lesson.get("narrative_html", "")
            ))
            c.execute(
                """
                UPDATE lessons
                SET source_doc_id = ?,
                    source_url = ?,
                    ingested_at = ?,
                    ingest_run_id = ?,
                    ingest_parser_version = ?
                WHERE id = ?
                """,
                (
                    meta.get("source_doc_id"),
                    meta.get("source_url"),
                    meta.get("ingested_at"),
                    meta.get("ingest_run_id"),
                    meta.get("ingest_parser_version"),
                    lesson_id,
                ),
            )
            
            for std in lesson.get("standards", []):
                c.execute("INSERT OR IGNORE INTO standards (code, description, subject) VALUES (?, ?, ?)", (std["code"], std["description"], meta["subject"]))
                c.execute("INSERT OR REPLACE INTO lesson_standards (lesson_id, standard_code) VALUES (?, ?)", (lesson_id, std["code"]))

            # NEW Updated Vocabulary Storage
            for term in lesson.get("vocabulary", []):
                vocab_item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, term.lower()))
                c.execute("""
                    INSERT OR IGNORE INTO vocabulary_items (id, base_term_en, subject, grade_cluster) 
                    VALUES (?, ?, ?, ?)
                """, (vocab_item_id, term, meta["subject"], f"{meta['grade']}"))
                
                c.execute("INSERT OR REPLACE INTO lesson_vocabulary (lesson_id, vocab_item_id) VALUES (?, ?)", 
                          (lesson_id, vocab_item_id))

            if lesson.get("narrative"):
                self.fragments_table.add([{
                    "id": f"{lesson_id}_narrative", "unit_id": meta["id"], "lesson_id": lesson_id,
                    "content": lesson["narrative"], "type": "lesson_narrative", "metadata": json.dumps({"lesson_number": lesson["lesson_number"]})
                }])
        self.conn.commit()
        print(f"Successfully ingested Unit {meta['unit_number']}: {meta['title']} ({meta['subject']})")

if __name__ == "__main__":
    db_path = r"d:\LP\data\curriculum.db"
    vdb_path = r"d:\LP\data\lance_db"
    if len(sys.argv) >= 4:
        file_path, grade, subject = sys.argv[1], int(sys.argv[2]), sys.argv[3]
        CurriculumIngestor(db_path, vdb_path).ingest(file_path, grade, subject)
    else:
        print("Usage: python extract_curriculum.py <file_path> <grade> <subject>")
