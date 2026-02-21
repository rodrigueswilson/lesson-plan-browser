import { ScheduleEntry } from '@lesson-api';

const MEETING_SUBJECTS = [
  'PLC',
  'PLC MEETING',
  'PROFESSIONAL LEARNING COMMUNITY',
  'GLM',
  'GRADE LEVEL MEETING',
  'GRADE LEVEL MEETINGS',
];

/** Green non-class periods; never treat these as meetings (they must stay green). */
const GREEN_NON_CLASS = [
  'PREP',
  'PREP TIME',
  'LUNCH',
  'A.M. ROUTINE',
  'A. M. ROUTINE',
  'AM ROUTINE',
  'MORNING ROUTINE',
  'DISMISSAL',
];

function normalizeSubjectForMatch(subject?: string | null): string {
  return (subject ?? '')
    .replace(/\uFEFF/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase();
}

export function isMeetingPeriod(subject?: string | null): boolean {
  if (!subject) return false;
  const n = normalizeSubjectForMatch(subject);
  if (GREEN_NON_CLASS.includes(n)) return false;
  return MEETING_SUBJECTS.includes(n) ||
    n === 'PLC' ||
    n === 'GLM' ||
    (n.includes('PLC') && n.includes('MEETING')) ||
    (n.includes('GRADE') && n.includes('LEVEL') && n.includes('MEETING')) ||
    n.includes('PROFESSIONAL LEARNING') ||
    n.startsWith('GLM') ||
    n.startsWith('PLC');
}

const AM_ROUTINE_PATTERN = /^A\.?\s*M\.?\s*ROUTINE$/;

/**
 * True if this subject is a non-class period (no lesson plan): Lunch, Dismissal, PREP,
 * A.M. Routine, or any meeting (PLC, GLM, etc.). Single source of truth for "do not open lesson".
 */
export function isNonClassPeriod(subject?: string | null): boolean {
  if (!subject) return false;
  const n = normalizeSubjectForMatch(subject);
  if (GREEN_NON_CLASS.includes(n)) return true;
  if (AM_ROUTINE_PATTERN.test(n)) return true;
  return isMeetingPeriod(subject);
}

/**
 * Format schedule entry display to match the schedule cell: "Subject (grade) homeroom".
 * For meetings (PLC, GLM) and lessons, include grade and homeroom when present.
 * For other non-class periods (PREP, Lunch, etc.), show only subject.
 */
export function formatEntryDisplay(
  subject: string | null | undefined,
  grade: string | null | undefined,
  homeroom: string | null | undefined,
  showGradeAndHomeroom: boolean
): string {
  if (!subject) return '';
  if (!showGradeAndHomeroom) return subject.trim();
  const parts = [subject.trim()];
  if (grade?.trim()) parts.push(`(${grade.trim()})`);
  if (homeroom?.trim()) parts.push(homeroom.trim());
  return parts.join(' ');
}

export const normalizeSubject = (subject?: string | null): string =>
  (() => {
    const normalized = (subject ?? '').replace(/\s+/g, ' ').trim().toUpperCase();

    // Normalize common abbreviations/typos to improve matching stability
    // (e.g., schedule entry subject "Mat" should match plan slot "Math").
    if (normalized === 'MAT' || normalized === 'MATHS') return 'MATH';

    return normalized;
  })();

const trimSubject = (subject?: string | null): string =>
  (subject ?? '').replace(/\s+/g, ' ').trim();

const selectPreferredEntry = (entries: ScheduleEntry[]): ScheduleEntry => {
  if (entries.length === 1) {
    const entry = entries[0];
    return { ...entry, subject: trimSubject(entry.subject) };
  }

  const subjectCounts = new Map<string, number>();
  entries.forEach((entry) => {
    const normalized = normalizeSubject(entry.subject);
    subjectCounts.set(normalized, (subjectCounts.get(normalized) || 0) + 1);
  });

  let preferredSubject = '';
  let preferredCount = -1;
  subjectCounts.forEach((count, subject) => {
    if (count > preferredCount || (count === preferredCount && subject < preferredSubject)) {
      preferredSubject = subject;
      preferredCount = count;
    }
  });

  const matchingEntries = entries.filter(
    (entry) => normalizeSubject(entry.subject) === preferredSubject
  );

  const preferredExactCase = matchingEntries.find(
    (entry) => trimSubject(entry.subject) === preferredSubject
  );

  const preferredInsensitive = matchingEntries.find(
    (entry) => trimSubject(entry.subject).toUpperCase() === preferredSubject
  );

  const fallbackSubject = matchingEntries
    .map((entry) => trimSubject(entry.subject))
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b))[0] || preferredSubject;

  const chosen = preferredExactCase ?? preferredInsensitive ?? matchingEntries[0];
  const subject = trimSubject(preferredExactCase?.subject ?? preferredInsensitive?.subject ?? fallbackSubject) || fallbackSubject;

  return {
    ...chosen,
    subject,
  };
};

export const dedupeScheduleEntries = (entries: ScheduleEntry[]): ScheduleEntry[] => {
  if (!entries || entries.length === 0) {
    return [];
  }

  const groups = new Map<string, ScheduleEntry[]>();

  entries.forEach((entry) => {
    const key = `${entry.day_of_week}-${entry.start_time}-${entry.end_time}-${entry.slot_number}-${entry.grade || ''}-${entry.homeroom || ''}`;
    if (!groups.has(key)) {
      groups.set(key, [entry]);
    } else {
      groups.get(key)!.push(entry);
    }
  });

  const result: ScheduleEntry[] = [];
  groups.forEach((group) => {
    result.push(selectPreferredEntry(group));
  });

  return result;
};

export const areScheduleEntriesEquivalent = (
  entryA: ScheduleEntry,
  entryB: ScheduleEntry
): boolean => {
  return (
    entryA.day_of_week === entryB.day_of_week &&
    entryA.start_time === entryB.start_time &&
    entryA.end_time === entryB.end_time &&
    entryA.slot_number === entryB.slot_number &&
    (entryA.grade || '') === (entryB.grade || '') &&
    (entryA.homeroom || '') === (entryB.homeroom || '') &&
    normalizeSubject(entryA.subject) === normalizeSubject(entryB.subject)
  );
};
