import { ScheduleEntry } from '@lesson-api';

export const normalizeSubject = (subject?: string | null): string =>
  (subject ?? '').replace(/\s+/g, ' ').trim().toUpperCase();

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
