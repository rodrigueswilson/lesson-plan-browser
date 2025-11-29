import { ScheduleEntry } from '@lesson-api';
import { normalizeSubject } from './scheduleEntries';

interface PlanSlotMatch {
  planSlotIndex: number;
  planSlotData: any;
}

interface PlanSlotMatchOptions {
  disableFallback?: boolean;
}

const isArray = (value: any): value is any[] => Array.isArray(value);

export const findPlanSlotForEntry = (
  dayData: any,
  scheduleEntry: ScheduleEntry,
  options: PlanSlotMatchOptions = {}
): PlanSlotMatch | null => {
  if (!dayData?.slots || !isArray(dayData.slots)) {
    return null;
  }

  const slots: any[] = dayData.slots;
  const isAvailable = (_idx: number) => true; // Always available - allow co-teaching scenarios

  // Helper to check if subjects are compatible (handles co-teaching scenarios)
  const subjectsMatch = (slotSubject: string, entrySubject: string): boolean => {
    const normalized1 = normalizeSubject(slotSubject);
    const normalized2 = normalizeSubject(entrySubject);

    if (normalized1 === normalized2) return true;

    // Handle co-teaching: ELA/SS matches with both ELA and Social Studies
    const combined = normalized1.toUpperCase();
    const entry = normalized2.toUpperCase();

    if (combined.includes('ELA') && combined.includes('SS')) {
      return entry.includes('ELA') || entry.includes('SOCIAL');
    }

    return false;
  };

  // Helper to calculate subject specificity (higher = more specific)
  const getSubjectSpecificity = (subject: string): number => {
    if (!subject) return 0;
    // Compound subjects like "ELA/SS" are more specific than simple "ELA"
    const hasSlash = subject.includes('/') || subject.includes('\\');
    const parts = hasSlash ? subject.split(/[\/\\]/).length : 1;
    return parts;
  };

  const normalizedEntrySubject = normalizeSubject(scheduleEntry.subject || '');

  const matchers = [
    // 1. Best match: Subject + Grade + Homeroom + Time (if all present)
    (slot: any, idx: number) =>
      subjectsMatch(slot?.subject || '', scheduleEntry.subject) &&
      slot?.grade === scheduleEntry.grade &&
      slot?.homeroom === scheduleEntry.homeroom &&
      slot?.start_time === scheduleEntry.start_time &&
      slot?.end_time === scheduleEntry.end_time &&
      isAvailable(idx),
    // 2. Subject + Grade + Homeroom (when lesson plan lacks time)
    (slot: any, idx: number) =>
      subjectsMatch(slot?.subject || '', scheduleEntry.subject) &&
      (!slot?.grade || slot.grade === scheduleEntry.grade) &&
      (!slot?.homeroom || slot.homeroom === scheduleEntry.homeroom) &&
      isAvailable(idx),
    // 3. Subject + Time (when grade/homeroom might be generic)
    (slot: any, idx: number) =>
      subjectsMatch(slot?.subject || '', scheduleEntry.subject) &&
      slot?.start_time === scheduleEntry.start_time &&
      slot?.end_time === scheduleEntry.end_time &&
      isAvailable(idx),
    // 4. Subject match only (Last resort for subject alignment)
    (slot: any, idx: number) =>
      subjectsMatch(slot?.subject || '', scheduleEntry.subject) &&
      isAvailable(idx),
  ];

  for (const matcher of matchers) {
    // Find ALL matches, not just the first one
    const matchIndices: number[] = [];
    slots.forEach((slot, idx) => {
      if (matcher(slot, idx)) {
        matchIndices.push(idx);
      }
    });

    if (matchIndices.length > 0) {
      // Prefer exact subject matches first
      const exactMatchIdx = matchIndices.find(
        (idx) => normalizeSubject(slots[idx]?.subject || '') === normalizedEntrySubject
      );

      if (exactMatchIdx !== undefined) {
        return {
          planSlotIndex: exactMatchIdx,
          planSlotData: slots[exactMatchIdx],
        };
      }

      // If multiple matches, prefer the most specific subject
      // (e.g., "ELA/SS" over "ELA")
      let bestIdx = matchIndices[0];
      let bestSpecificity = getSubjectSpecificity(slots[bestIdx]?.subject || '');

      for (const idx of matchIndices) {
        const specificity = getSubjectSpecificity(slots[idx]?.subject || '');
        if (specificity > bestSpecificity) {
          bestIdx = idx;
          bestSpecificity = specificity;
        }
      }

      return {
        planSlotIndex: bestIdx,
        planSlotData: slots[bestIdx],
      };
    }
  }

  if (options.disableFallback) {
    return null;
  }

  const fallbackIndex = slots.findIndex((_, idx) => isAvailable(idx));
  if (fallbackIndex !== -1) {
    return {
      planSlotIndex: fallbackIndex,
      planSlotData: slots[fallbackIndex],
    };
  }

  return null;
};

const buildTailoredInstruction = (slot: any): string | undefined => {
  if (!slot) {
    return undefined;
  }

  const tailored = slot.tailored_instruction || {};

  if (tailored.original_content) {
    const firstSentence = tailored.original_content
      .split(/\n+/)
      .map((line: string) => line.trim())
      .filter(Boolean)[0];
    if (firstSentence) {
      return firstSentence.length > 160 ? `${firstSentence.slice(0, 157)}…` : firstSentence;
    }
  }

  if (tailored.co_teaching_model?.model_name) {
    return `Co-Teaching: ${tailored.co_teaching_model.model_name}`;
  }

  if (isArray(tailored.ell_support) && tailored.ell_support.length > 0) {
    const names = tailored.ell_support
      .map((support: any) => (typeof support === 'string' ? support : support?.strategy_name))
      .filter(Boolean);

    if (names.length > 0) {
      const preview = names.slice(0, 2).join(', ');
      return names.length > 2 ? `ELL Support: ${preview}…` : `ELL Support: ${preview}`;
    }

    return `ELL Support: ${tailored.ell_support.length} strategies`;
  }

  if (isArray(tailored.materials) && tailored.materials.length > 0) {
    const preview = tailored.materials.slice(0, 2).join(', ');
    return tailored.materials.length > 2 ? `Materials: ${preview}…` : `Materials: ${preview}`;
  }

  return undefined;
};

export const buildSlotDataMap = (
  dayData: any,
  lessons: ScheduleEntry[]
): Record<number, {
  studentGoal?: string;
  widaObjective?: string;
  tailoredInstruction?: string;
  planSlotNumber?: number;
  planSlotIndex?: number;
  planSlot?: any;
}> => {
  const slotData: Record<number, any> = {};
  const groupAssignments: Record<string, any> = {};
  if (!dayData?.slots || !isArray(dayData.slots) || lessons.length === 0) {
    return slotData;
  }

  // NOTE: We no longer track usedIndices because co-teaching scenarios
  // require multiple schedule entries to map to the same lesson plan slot
  // (e.g., ELA and Social S. both map to ELA/SS)

  lessons.forEach((lesson) => {
    const groupKey = lesson.plan_slot_group_id?.trim().toLowerCase();
    // Try to find a match WITHOUT fallback first
    let match = findPlanSlotForEntry(dayData, lesson, { disableFallback: true });

    // If no match, try with fallback
    if (!match) {
      match = findPlanSlotForEntry(dayData, lesson, { disableFallback: false });
    }

    if (!match && groupKey && groupAssignments[groupKey]) {
      slotData[lesson.slot_number] = { ...groupAssignments[groupKey] };
      return;
    }

    if (match) {
      const slot = match.planSlotData || {};
      const objective = slot.objective || {};

      const slotInfo = {
        studentGoal: objective.student_goal,
        widaObjective: objective.wida_objective,
        tailoredInstruction: buildTailoredInstruction(slot),
        planSlotNumber: slot.slot_number,
        planSlotIndex: match.planSlotIndex,
        planSlot: slot,
      };
      slotData[lesson.slot_number] = slotInfo;

      if (groupKey) {
        groupAssignments[groupKey] = slotInfo;
      }
    }
  });

  return slotData;
};
