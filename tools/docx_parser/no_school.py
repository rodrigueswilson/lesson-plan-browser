"""
No-school day detection for DOCX lesson plans.
"""

import re
from typing import List


def get_no_school_patterns() -> List[str]:
    """Get regex patterns for detecting No School days."""
    return [
        r"no\s+school",
        r"no\s*-\s*school",
        r"school\s+closed",
        r"holiday",
        r"vacation\s+day",
        r"professional\s+development",
        r"staff\s+development",
        r"teacher\s+development",
        r"pd\s+day",
        r"in[-\s]?service",
        r"teacher\s+workday",
        r"planning\s+day",
        r"prep\s+day",
        r"conference\s+day",
        r"parent[-\s]teacher\s+conference",
        r"early\s+dismissal",
        r"half\s+day",
        r"early\s+release",
    ]


def is_day_no_school(day_text: str) -> bool:
    """
    Check if a specific day's content indicates 'No School'.

    Args:
        day_text: Text content for a specific day

    Returns:
        True if day is "No School", False otherwise
    """
    if not day_text or len(day_text.strip()) < 5:
        return False

    day_text_lower = day_text.lower().strip()

    specific_patterns = [
        r"^no\s+school\s*$",
        r"^no\s+school\s+[,\-\.]",
        r"^no\s*-\s*school\s*$",
        r"^holiday\s*$",
        r"^school\s+closed\s*$",
    ]

    for pattern in specific_patterns:
        if re.search(pattern, day_text_lower, re.IGNORECASE):
            return True

    if len(day_text.strip()) < 30:
        core_patterns = [
            r"no\s+school",
            r"no\s*-\s*school",
            r"school\s+closed",
            r"^holiday$",
            r"staff\s+development",
            r"professional\s+development",
            r"pd\s+day",
            r"planning\s+day",
            r"teacher\s+workday",
            r"prep\s+day",
            r"conference\s+day",
            r"in[-\s]?service",
        ]
        for pattern in core_patterns:
            if re.search(pattern, day_text_lower, re.IGNORECASE):
                return True

    if len(day_text.strip()) >= 30:
        strict_patterns = [
            r"^(no\s+school|no\s*-\s*school|school\s+closed|holiday)[\s,\-\.]",
            r"[\s,\-\.](no\s+school|no\s*-\s*school|school\s+closed|holiday)\s*$",
        ]
        for pattern in strict_patterns:
            if re.search(pattern, day_text_lower, re.IGNORECASE):
                if day_text_lower.count('.') <= 1 and day_text_lower.count(',') <= 2:
                    return True

    return False
