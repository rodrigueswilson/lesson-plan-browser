import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatWeekOf(weekString: string): string {
  // Convert "10-06-10-10" to "Week of Oct 6 - Oct 10"
  const parts = weekString.split('-');
  if (parts.length === 4) {
    const [month1, day1, month2, day2] = parts;
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const m1 = monthNames[parseInt(month1) - 1];
    const m2 = monthNames[parseInt(month2) - 1];
    return `Week of ${m1} ${parseInt(day1)} - ${m2} ${parseInt(day2)}`;
  }
  return weekString;
}

export const SUBJECTS = [
  'ELA',
  'Math',
  'Science',
  'Social Studies',
  'ELA/SS',
  'Science/Health',
  'Art',
  'Music',
  'PE',
  'Other',
];

export const GRADES = [
  'K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'
];

export const PROFICIENCY_LEVELS = [
  'Entering (Level 1)',
  'Emerging (Level 2)',
  'Developing (Level 3)',
  'Expanding (Level 4)',
  'Bridging (Level 5)',
  'Reaching (Level 6)',
];
