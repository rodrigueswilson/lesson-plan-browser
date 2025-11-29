export interface LessonPlanContext {
  dayData: Record<string, any> | null;
  slotData: Record<string, any> | null;
}

function normalizeDay(day?: string | null): string | null {
  if (!day) {
    return null;
  }
  return day.trim().toLowerCase();
}

function normalizeSlot(slot?: number | string | null): number | null {
  if (slot === undefined || slot === null) {
    return null;
  }
  const asNumber = Number(slot);
  return Number.isNaN(asNumber) ? null : asNumber;
}

export function extractLessonPlanContext(
  lessonJson: any,
  day?: string | null,
  slot?: number | string | null
): LessonPlanContext | null {
  if (!lessonJson || typeof lessonJson !== 'object') {
    return null;
  }

  const normalizedDay = normalizeDay(day);
  if (!normalizedDay) {
    return null;
  }

  const days = lessonJson.days;
  if (!days || typeof days !== 'object') {
    return null;
  }

  const dayData = days[normalizedDay];
  if (!dayData || typeof dayData !== 'object') {
    return { dayData: null, slotData: null };
  }

  const normalizedSlot = normalizeSlot(slot);
  const slots = Array.isArray(dayData.slots) ? dayData.slots : [];
  let slotData: Record<string, any> | null = null;

  if (slots.length > 0) {
    if (normalizedSlot !== null) {
      slotData =
        slots.find((s: any) => {
          if (!s || typeof s !== 'object') {
            return false;
          }
          const slotNumber = normalizeSlot(s.slot_number);
          return slotNumber !== null && slotNumber === normalizedSlot;
        }) || null;
    }

    if (!slotData) {
      slotData = slots[0] || null;
    }
  }

  return {
    dayData,
    slotData,
  };
}

