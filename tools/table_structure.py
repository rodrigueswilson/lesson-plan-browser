"""
Table Structure Detection for Coordinate-Based Hyperlink Placement

Detects table structure patterns and provides mapping for flexible placement.
Supports standard 8x6, 9x6 with Day row, 13x6 extended, and adaptive structures.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class StructureMetadata:
    """Metadata about table structure for adaptive placement."""
    
    structure_type: str  # "standard_8x6", "with_day_row_9x6", "extended_13x6", "adaptive"
    num_rows: int
    num_cols: int
    row_offset: int  # Offset to apply to row indices (e.g., +1 for Day row)
    has_day_row: bool
    row_label_map: Dict[str, int]  # Label → row_index
    col_header_map: Dict[str, int]  # Day → col_index
    
    def get_row_index(self, label: str) -> Optional[int]:
        """Get row index by label with aggressive normalization and fallback matching."""
        if not label:
            return None
        
        # Apply same aggressive normalization as _build_row_map
        normalized = label.strip().lower()
        normalized = normalized.rstrip(':').rstrip(',').rstrip('.')
        normalized = normalized.replace('/', ' ').replace('&', ' ').replace(',', ' ')
        normalized = normalized.replace('#', '').replace('  ', ' ').strip()
        
        # Try exact normalized match
        if normalized in self.row_label_map:
            return self.row_label_map[normalized]
        
        # Try compact version
        compact = ' '.join(normalized.split())
        if compact in self.row_label_map:
            return self.row_label_map[compact]
        
        # Try without spaces
        no_spaces = normalized.replace(' ', '')
        if no_spaces in self.row_label_map:
            return self.row_label_map[no_spaces]
        
        # Try pattern matching
        for pattern_key in ['unit', 'objective', 'anticipatory', 'instruction', 
                           'misconception', 'assessment', 'homework']:
            if pattern_key in normalized:
                if pattern_key in self.row_label_map:
                    return self.row_label_map[pattern_key]
        
        # Last resort: partial match on any key (fuzzy)
        for key, idx in self.row_label_map.items():
            # Skip pattern keys (they're short and generic)
            if key in ['unit', 'objective', 'anticipatory', 'instruction', 
                      'misconception', 'assessment', 'homework']:
                continue
            # Check if either contains the other (at least 5 chars)
            if len(key) >= 5 and len(normalized) >= 5:
                if key in normalized or normalized in key:
                    return idx
        
        return None
    
    def get_col_index(self, day: str) -> Optional[int]:
        """Get column index by day name (case-insensitive)."""
        if not day:
            return None
        
        normalized = day.strip().lower()
        return self.col_header_map.get(normalized)


class TableStructureDetector:
    """Detect and classify table structures."""
    
    # Standard row labels (case-insensitive)
    STANDARD_ROWS = [
        '',  # Row 0 (header)
        'unit, lesson #, module:',
        'objective:',
        'anticipatory set:',
        'tailored instruction:',
        'misconception:',
        'assessment:',
        'homework:'
    ]
    
    # Row label patterns for matching
    ROW_PATTERNS = {
        'unit': ['unit', 'lesson', 'module'],
        'objective': ['objective', 'essential question', 'learning goal'],
        'anticipatory': ['anticipatory set', 'warm-up', 'do now', 'hook'],
        'instruction': ['tailored instruction', 'instruction', 'teaching', 'activity', 'procedure'],
        'misconception': ['misconception', 'common error'],
        'assessment': ['assessment', 'check for understanding', 'evaluate', 'exit ticket'],
        'homework': ['homework', 'independent practice', 'extension', 'assignment']
    }
    
    def detect_structure(self, table) -> StructureMetadata:
        """
        Detect table structure and return metadata.
        
        Args:
            table: python-docx Table object
        
        Returns:
            StructureMetadata with structure info and mappings
        """
        
        if not table or not table.rows:
            return self._create_unknown_structure(table)
        
        num_rows = len(table.rows)
        num_cols = len(table.rows[0].cells) if table.rows else 0
        
        # Extract row labels
        row_labels = [
            row.cells[0].text.strip().lower() if row.cells else ""
            for row in table.rows
        ]
        
        # Extract column headers
        col_headers = [
            cell.text.strip() for cell in table.rows[0].cells
        ] if table.rows else []
        
        # Check for standard 8x6
        if num_rows == 8 and num_cols == 6:
            if self._matches_standard_rows(row_labels):
                return self._create_standard_8x6(row_labels, col_headers)
        
        # Check for 9x6 with Day row
        if num_rows == 9 and num_cols == 6:
            if row_labels[0] == 'day':
                return self._create_with_day_row(row_labels, col_headers)
        
        # Check for 13x6 extended
        if num_rows == 13 and num_cols == 6:
            return self._create_extended_13x6(row_labels, col_headers)
        
        # Unknown structure - create adaptive mapping
        return self._create_adaptive_structure(row_labels, col_headers)
    
    def _matches_standard_rows(self, row_labels: List[str]) -> bool:
        """Check if row labels match standard pattern."""
        if len(row_labels) < len(self.STANDARD_ROWS):
            return False
        
        for i, expected in enumerate(self.STANDARD_ROWS):
            if expected and row_labels[i] != expected:
                return False
        
        return True
    
    def _create_standard_8x6(self, row_labels, col_headers) -> StructureMetadata:
        """Create metadata for standard 8x6 structure."""
        return StructureMetadata(
            structure_type="standard_8x6",
            num_rows=8,
            num_cols=6,
            row_offset=0,
            has_day_row=False,
            row_label_map=self._build_row_map(row_labels),
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_with_day_row(self, row_labels, col_headers) -> StructureMetadata:
        """Create metadata for 9x6 with Day row."""
        return StructureMetadata(
            structure_type="with_day_row_9x6",
            num_rows=9,
            num_cols=6,
            row_offset=1,  # All content rows shifted by 1
            has_day_row=True,
            row_label_map=self._build_row_map(row_labels[1:]),  # Skip Day row
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_extended_13x6(self, row_labels, col_headers) -> StructureMetadata:
        """Create metadata for 13x6 extended structure."""
        return StructureMetadata(
            structure_type="extended_13x6",
            num_rows=13,
            num_cols=6,
            row_offset=0,
            has_day_row=False,
            row_label_map=self._build_row_map(row_labels),
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_adaptive_structure(self, row_labels, col_headers) -> StructureMetadata:
        """Create adaptive metadata for unknown structure."""
        return StructureMetadata(
            structure_type="adaptive",
            num_rows=len(row_labels),
            num_cols=len(col_headers),
            row_offset=0,
            has_day_row=False,
            row_label_map=self._build_row_map(row_labels),
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_unknown_structure(self, table) -> StructureMetadata:
        """Create metadata for unknown/invalid structure."""
        return StructureMetadata(
            structure_type="unknown",
            num_rows=0,
            num_cols=0,
            row_offset=0,
            has_day_row=False,
            row_label_map={},
            col_header_map={}
        )
    
    def _build_row_map(self, row_labels: List[str]) -> Dict[str, int]:
        """Build mapping from row label to index with aggressive normalization."""
        row_map = {}
        
        for idx, label in enumerate(row_labels):
            if label:
                # Aggressive normalization: lowercase, strip, remove punctuation
                normalized = label.strip().lower()
                normalized = normalized.rstrip(':').rstrip(',').rstrip('.')
                
                # Remove common separators and collapse whitespace
                normalized = normalized.replace('/', ' ').replace('&', ' ').replace(',', ' ')
                normalized = normalized.replace('#', '').replace('  ', ' ').strip()
                
                # Store exact normalized label
                row_map[normalized] = idx
                
                # Store compact version (single spaces only)
                compact = ' '.join(normalized.split())
                if compact != normalized:
                    row_map[compact] = idx
                
                # Store without spaces for fuzzy matching
                no_spaces = normalized.replace(' ', '')
                if len(no_spaces) > 3:  # Avoid too-short keys
                    row_map[no_spaces] = idx
                
                # Also store pattern-based keys
                for pattern_key, patterns in self.ROW_PATTERNS.items():
                    if any(p in normalized for p in patterns):
                        row_map[pattern_key] = idx
                        break  # Only match first pattern
        
        return row_map
    
    def _build_col_map(self, col_headers: List[str]) -> Dict[str, int]:
        """Build mapping from day name to column index."""
        col_map = {}
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        for idx, header in enumerate(col_headers):
            header_lower = header.lower()
            
            # Extract day name (ignore dates)
            for day in days:
                if day in header_lower:
                    col_map[day] = idx
                    break
        
        return col_map
