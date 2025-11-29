/**
 * Utility functions for formatting names and dates.
 */

/**
 * Build teacher name as "Primary First Last / Bilingual First Last"
 */
export function buildTeacherName(
  primaryFirst: string,
  primaryLast: string,
  bilingualFirst: string,
  bilingualLast: string
): string {
  const primary = `${primaryFirst || ''} ${primaryLast || ''}`.trim();
  const bilingual = `${bilingualFirst || ''} ${bilingualLast || ''}`.trim();
  
  if (primary && bilingual) {
    return `${primary} / ${bilingual}`;
  } else if (primary) {
    return primary;
  } else if (bilingual) {
    return bilingual;
  } else {
    return 'Unknown';
  }
}

/**
 * Format week dates to MM/DD-MM/DD format.
 * 
 * Handles various input formats:
 * - "10-27-10-31" → "10/27-10/31"
 * - "10/27-10/31" → "10/27-10/31"
 * - "Week of 10/27-10/31" → "10/27-10/31"
 */
export function formatWeekDates(weekOf: string): string {
  if (!weekOf) return '';
  
  // Remove common prefixes
  let cleaned = weekOf.replace(/Week of/i, '').trim();
  
  // Remove spaces and normalize
  cleaned = cleaned.replace(/\s+/g, '').replace(/to/i, '-');
  
  // Try to extract dates
  const datePattern = /(\d{1,2})[/-](\d{1,2})(?:[/-]\d{4})?/g;
  const matches = [...cleaned.matchAll(datePattern)];
  
  if (matches.length >= 2) {
    const [, startMonth, startDay] = matches[0];
    const [, endMonth, endDay] = matches[1];
    return `${startMonth}/${startDay}-${endMonth}/${endDay}`;
  }
  
  // Fallback: try "10-27-10-31" format
  const parts = cleaned.split('-');
  if (parts.length === 4 && parts.every(p => /^\d+$/.test(p))) {
    return `${parts[0]}/${parts[1]}-${parts[2]}/${parts[3]}`;
  }
  
  return weekOf;
}
