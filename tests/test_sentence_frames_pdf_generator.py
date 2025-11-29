import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.sentence_frames_pdf_generator import (  # noqa: E402
	generate_sentence_frames_html,
)


@pytest.mark.anyio
async def test_sentence_frames_html_generation(tmp_path):
	"""Generate sentence frames HTML from a minimal lesson_json and validate layout.

	This focuses on HTML structure and English-only content; PDF conversion is
	covered indirectly via the shared convert_to_pdf pipeline used by
	objectives, so we avoid Playwright/WeasyPrint dependencies here.
	"""

	lesson_json = {
		"metadata": {
			"week_of": "10/06-10/10",
			"teacher_name": "Sentence Frames Tester",
			"grade": "5",
			"subject": "Science",
			"homeroom": "HR-5A",
		},
		"days": {
			"monday": {
				"unit_lesson": "Unit One Lesson Seven",
				# Day-level sentence frames: 3x 1-2, 3x 3-4, 2x 5-6
				"sentence_frames": [
					{
						"proficiency_level": "levels_1_2",
						"english": "This is ___",
						"portuguese": "Isto e ___",
						"frame_type": "frame",
						"language_function": "describe",
					},
					{
						"proficiency_level": "levels_1_2",
						"english": "I see ___",
						"portuguese": "Eu vejo ___",
						"frame_type": "frame",
						"language_function": "observe",
					},
					{
						"proficiency_level": "levels_1_2",
						"english": "It has ___",
						"portuguese": "Tem ___",
						"frame_type": "frame",
						"language_function": "describe",
					},
					{
						"proficiency_level": "levels_3_4",
						"english": "First ___, then ___",
						"portuguese": "Primeiro ___, depois ___",
						"frame_type": "frame",
						"language_function": "sequence",
					},
					{
						"proficiency_level": "levels_3_4",
						"english": "This shows ___ because ___",
						"portuguese": "Isso mostra ___ porque ___",
						"frame_type": "frame",
						"language_function": "explain",
					},
					{
						"proficiency_level": "levels_3_4",
						"english": "I think ___ because ___",
						"portuguese": "Eu acho ___ porque ___",
						"frame_type": "frame",
						"language_function": "justify",
					},
					{
						"proficiency_level": "levels_5_6",
						"english": "Evidence suggests that ___",
						"portuguese": "As evidencias sugerem que ___",
						"frame_type": "stem",
						"language_function": "explain_evidence",
					},
					{
						"proficiency_level": "levels_5_6",
						"english": "How does ___ relate to ___?",
						"portuguese": "Como ___ se relaciona com ___?",
						"frame_type": "open_question",
						"language_function": "compare",
					},
				],
			}
		},
	}

	output_html = tmp_path / "sentence_frames_test.html"

	# Act: generate HTML
	html_path_str = generate_sentence_frames_html(
		lesson_json,
		output_path=str(output_html),
		user_name="Sentence Frames Tester",
	)

	html_path = Path(html_path_str)
	assert html_path.exists(), "Sentence frames HTML file was not created"

	contents = html_path.read_text(encoding="utf-8")

	# Basic structure checks
	assert "Sentence Frames - Week of" in contents
	assert "Levels 1-2" in contents
	assert "Levels 5-6" in contents

	# Ensure all English frames are present
	for english_text in [
		"This is ___",
		"I see ___",
		"It has ___",
		"First ___, then ___",
		"This shows ___ because ___",
		"I think ___ because ___",
		"Evidence suggests that ___",
		"How does ___ relate to ___?",
	]:
		assert english_text in contents

	# Ensure some known Portuguese strings are NOT rendered (English-only requirement)
	for portuguese_snippet in [
		"Isto e ___",
		"Eu vejo ___",
		"Primeiro ___, depois ___",
		"Isso mostra ___ porque ___",
		"As evidencias sugerem que ___",
		"Como ___ se relaciona com ___?",
	]:
		assert portuguese_snippet not in contents

	# Ensure normalized function labels appear (uppercase, spaces instead of underscores)
	for func in [
		"Describe",
		"Observe",
		"Sequence",
		"Explain",
		"Justify",
		"Explain evidence",
		"Compare",
	]:
		assert func in contents