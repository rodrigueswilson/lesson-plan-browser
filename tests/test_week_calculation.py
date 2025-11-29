"""Test week number calculation."""
from datetime import datetime

week_of = "10-20-10-24"

# Parse first date from range
first_date = week_of.split("-")[0].strip()
print(f"First date: {first_date}")

month, day = map(int, first_date.split("/"))
print(f"Month: {month}, Day: {day}")

# Create date object (use current year)
year = datetime.now().year
date_obj = datetime(year, month, day)
print(f"Date object: {date_obj}")

# Calculate week number (ISO week)
week_num = date_obj.isocalendar()[1]
print(f"ISO Week: {week_num}")
