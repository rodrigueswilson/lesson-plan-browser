"""
Render single-slot and multi-slot combined lessons to DOCX (signatures, objectives, sentence frames).
Used by combine.combine_lessons_impl. Public API: _render_single_slot, _render_multi_slot.
"""

from tools.batch_processor_pkg.combine_render.multi_slot import _render_multi_slot
from tools.batch_processor_pkg.combine_render.single_slot import _render_single_slot

__all__ = ["_render_single_slot", "_render_multi_slot"]
