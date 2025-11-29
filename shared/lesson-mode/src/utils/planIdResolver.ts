import { ScheduleEntry, WeeklyPlan, planApi, lessonApi } from '@lesson-api';

/**
 * Resolves the plan ID for a schedule entry based on week context.
 * Finds the plan that matches the schedule entry's week and other criteria.
 */
export async function resolvePlanIdFromScheduleEntry(
  scheduleEntry: ScheduleEntry,
  userId: string,
  plans?: WeeklyPlan[]
): Promise<{ planId: string; day: string; slot: number } | null> {
  try {
    // If plans not provided, fetch them
    let availablePlans = plans;
    if (!availablePlans) {
      const response = await planApi.list(userId, 100, userId);
      availablePlans = response.data || [];
    }

    if (!availablePlans || availablePlans.length === 0) {
      return null;
    }

    // Get the current week based on the schedule entry's day
    const currentWeekOf = getWeekOfForDay(scheduleEntry.day_of_week);

    // Try to find a plan that matches the week
    // First, try exact match with current week
    let matchingPlan = availablePlans.find(p => p.week_of === currentWeekOf);

    // If no exact match, try to find the most recent plan for that week
    if (!matchingPlan) {
      // Find plans that could match (same week format pattern)
      const candidatePlans = availablePlans.filter(p => {
        if (!p.week_of) return false;
        // Check if week_of overlaps with current week
        return weeksOverlap(p.week_of, currentWeekOf);
      });

      if (candidatePlans.length > 0) {
        // Sort by week_of descending (most recent first)
        candidatePlans.sort((a, b) => {
          if (!a.week_of || !b.week_of) return 0;
          return b.week_of.localeCompare(a.week_of);
        });
        matchingPlan = candidatePlans[0];
      }
    }

    // If still no match, use the most recent plan as fallback
    if (!matchingPlan) {
      const sortedPlans = [...availablePlans].sort((a, b) => {
        if (!a.week_of || !b.week_of) return 0;
        return b.week_of.localeCompare(a.week_of);
      });
      matchingPlan = sortedPlans[0];
    }

    if (!matchingPlan) {
      return null;
    }

    // Verify the plan has data for the required day and slot
    try {
      const planDetail = await lessonApi.getPlanDetail(matchingPlan.id, userId);
      if (planDetail.data && planDetail.data.lesson_json) {
        const dayData = planDetail.data.lesson_json.days?.[scheduleEntry.day_of_week];
        if (dayData && dayData.slots) {
          // Find the matching slot in the plan
          const matchingSlot = findMatchingSlot(dayData.slots, scheduleEntry);
          if (matchingSlot !== null) {
            return {
              planId: matchingPlan.id,
              day: scheduleEntry.day_of_week,
              slot: matchingSlot.slot_number || scheduleEntry.slot_number,
            };
          }
        }
      }
    } catch (err) {
      console.error('Failed to verify plan detail:', err);
      // Still return the plan ID even if verification fails
      return {
        planId: matchingPlan.id,
        day: scheduleEntry.day_of_week,
        slot: scheduleEntry.slot_number,
      };
    }

    return {
      planId: matchingPlan.id,
      day: scheduleEntry.day_of_week,
      slot: scheduleEntry.slot_number,
    };
  } catch (error) {
    console.error('Failed to resolve plan ID from schedule entry:', error);
    return null;
  }
}

/**
 * Gets the week_of format for a given day of the week.
 * Returns format like "MM/DD-MM/DD" representing the week containing that day.
 */
function getWeekOfForDay(dayOfWeek: string): string {
  const now = new Date();
  const dayIndex = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'].indexOf(dayOfWeek.toLowerCase());
  
  if (dayIndex === -1) {
    // Default to current date
    return formatWeekOf(now);
  }

  // Find the Monday of the week containing this day
  const currentDayIndex = now.getDay();
  const daysUntilMonday = (currentDayIndex + 7 - 1) % 7; // Monday is day 1
  const monday = new Date(now);
  monday.setDate(now.getDate() - daysUntilMonday);
  
  // Adjust if we're looking at a specific day
  const targetDayIndex = (dayIndex === 0 ? 7 : dayIndex); // Sunday = 7
  const daysDifference = (targetDayIndex - 1) - (currentDayIndex === 0 ? 7 : currentDayIndex);
  const targetDate = new Date(now);
  targetDate.setDate(now.getDate() + daysDifference);
  
  // Find Monday of the week containing targetDate
  const targetDayOfWeek = targetDate.getDay();
  const daysToMonday = (targetDayOfWeek + 7 - 1) % 7;
  const weekMonday = new Date(targetDate);
  weekMonday.setDate(targetDate.getDate() - daysToMonday);
  
  return formatWeekOf(weekMonday);
}

/**
 * Formats a date as week_of string (MM/DD-MM/DD format).
 * Assumes the date is a Monday.
 */
function formatWeekOf(monday: Date): string {
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  
  const formatDate = (date: Date) => {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${month}/${day}`;
  };
  
  return `${formatDate(monday)}-${formatDate(sunday)}`;
}

/**
 * Checks if two week_of strings overlap (same week).
 */
function weeksOverlap(week1: string, week2: string): boolean {
  if (!week1 || !week2) return false;
  
  // Simple check: if they're the same string, they overlap
  if (week1 === week2) return true;
  
  // Try to parse and check if dates overlap
  try {
    const [start1, end1] = parseWeekOf(week1);
    const [start2, end2] = parseWeekOf(week2);
    
    if (!start1 || !end1 || !start2 || !end2) return false;
    
    // Check if ranges overlap
    return (start1 <= end2 && start2 <= end1);
  } catch {
    return false;
  }
}

/**
 * Parses a week_of string into start and end dates.
 */
function parseWeekOf(weekOf: string): [Date | null, Date | null] {
  const parts = weekOf.split('-');
  if (parts.length !== 2) return [null, null];
  
  try {
    const [month1, day1] = parts[0].split('/').map(Number);
    const [month2, day2] = parts[1].split('/').map(Number);
    
    const currentYear = new Date().getFullYear();
    const start = new Date(currentYear, month1 - 1, day1);
    const end = new Date(currentYear, month2 - 1, day2);
    
    return [start, end];
  } catch {
    return [null, null];
  }
}

/**
 * Finds the matching slot in a plan's day data for a schedule entry.
 */
function findMatchingSlot(slots: any[], scheduleEntry: ScheduleEntry): { slot_number: number } | null {
  if (!slots || !Array.isArray(slots)) {
    return null;
  }

  // Try to find exact match by slot number first
  let match = slots.find((slot, idx) => {
    const slotNum = slot.slot_number ?? idx + 1;
    return slotNum === scheduleEntry.slot_number;
  });

  if (match) {
    const slotNum = match.slot_number ?? slots.indexOf(match) + 1;
    return { slot_number: slotNum };
  }

  // Try to match by subject, grade, homeroom
  match = slots.find((slot) => {
    const subjectMatch = normalizeSubject(slot.subject || '') === normalizeSubject(scheduleEntry.subject || '');
    const gradeMatch = !slot.grade || slot.grade === scheduleEntry.grade;
    const homeroomMatch = !slot.homeroom || slot.homeroom === scheduleEntry.homeroom;
    
    return subjectMatch && gradeMatch && homeroomMatch;
  });

  if (match) {
    const slotNum = match.slot_number ?? slots.indexOf(match) + 1;
    return { slot_number: slotNum };
  }

  // Fallback to first available slot
  if (slots.length > 0) {
    const slotNum = slots[0].slot_number ?? 1;
    return { slot_number: slotNum };
  }

  return null;
}

/**
 * Normalizes subject names for matching.
 */
function normalizeSubject(subject: string): string {
  return (subject || '').trim().toUpperCase();
}
