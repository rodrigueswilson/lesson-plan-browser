"""Test week number calculation."""
import pytest
from datetime import datetime


def test_week_of_first_date_parsing():
    """Parse first date from week range and compute ISO week number."""
    # Format: "MM/DD-MM/DD" (e.g. week of 10/20 to 10/24)
    week_of = "10/20-10/24"
    first_date = week_of.split("-")[0].strip()
    assert first_date == "10/20"

    month, day = map(int, first_date.split("/"))
    assert month == 10
    assert day == 20

    year = datetime.now().year
    date_obj = datetime(year, month, day)
    week_num = date_obj.isocalendar()[1]
    assert 1 <= week_num <= 53


def test_week_number_from_date():
    """ISO week number from explicit date."""
    date_obj = datetime(2025, 10, 20)
    week_num = date_obj.isocalendar()[1]
    assert week_num == 43
