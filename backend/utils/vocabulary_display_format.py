"""Vocabulary pair display formatting (English / Portuguese separator)."""

# Unicode U+2192; use escape so source files stay ASCII-only.
VOCAB_PAIR_SEP = " \u2192 "


def format_vocab_markdown_bullet(english: str, portuguese: str) -> str:
    """One markdown bullet for DOCX / tailored instruction: bold EN, italic PT."""
    return f"- **{english}**{VOCAB_PAIR_SEP}*{portuguese}*"


def format_vocab_plain_bullet(english: str, portuguese: str) -> str:
    """Plain bullet line for lesson step display_content."""
    return f"- {english}{VOCAB_PAIR_SEP}{portuguese}"
