"""Row/column index helpers for the daily plans table using structure metadata."""


def get_row_index(renderer, label: str) -> int:
    """Get row index for a given label using structure metadata."""
    if renderer.structure_metadata:
        idx = renderer.structure_metadata.get_row_index(label)
        if idx is not None:
            return idx + renderer.structure_metadata.row_offset
    return -1


def get_col_index(renderer, day: str) -> int:
    """Get column index for a given day using structure metadata."""
    if renderer.structure_metadata:
        idx = renderer.structure_metadata.get_col_index(day)
        return idx if idx is not None else -1
    return -1
