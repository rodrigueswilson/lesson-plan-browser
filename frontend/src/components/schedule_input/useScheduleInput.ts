import { useState, useEffect, useMemo } from 'react';
import { scheduleApi, ScheduleEntryCreate } from '@lesson-api';
import { useStore } from '@lesson-browser';

export interface ScheduleCell {
  subject: string;
  grade: string | null;
  homeroom: string | null;
  plan_slot_group_id?: string | null;
}

export interface ScheduleRow {
  start_time: string;
  end_time: string;
  monday: ScheduleCell | null;
  tuesday: ScheduleCell | null;
  wednesday: ScheduleCell | null;
  thursday: ScheduleCell | null;
  friday: ScheduleCell | null;
}

export type Weekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';

export const DAY_KEYS: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
export const DAY_LABELS: Record<Weekday, string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
};

export const DEFAULT_TIME_SLOTS = [
  { start: '08:15', end: '08:30' },
  { start: '08:30', end: '09:15' },
  { start: '09:18', end: '10:03' },
  { start: '10:06', end: '10:51' },
  { start: '10:54', end: '11:39' },
  { start: '11:42', end: '12:27' },
  { start: '12:30', end: '13:15' },
  { start: '13:18', end: '14:03' },
  { start: '14:06', end: '15:00' },
  { start: '15:00', end: '15:05' },
];

export interface ConflictDetail {
  id: string;
  entries: Array<{ day: Weekday; time: string; subject: string | null }>;
}

export function useScheduleInput() {
  const { currentUser } = useStore();
  const [scheduleData, setScheduleData] = useState<ScheduleRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const initializeSchedule = () => {
    const rows: ScheduleRow[] = DEFAULT_TIME_SLOTS.map((slot) => ({
      start_time: slot.start,
      end_time: slot.end,
      monday: null,
      tuesday: null,
      wednesday: null,
      thursday: null,
      friday: null,
    }));
    setScheduleData(rows);
  };

  useEffect(() => {
    if (currentUser) {
      loadExistingSchedule();
    } else {
      initializeSchedule();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser?.id]);

  const { existingGroups, conflictLookup, conflictDetails } = useMemo(() => {
    const groupSet = new Set<string>();
    const metadata: Record<
      string,
      {
        subject: string | null | undefined;
        grade: string | null | undefined;
        homeroom: string | null | undefined;
        conflict: boolean;
        entries: Array<{ day: Weekday; time: string; subject: string | null }>;
      }
    > = {};

    scheduleData.forEach((row) => {
      DAY_KEYS.forEach((day) => {
        const cell = row[day];
        if (!cell?.plan_slot_group_id) return;

        const id = cell.plan_slot_group_id.trim();
        if (!id) return;

        groupSet.add(id);
        if (!metadata[id]) {
          metadata[id] = {
            subject: cell.subject,
            grade: cell.grade,
            homeroom: cell.homeroom,
            conflict: false,
            entries: [],
          };
        } else {
          const meta = metadata[id];
          if (cell.subject && meta.subject && cell.subject !== meta.subject) {
            meta.conflict = true;
          } else if (!meta.subject && cell.subject) {
            meta.subject = cell.subject;
          }

          if (cell.grade && meta.grade && cell.grade !== meta.grade) {
            meta.conflict = true;
          } else if (!meta.grade && cell.grade) {
            meta.grade = cell.grade;
          }

          if (cell.homeroom && meta.homeroom && cell.homeroom !== meta.homeroom) {
            meta.conflict = true;
          } else if (!meta.homeroom && cell.homeroom) {
            meta.homeroom = cell.homeroom;
          }
        }

        metadata[id].entries.push({
          day,
          time: `${row.start_time}-${row.end_time}`,
          subject: cell.subject,
        });
      });
    });

    const existingGroups = Array.from(groupSet).sort((a, b) =>
      a.localeCompare(b, undefined, { sensitivity: 'base' })
    );

    const conflictDetails: ConflictDetail[] = Object.entries(metadata)
      .filter(([, meta]) => meta.conflict)
      .map(([id, meta]) => ({
        id,
        entries: meta.entries,
      }));

    const conflictLookup = conflictDetails.reduce<Record<string, boolean>>((acc, { id }) => {
      acc[id] = true;
      return acc;
    }, {});

    return { existingGroups, conflictLookup, conflictDetails };
  }, [scheduleData]);

  const loadExistingSchedule = async () => {
    if (!currentUser) return;

    setIsLoading(true);
    setError(null);

    try {
      const entries = await scheduleApi.getSchedule(currentUser.id);
      const entriesArray = Array.isArray(entries) ? entries : [];

      const rows: ScheduleRow[] = DEFAULT_TIME_SLOTS.map((slot) => ({
        start_time: slot.start,
        end_time: slot.end,
        monday: null,
        tuesday: null,
        wednesday: null,
        thursday: null,
        friday: null,
      }));

      console.log('[ScheduleInput] Loading entries:', entriesArray.length);
      entriesArray.forEach((entry) => {
        const rowIndex = DEFAULT_TIME_SLOTS.findIndex(
          (slot) => slot.start === entry.start_time && slot.end === entry.end_time
        );

        if (rowIndex >= 0) {
          const cell: ScheduleCell = {
            subject: entry.subject,
            grade: entry.grade,
            homeroom: entry.homeroom,
            plan_slot_group_id: entry.plan_slot_group_id || null,
          };

          const dayKey = entry.day_of_week as keyof ScheduleRow;
          if (dayKey !== 'start_time' && dayKey !== 'end_time') {
            rows[rowIndex][dayKey] = cell;
            console.log(
              `[ScheduleInput] Loaded: ${entry.day_of_week} ${entry.start_time}-${entry.end_time} = ${entry.subject}`
            );
          }
        } else {
          console.warn(`[ScheduleInput] No match found for ${entry.start_time}-${entry.end_time}`);
        }
      });

      console.log('[ScheduleInput] Final rows:', rows);

      setScheduleData(rows);
      setSuccess('Schedule loaded successfully');
      setTimeout(() => setSuccess((s) => (s === 'Schedule loaded successfully' ? null : s)), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load schedule');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCellChange = (
    rowIndex: number,
    dayOfWeek: Weekday,
    cell: ScheduleCell | null
  ) => {
    setScheduleData((prev) => {
      const updated = [...prev];
      updated[rowIndex] = {
        ...updated[rowIndex],
        [dayOfWeek]: cell,
      };
      return updated;
    });
    setError(null);
    setSuccess(null);
  };

  const handleSave = async () => {
    if (!currentUser) {
      setError('Please select a user first');
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const entries: ScheduleEntryCreate[] = [];

      scheduleData.forEach((row, rowIndex) => {
        DAY_KEYS.forEach((day) => {
          const cell = row[day];
          if (cell && cell.subject) {
            entries.push({
              user_id: currentUser.id,
              day_of_week: day,
              start_time: row.start_time,
              end_time: row.end_time,
              subject: cell.subject,
              homeroom: cell.homeroom || null,
              grade: cell.grade || null,
              slot_number: rowIndex + 1,
              is_active: true,
              plan_slot_group_id: cell.plan_slot_group_id || null,
            });
          }
        });
      });

      if (entries.length === 0) {
        setError('No schedule entries to save');
        setIsSaving(false);
        return;
      }

      const result = await scheduleApi.bulkCreate(currentUser.id, entries);

      if (result.success) {
        setSuccess(`Schedule saved successfully! ${result.created_count} entries created.`);
      } else {
        const errorMessages =
          result.errors && result.errors.length > 0
            ? result.errors.join(', ')
            : 'Unknown error occurred';
        setError(`Some entries failed to save. ${errorMessages}`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save schedule');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = () => {
    if (confirm('Are you sure you want to clear all schedule entries?')) {
      initializeSchedule();
      setError(null);
      setSuccess(null);
    }
  };

  return {
    currentUser,
    scheduleData,
    isLoading,
    isSaving,
    error,
    success,
    existingGroups,
    conflictLookup,
    conflictDetails,
    loadExistingSchedule,
    handleCellChange,
    handleSave,
    handleClear,
  };
}
