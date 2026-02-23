"""
Calculate estimated section heights for objectives layout analysis.
Used by analyze_objectives_layout.py.
"""


def calculate_estimated_heights(page_info, usable_height):
    """Calculate estimated heights for each section."""
    heights = {}

    # Header height
    if page_info['has_header']:
        header_paras = page_info['paragraphs_by_type']['header']
        if header_paras:
            para_info = header_paras[0]
            font_size = para_info.get('font_size', 10)
            heights['header'] = (font_size * 1.2) / 72  # ~0.17" for 10pt

    # Student Goal height - combine all text first
    if page_info['has_student_goal']:
        student_paras = page_info['paragraphs_by_type']['student_goal']
        if student_paras:
            font_size = student_paras[0].get('font_size', 24)
            line_spacing = student_paras[0].get('line_spacing') or 1.25

            combined_text = ' '.join(para_info['text'] for para_info in student_paras if para_info['text'].strip())

            chars_per_line = (9.4 * 72) / (font_size * 0.6) if font_size > 0 else 60
            words_per_line = max(1, chars_per_line / 6)
            words = combined_text.split()
            estimated_lines = max(1, len(words) / words_per_line)

            text_height = (font_size * line_spacing * estimated_lines) / 72

            spacing_height = 0
            if student_paras:
                spacing_height += (student_paras[0].get('space_before', 0)) / 72
                spacing_height += (student_paras[-1].get('space_after', 0)) / 72

            heights['student_goal'] = text_height + spacing_height

    # Separator height
    if page_info['has_separator']:
        separator_paras = page_info['paragraphs_by_type']['separator']
        if separator_paras:
            para_info = separator_paras[0]
            heights['separator'] = (
                (para_info.get('space_before', 0) + para_info.get('space_after', 0)) / 72 + 0.05
            )

    # WIDA height - combine all text first
    if page_info['has_wida']:
        wida_paras = page_info['paragraphs_by_type']['wida']
        if wida_paras:
            font_size = None
            for para_info in wida_paras:
                if para_info.get('font_size') and 'WIDA/Bilingual:' not in para_info['text']:
                    font_size = para_info.get('font_size', 14)
                    break
            if not font_size:
                font_size = 14

            line_spacing = wida_paras[0].get('line_spacing') or 1.0

            combined_text = ' '.join(
                para_info['text'] for para_info in wida_paras
                if para_info['text'].strip() and 'WIDA/Bilingual:' not in para_info['text']
            )

            chars_per_line = (9.6 * 72) / (font_size * 0.55) if font_size > 0 else 60
            words_per_line = max(1, chars_per_line / 6)
            words = combined_text.split()
            estimated_lines = max(1, len(words) / words_per_line)

            text_height = (font_size * line_spacing * estimated_lines) / 72

            label_height = 0
            for para_info in wida_paras:
                if 'WIDA/Bilingual:' in para_info['text']:
                    label_font = para_info.get('font_size', font_size)
                    label_height = (label_font * 1.2) / 72
                    break

            spacing_height = 0
            if wida_paras:
                spacing_height += (wida_paras[0].get('space_before', 0)) / 72
                spacing_height += (wida_paras[-1].get('space_after', 0)) / 72

            heights['wida'] = text_height + label_height + spacing_height

    total_estimated = sum(heights.values())
    heights['total_estimated'] = total_estimated
    heights['percentage_of_page'] = (total_estimated / usable_height) * 100 if usable_height > 0 else 0

    return heights
