import type { LessonStep } from '@lesson-api';

/**
 * Creates default lesson steps when phase_plan is not available.
 * Provides a traditional 45-minute lesson structure:
 * - Warmup: 5 minutes
 * - Input: 15 minutes
 * - Practice: 20 minutes
 * - Closure: 5 minutes
 */
export function createDefaultLessonSteps(
  planId: string,
  day: string,
  slot: number
): LessonStep[] {
  const now = new Date().toISOString();
  let startTimeOffset = 0; // minutes from lesson start

  const steps: LessonStep[] = [
    {
      id: `default-${planId}-${day}-${slot}-1`,
      lesson_plan_id: planId,
      day_of_week: day,
      slot_number: slot,
      step_number: 1,
      step_name: 'Warmup',
      duration_minutes: 5,
      start_time_offset: startTimeOffset,
      content_type: 'instruction',
      display_content: 'Warmup Activity\n\nEngage students with a brief activity to activate prior knowledge and prepare them for the lesson.',
      created_at: now,
      updated_at: now,
    },
    {
      id: `default-${planId}-${day}-${slot}-2`,
      lesson_plan_id: planId,
      day_of_week: day,
      slot_number: slot,
      step_number: 2,
      step_name: 'Input',
      duration_minutes: 15,
      start_time_offset: (startTimeOffset += 5),
      content_type: 'instruction',
      display_content: 'Input/Instruction\n\nPresent new content, concepts, or skills to students. This is the main teaching phase of the lesson.',
      created_at: now,
      updated_at: now,
    },
    {
      id: `default-${planId}-${day}-${slot}-3`,
      lesson_plan_id: planId,
      day_of_week: day,
      slot_number: slot,
      step_number: 3,
      step_name: 'Practice',
      duration_minutes: 20,
      start_time_offset: (startTimeOffset += 15),
      content_type: 'instruction',
      display_content: 'Guided and Independent Practice\n\nStudents practice the new skills or concepts with teacher support and then independently.',
      created_at: now,
      updated_at: now,
    },
    {
      id: `default-${planId}-${day}-${slot}-4`,
      lesson_plan_id: planId,
      day_of_week: day,
      slot_number: slot,
      step_number: 4,
      step_name: 'Closure',
      duration_minutes: 5,
      start_time_offset: (startTimeOffset += 20),
      content_type: 'assessment',
      display_content: 'Closure\n\nWrap up the lesson by reviewing key concepts, checking for understanding, and preparing for the next lesson.',
      created_at: now,
      updated_at: now,
    },
  ];

  return steps;
}

