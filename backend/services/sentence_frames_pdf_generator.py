"""HTML + PDF generator for sentence frames with precise layout control.

This module mirrors the ObjectivesPDFGenerator pattern but focuses on
printable, English-only sentence frame sheets (two pages per lesson,
with fold lines and thirds).

Public API: SentenceFramesPDFGenerator, generate_sentence_frames_html,
generate_sentence_frames_pdf, generate_sentence_frames_docx.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.file_manager import get_file_manager
from backend.telemetry import logger
from backend.utils.metadata_utils import get_teacher_name

from backend.services.sentence_frames import docx_renderer, extraction, html_builder, pdf_renderer


class SentenceFramesPDFGenerator:
    """Generate sentence frames as HTML and convert to PDF for printing."""

    def __init__(self) -> None:
        self.css_template = html_builder.get_css_template()
        self.html_template = html_builder.get_html_template()
        self.file_manager = get_file_manager()
        self._default_output_dir = Path(self.file_manager.base_path)

    def _resolve_output_directory(self, lesson_json: Dict[str, Any]) -> Path:
        metadata = lesson_json.get("metadata", {})
        week_of = metadata.get("week_of")
        if week_of:
            try:
                week_folder = Path(self.file_manager.get_week_folder(week_of))
                week_folder.mkdir(parents=True, exist_ok=True)
                return week_folder
            except Exception as exc:
                logger.warning(
                    "sentence_frames_week_folder_resolution_failed",
                    extra={"week_of": week_of, "error": str(exc)},
                )

        self._default_output_dir.mkdir(parents=True, exist_ok=True)
        return self._default_output_dir

    def _sanitize_for_filename(self, value: str, fallback: str) -> str:
        import re

        clean = re.sub(r"[^A-Za-z0-9]+", "_", (value or "")).strip("_")
        return clean or fallback

    def _build_default_basename(
        self, lesson_json: Dict[str, Any], user_name: Optional[str]
    ) -> str:
        metadata = lesson_json.get("metadata", {})
        teacher = get_teacher_name(metadata, user_name=user_name) or "Teacher"
        week_label = metadata.get("week_of") or datetime.now().strftime("%m-%d")
        teacher_slug = self._sanitize_for_filename(teacher, "Teacher")
        week_slug = self._sanitize_for_filename(week_label.replace("/", "-"), "Week")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{teacher_slug}_SentenceFrames_{week_slug}_{timestamp}"

    def _resolve_html_path(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        output_path: Optional[str],
    ) -> Path:
        if output_path:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            return target

        directory = self._resolve_output_directory(lesson_json)
        base_name = self._build_default_basename(lesson_json, user_name)
        target = directory / f"{base_name}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _resolve_pdf_and_html_paths(
        self,
        lesson_json: Dict[str, Any],
        user_name: Optional[str],
        pdf_path: Optional[str],
    ) -> Tuple[Path, Path]:
        if pdf_path:
            pdf_file = Path(pdf_path)
            html_file = pdf_file.with_suffix(".html")
            pdf_file.parent.mkdir(parents=True, exist_ok=True)
            html_file.parent.mkdir(parents=True, exist_ok=True)
            return html_file, pdf_file

        directory = self._resolve_output_directory(lesson_json)
        base_name = self._build_default_basename(lesson_json, user_name)
        html_file = directory / f"{base_name}.html"
        pdf_file = directory / f"{base_name}.pdf"
        html_file.parent.mkdir(parents=True, exist_ok=True)
        return html_file, pdf_file

    def extract_sentence_frames(self, lesson_json: Dict[str, Any]):
        """Extract sentence frame payloads from lesson JSON."""
        return extraction.extract_sentence_frames(lesson_json)

    def generate_html(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> str:
        """Generate HTML file with sentence frames pages."""
        payloads = self.extract_sentence_frames(lesson_json)
        if not payloads:
            raise ValueError("No sentence_frames found in lesson plan")

        metadata = lesson_json.get("metadata", {})
        final_html = html_builder.build_pages(payloads, metadata)

        output_file = self._resolve_html_path(lesson_json, user_name, output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        logger.info(
            "sentence_frames_html_generated",
            extra={
                "output_path": str(output_file),
                "page_pairs": len(payloads),
                "week_of": payloads[0]["week_of"],
            },
        )

        return str(output_file)

    def convert_to_pdf(self, html_path: str, pdf_path: str) -> str:
        """Convert HTML file to PDF using WeasyPrint with Playwright fallback."""
        return pdf_renderer.convert_to_pdf(
            html_path, pdf_path, self.css_template
        )

    def generate_docx(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> str:
        """Generate DOCX file with sentence frames, two pages per day (front/back)."""
        payloads = self.extract_sentence_frames(lesson_json)
        if not payloads:
            raise ValueError("No sentence frames found in lesson plan")

        metadata = lesson_json.get("metadata", {})

        if output_path:
            docx_file = Path(output_path)
        else:
            directory = self._resolve_output_directory(lesson_json)
            base_name = self._build_default_basename(lesson_json, user_name)
            docx_file = directory / f"{base_name}.docx"

        docx_file.parent.mkdir(parents=True, exist_ok=True)

        return docx_renderer.generate_docx(payloads, metadata, docx_file)

    def generate_pdf(
        self,
        lesson_json: Dict[str, Any],
        output_path: Optional[str] = None,
        user_name: Optional[str] = None,
        keep_html: bool = True,
    ) -> str:
        """Generate PDF file with sentence frames (HTML + PDF conversion)."""
        html_path, pdf_path = self._resolve_pdf_and_html_paths(
            lesson_json, user_name, output_path
        )
        generated_html = self.generate_html(
            lesson_json, str(html_path), user_name=user_name
        )
        final_pdf = self.convert_to_pdf(generated_html, str(pdf_path))
        if not keep_html:
            try:
                Path(generated_html).unlink()
            except OSError:
                pass
        return final_pdf


def generate_sentence_frames_html(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
) -> str:
    """Convenience wrapper to generate sentence frames HTML."""
    generator = SentenceFramesPDFGenerator()
    return generator.generate_html(
        lesson_json, output_path=output_path, user_name=user_name
    )


def generate_sentence_frames_pdf(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
    keep_html: bool = True,
) -> str:
    """Convenience wrapper to generate sentence frames PDF from lesson JSON."""
    generator = SentenceFramesPDFGenerator()
    return generator.generate_pdf(lesson_json, output_path, user_name, keep_html)


def generate_sentence_frames_docx(
    lesson_json: Dict[str, Any],
    output_path: str,
    user_name: Optional[str] = None,
) -> str:
    """Convenience wrapper to generate sentence frames DOCX from lesson JSON."""
    generator = SentenceFramesPDFGenerator()
    return generator.generate_docx(lesson_json, output_path, user_name)
