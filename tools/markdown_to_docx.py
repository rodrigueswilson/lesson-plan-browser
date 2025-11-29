"""
Markdown to DOCX Converter - Convert markdown formatting to DOCX runs.

Handles:
- Bold: **text** or __text__
- Italic: *text* or _text_
- Bullet lists: - item or * item
- Numbered lists: 1. item
- Line breaks and paragraphs
"""

import re
from typing import List, Tuple
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class MarkdownToDocx:
    """Convert markdown text to DOCX formatted paragraphs."""
    
    # Regex patterns for markdown
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*|__(.+?)__')
    ITALIC_PATTERN = re.compile(r'\*(.+?)\*|_(.+?)_')
    BULLET_PATTERN = re.compile(r'^[\-\*]\s+(.+)$')
    NUMBERED_PATTERN = re.compile(r'^\d+\.\s+(.+)$')
    
    @staticmethod
    def add_formatted_text(paragraph, text: str):
        """
        Add formatted text to a paragraph, handling markdown formatting.
        
        Args:
            paragraph: python-docx paragraph object
            text: Text with markdown formatting
        """
        if not text:
            return
        
        # Split by bold markers first
        parts = []
        last_end = 0
        
        for match in MarkdownToDocx.BOLD_PATTERN.finditer(text):
            # Add text before bold
            if match.start() > last_end:
                parts.append(('normal', text[last_end:match.start()]))
            
            # Add bold text
            bold_text = match.group(1) or match.group(2)
            parts.append(('bold', bold_text))
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            parts.append(('normal', text[last_end:]))
        
        # Now process each part for italics
        for style, part_text in parts:
            if style == 'bold':
                # Check for italic within bold
                if MarkdownToDocx.ITALIC_PATTERN.search(part_text):
                    # Handle bold+italic
                    MarkdownToDocx._add_bold_with_italic(paragraph, part_text)
                else:
                    # Just bold
                    run = paragraph.add_run(part_text)
                    run.bold = True
            else:
                # Process for italic
                MarkdownToDocx._add_text_with_italic(paragraph, part_text)
    
    @staticmethod
    def _add_text_with_italic(paragraph, text: str):
        """Add text with italic formatting."""
        parts = []
        last_end = 0
        
        for match in MarkdownToDocx.ITALIC_PATTERN.finditer(text):
            # Add text before italic
            if match.start() > last_end:
                parts.append(('normal', text[last_end:match.start()]))
            
            # Add italic text
            italic_text = match.group(1) or match.group(2)
            parts.append(('italic', italic_text))
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            parts.append(('normal', text[last_end:]))
        
        # Add runs
        for style, part_text in parts:
            if part_text:
                run = paragraph.add_run(part_text)
                if style == 'italic':
                    run.italic = True
    
    @staticmethod
    def _add_bold_with_italic(paragraph, text: str):
        """Add bold text that may contain italic."""
        parts = []
        last_end = 0
        
        for match in MarkdownToDocx.ITALIC_PATTERN.finditer(text):
            # Add text before italic
            if match.start() > last_end:
                run = paragraph.add_run(text[last_end:match.start()])
                run.bold = True
            
            # Add bold+italic text
            italic_text = match.group(1) or match.group(2)
            run = paragraph.add_run(italic_text)
            run.bold = True
            run.italic = True
            last_end = match.end()
        
        # Add remaining text
        if last_end < len(text):
            run = paragraph.add_run(text[last_end:])
            run.bold = True
    
    @staticmethod
    def add_paragraph(cell, text: str, style=None):
        """
        Add a paragraph to a cell, handling markdown formatting.
        
        Args:
            cell: python-docx cell object
            text: Text with markdown formatting
            style: Optional paragraph style
            
        Returns:
            The created paragraph
        """
        # Check if it's a bullet list item
        bullet_match = MarkdownToDocx.BULLET_PATTERN.match(text)
        if bullet_match:
            para = cell.add_paragraph(style=style)
            # Add bullet character manually since template may not have List Bullet style
            para.add_run('  ')  # Bullet character
            MarkdownToDocx.add_formatted_text(para, bullet_match.group(1))
            return para
        
        # Check if it's a numbered list item
        numbered_match = MarkdownToDocx.NUMBERED_PATTERN.match(text)
        if numbered_match:
            para = cell.add_paragraph(style=style)
            # Keep the number prefix
            MarkdownToDocx.add_formatted_text(para, text)
            return para
        
        # Regular paragraph
        para = cell.add_paragraph(style=style)
        MarkdownToDocx.add_formatted_text(para, text)
        return para
    
    @staticmethod
    def add_multiline_text(cell, text: str, preserve_empty_lines: bool = False):
        """
        Add multi-line text to a cell, handling markdown formatting.
        
        Args:
            cell: python-docx cell object
            text: Multi-line text with markdown formatting
            preserve_empty_lines: Whether to preserve empty lines
        """
        if not text:
            return
        
        lines = text.split('\n')
        
        # Find first empty paragraph or create one
        # Skip non-empty paragraphs (like headers) to avoid merging content
        first_empty_para = None
        for para in cell.paragraphs:
            if not para.text.strip() and not para.runs:
                first_empty_para = para
                break
        
        # If no empty paragraph found, create one
        if first_empty_para is None:
            first_empty_para = cell.add_paragraph()
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines unless preserving
            if not line and not preserve_empty_lines:
                continue
            
            # Add paragraph
            if i == 0:
                # Use the first empty paragraph (found or created)
                MarkdownToDocx.add_formatted_text(first_empty_para, line)
            else:
                # Add new paragraph
                MarkdownToDocx.add_paragraph(cell, line)
    
    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Remove markdown formatting from text, leaving plain text.
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            Plain text without markdown
        """
        if not text:
            return ""
        
        # Remove bold
        text = MarkdownToDocx.BOLD_PATTERN.sub(r'\1\2', text)
        
        # Remove italic
        text = MarkdownToDocx.ITALIC_PATTERN.sub(r'\1\2', text)
        
        # Remove bullet markers
        text = MarkdownToDocx.BULLET_PATTERN.sub(r'\1', text)
        
        # Remove numbered markers
        text = MarkdownToDocx.NUMBERED_PATTERN.sub(r'\1', text)
        
        return text
