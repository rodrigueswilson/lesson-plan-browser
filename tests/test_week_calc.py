from datetime import datetime

# Test the week calculation
week_of = "10/13-10/17"
first_date = week_of.split('-')[0].strip()
month, day = map(int, first_date.split('/'))
year = datetime.now().year
date_obj = datetime(year, month, day)
week_num = date_obj.isocalendar()[1]

print(f"Input: {week_of}")
print(f"Parsed date: {month}/{day}/{year}")
print(f"Date object: {date_obj}")
print(f"ISO Week number: {week_num}")
