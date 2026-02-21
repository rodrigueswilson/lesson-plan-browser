import { useState, useEffect, useMemo } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import { lessonApi, LessonPlanDetail, ScheduleEntry } from '@lesson-api';
import { useStore } from '../store/useStore';
import { highlightVocabularyWords, extractVocabularyWords, getCognateBadgeClasses, getCognateBadgeLabel } from '@lesson-mode/utils/vocabularyHighlight';
import { parseMarkdown } from '@lesson-mode/utils/markdownUtils';
import { LessonMetadataDisplay } from './LessonMetadataDisplay';

interface LessonDetailViewProps {
  scheduleEntry: ScheduleEntry;
  day: string;
  slot: number;
  planSlotIndex?: number;
  initialSlotData?: any;
  weekOf: string;
  onBack: () => void;
  onEnterLessonMode?: (scheduleEntry: ScheduleEntry, day?: string, slot?: number, planId?: string, previousViewMode?: 'week' | 'day' | 'lesson', weekOf?: string) => void;
  onPreviousLesson?: () => void;
  onNextLesson?: () => void;
  canGoPrevious?: boolean;
  canGoNext?: boolean;
}

export function LessonDetailView({
  scheduleEntry,
  day,
  slot,
  planSlotIndex,
  initialSlotData,
  weekOf,
  onBack,
  onEnterLessonMode,
  onPreviousLesson,
  onNextLesson,
  canGoPrevious = false,
  canGoNext = false,
}: LessonDetailViewProps) {
  const { currentUser } = useStore();
  const [lessonPlan, setLessonPlan] = useState<LessonPlanDetail | null>(null);
  const [loading, setLoading] = useState(!initialSlotData); // Start as false if we have data
  const [error, setError] = useState<string | null>(null);
  const [lessonSteps, setLessonSteps] = useState<any[]>([]);

  // CRITICAL: Log the weekOf prop received to verify it's correct
  console.log('[LessonDetailView] Component rendered with props:', {
    weekOf: weekOf,
    day: day,
    slot: slot,
    subject: scheduleEntry.subject,
    scheduleEntryWeekOf: scheduleEntry.week_of,
    note: 'This weekOf will be used to find the plan'
  });

  useEffect(() => {
    const loadLessonPlan = async () => {
      if (!currentUser) {
        setError('No user selected');
        setLoading(false);
        return;
      }

      try {
        console.log('[LessonDetailView] Loading lesson plan with weekOf:', weekOf, 'day:', day, 'slot:', slot);

        // Find plan for this week
        const { planApi } = await import('@lesson-api');
        const plansResponse = await planApi.list(currentUser.id, 100, currentUser.id); // Increased limit
        const plans = plansResponse.data || [];

        // Normalize weekOf for comparison (handle both dash and slash formats)
        const normalizeWeek = (week: string) => {
          if (!week) return '';
          // Replace slashes with dashes for consistent comparison
          return week.replace(/\//g, '-');
        };

        const normalizedWeekOf = normalizeWeek(weekOf);
        console.log('[LessonDetailView] Normalized weekOf:', normalizedWeekOf, 'Available plans:', plans.map(p => p.week_of));

        // Try exact match first
        let plan = plans.find(p => p.week_of === weekOf);
        let matchMethod = plan ? 'exact' : null;

        // If not found, try normalized comparison (handles slash vs dash)
        if (!plan) {
          plan = plans.find(p => normalizeWeek(p.week_of) === normalizedWeekOf);
          matchMethod = plan ? 'normalized' : null;
        }

        // If still not found, try reverse normalization (handle both formats)
        if (!plan) {
          const reverseNormalize = (week: string) => week.replace(/-/g, '/');
          const reverseNormalized = reverseNormalize(weekOf);
          plan = plans.find(p => {
            const pNormalized = reverseNormalize(p.week_of);
            return normalizeWeek(pNormalized) === normalizedWeekOf || pNormalized === reverseNormalized;
          });
          matchMethod = plan ? 'reverse_normalized' : null;
        }

        // Detailed logging for debugging
        console.log('[LessonDetailView] Plan matching result:', {
          requestedWeekOf: weekOf,
          normalizedWeekOf: normalizedWeekOf,
          matchMethod: matchMethod,
          found: plan ? 'YES' : 'NO',
          matchedPlanId: plan?.id,
          matchedPlanWeekOf: plan?.week_of,
          allAvailableWeeks: plans.map(p => ({
            id: p.id,
            week_of: p.week_of,
            normalized: normalizeWeek(p.week_of)
          }))
        });

        if (!plan) {
          console.warn('[LessonDetailView] No plan found for week:', weekOf, 'Available weeks:', plans.map(p => p.week_of));
          setError('No lesson plan found for this week');
          setLoading(false);
          return;
        }

        // Check if plan has lesson_json
        if (!plan.lesson_json) {
          console.warn('[LessonDetailView] Plan found but lesson_json is null:', plan.id);
          // Still try to load it - the API might return it even if the list doesn't show it
        }

        const planDetailResponse = await lessonApi.getPlanDetail(plan.id, currentUser.id);
        const loadedPlan = planDetailResponse.data;

        // CRITICAL VALIDATION: Verify the loaded plan's week_of matches what we requested
        if (loadedPlan.week_of !== weekOf && normalizeWeek(loadedPlan.week_of) !== normalizedWeekOf) {
          console.error('[LessonDetailView] WEEK MISMATCH DETECTED!', {
            requestedWeekOf: weekOf,
            loadedPlanWeekOf: loadedPlan.week_of,
            normalizedRequested: normalizedWeekOf,
            normalizedLoaded: normalizeWeek(loadedPlan.week_of),
            planId: plan.id,
            error: 'Loaded plan is for a different week than requested!'
          });

          // Try to find the correct plan
          const correctPlan = plans.find(p => {
            const pNormalized = normalizeWeek(p.week_of);
            return p.week_of === weekOf || pNormalized === normalizedWeekOf;
          });

          if (correctPlan && correctPlan.id !== plan.id) {
            console.warn('[LessonDetailView] Found correct plan, reloading:', {
              wrongPlanId: plan.id,
              wrongPlanWeekOf: plan.week_of,
              correctPlanId: correctPlan.id,
              correctPlanWeekOf: correctPlan.week_of
            });

            const correctPlanDetailResponse = await lessonApi.getPlanDetail(correctPlan.id, currentUser.id);
            setLessonPlan(correctPlanDetailResponse.data);
          } else {
            console.error('[LessonDetailView] No correct plan found, using wrong plan but logging error');
            setLessonPlan(loadedPlan);
            setError(`Warning: Loaded plan is for week ${loadedPlan.week_of}, but requested week ${weekOf}`);
          }
        } else {
          console.log('[LessonDetailView] Plan week validation passed:', {
            requestedWeekOf: weekOf,
            loadedPlanWeekOf: loadedPlan.week_of,
            match: true
          });
          setLessonPlan(loadedPlan);
        }

        // Normalize day name for API calls (backend expects lowercase)
        const normalizedDayForApi = day?.toLowerCase();

        // Debug: Check what days are available in lesson_json
        if (planDetailResponse.data?.lesson_json?.days) {
          const availableDays = Object.keys(planDetailResponse.data.lesson_json.days);
          console.log('[LessonDetailView] Available days in lesson_json:', availableDays);
          console.log('[LessonDetailView] Requested day:', day, 'Normalized:', normalizedDayForApi);
          console.log('[LessonDetailView] Day match:', availableDays.includes(normalizedDayForApi));
        }

        // Load lesson steps to get vocabulary and sentence frames
        try {
          const stepsResponse = await lessonApi.getLessonSteps(plan.id, normalizedDayForApi, slot, currentUser.id);
          if (stepsResponse.data && stepsResponse.data.length > 0) {
            setLessonSteps(stepsResponse.data);
          } else {
            // Try to generate steps if they don't exist
            try {
              const generateResponse = await lessonApi.generateLessonSteps(plan.id, normalizedDayForApi, slot, currentUser.id);
              if (generateResponse.data && generateResponse.data.length > 0) {
                setLessonSteps(generateResponse.data);
              }
            } catch (genErr: any) {
              console.warn('[LessonDetailView] Could not generate lesson steps:', genErr);
              // Check if it's a phase_plan error - use fallback default steps
              const errorMessage = genErr?.message || '';
              if (errorMessage.includes('phase_plan') || errorMessage.includes('No phase_plan')) {
                console.log('[LessonDetailView] No phase_plan found, using default lesson steps');
                // Import and use default steps fallback
                import('@lesson-mode/utils/defaultLessonSteps').then(({ createDefaultLessonSteps }) => {
                  const defaultSteps = createDefaultLessonSteps(plan.id, day, slot);
                  setLessonSteps(defaultSteps);
                  setError(null); // Clear any error since we have fallback steps
                  console.log('[LessonDetailView] Created default lesson steps:', defaultSteps.length, 'steps');
                }).catch((importErr) => {
                  console.error('[LessonDetailView] Failed to import default steps utility:', importErr);
                  // Still show error as fallback
                  setError('This lesson plan is incomplete. The lesson needs a phase plan to generate steps. Please complete the lesson plan first.');
                });
              } else {
                // Don't set error for other generation failures - lesson can still be viewed
                console.warn('[LessonDetailView] Lesson steps generation failed, but lesson can still be viewed');
              }
            }
          }
        } catch (stepsErr) {
          console.warn('[LessonDetailView] Could not load lesson steps:', stepsErr);
        }
      } catch (err: any) {
        console.error('[LessonDetailView] Failed to load lesson plan:', err);
        const errorMessage = err?.message || '';
        // Provide more user-friendly error messages
        // Note: phase_plan errors are handled in the generateLessonSteps catch block above
        // and will use default steps, so we don't need to set error here for phase_plan issues
        if (errorMessage.includes('No lesson plan found')) {
          setError('No lesson plan found for this week. Please generate a lesson plan first.');
        } else if (!errorMessage.includes('phase_plan') && !errorMessage.includes('No phase_plan')) {
          // Only set error if it's not a phase_plan issue (those are handled with default steps)
          setError(errorMessage || 'Failed to load lesson plan. Please try selecting a different lesson.');
        }
        // If it's a phase_plan error, it's already handled with default steps above, so no error needed
      } finally {
        setLoading(false);
      }
    };

    loadLessonPlan();
  }, [currentUser, weekOf, day, slot]);


  // Compute slotData with vocabulary/sentence frames extracted from lesson steps
  // Use useMemo so it recalculates when lessonSteps becomes available
  // IMPORTANT: All hooks must be called before any conditional returns
  const slotData = useMemo(() => {
    // Always prefer data from lessonPlan (fresh from database) over initialSlotData (might be stale)
    // This ensures we show the latest vocabulary_cognates and sentence_frames
    let computedSlotData = null;

    // If no lessonPlan yet, use initialSlotData as temporary fallback
    // The useMemo will re-run when lessonPlan loads (it's in the dependency array)
    // and then we'll process the lessonPlan data
    if (!lessonPlan) {
      if (initialSlotData) {
        console.log('[LessonDetailView] No lessonPlan yet, using initialSlotData temporarily (will re-run when lessonPlan loads)');
        return initialSlotData;
      }
      console.log('[LessonDetailView] No lessonPlan or initialSlotData available');
      return null;
    }

    console.log('[LessonDetailView] Processing lessonPlan data', {
      plan_id: lessonPlan.id,
      has_lesson_json: !!lessonPlan.lesson_json,
      lesson_json_type: typeof lessonPlan.lesson_json,
      week_of: lessonPlan.week_of,
    });

    // Compute dayData inside useMemo to avoid dependency issues
    // Normalize day name to lowercase to match lesson_json structure
    const normalizedDay = day?.toLowerCase();

    // Parse lesson_json if it's a string
    let lessonJson = lessonPlan?.lesson_json;
    if (typeof lessonJson === 'string') {
      try {
        lessonJson = JSON.parse(lessonJson);
      } catch (e) {
        console.warn('[LessonDetailView] Failed to parse lesson_json:', e);
        lessonJson = null;
      }
    }

    let dayData = lessonJson?.days?.[normalizedDay];

    // Fallback: Try alternative day name formats if initial lookup fails
    if (!dayData && lessonJson?.days) {
      const availableDays = Object.keys(lessonJson.days);
      // Try exact match first (case-insensitive)
      const matchingDay = availableDays.find(d => d.toLowerCase() === normalizedDay);
      if (matchingDay) {
        dayData = lessonJson.days[matchingDay];
        console.log('[LessonDetailView] Found day data using case-insensitive match:', matchingDay);
      }
    }

    // Debug: Log day data lookup
    if (lessonJson?.days) {
      const availableDays = Object.keys(lessonJson.days);
      console.log('[LessonDetailView] slotData useMemo - Day lookup:', {
        requested_day: day,
        normalized_day: normalizedDay,
        available_days: availableDays,
        day_found: !!dayData,
        day_data_keys: dayData ? Object.keys(dayData) : null,
        has_slots: dayData?.slots ? `Array with ${dayData.slots.length} slots` : 'No slots',
        slot_numbers: dayData?.slots ? dayData.slots.map((s: any) => s?.slot_number).filter(Boolean) : [],
        day_data_type: typeof dayData,
        day_data_value: dayData,
      });
    } else {
      console.log('[LessonDetailView] No lesson_json.days found', {
        has_lesson_plan: !!lessonPlan,
        has_lesson_json: !!lessonPlan?.lesson_json,
        lesson_json_type: typeof lessonPlan?.lesson_json,
      });
    }

    // CRITICAL: Use the slot prop (from plan matching) to find content
    // The slot prop comes from planSlotNumber in WeekView, which is the authoritative plan slot number
    // The schedule entry's slot_number might not match the plan slot number
    // Priority: slot prop (plan slot) > planSlotIndex > scheduleEntry.slot_number
    const targetSlotNumber = slot ?? (typeof planSlotIndex === 'number' ? undefined : scheduleEntry.slot_number);

    console.log('[LessonDetailView] Slot resolution:', {
      prop_slot: slot,
      scheduleEntry_slot: scheduleEntry.slot_number,
      initialSlotData_slot: initialSlotData?.slot_number,
      planSlotIndex,
      using_target_slot: targetSlotNumber,
      note: 'Using plan slot number (from plan matching) for content display',
    });

    // First, try to get from lessonPlan (fresh data) using the slot prop (plan slot number)
    // Check if dayData has a slots array
    if (dayData?.slots && Array.isArray(dayData.slots) && dayData.slots.length > 0) {
      console.log('[LessonDetailView] Day data has slots array with', dayData.slots.length, 'slots');
      if (targetSlotNumber !== undefined) {
        computedSlotData = dayData.slots.find((s: any) => {
          const slotNum = typeof s.slot_number === 'number' ? s.slot_number : parseInt(s.slot_number);
          const targetNum = typeof targetSlotNumber === 'number' ? targetSlotNumber : parseInt(targetSlotNumber);
          return slotNum === targetNum;
        });
        if (computedSlotData) {
          console.log('[LessonDetailView] Found slot by slot number:', targetSlotNumber);
          console.log('[LessonDetailView] Slot data structure:', JSON.stringify({
            unit_lesson: computedSlotData.unit_lesson,
            unit_lesson_type: typeof computedSlotData.unit_lesson,
            unit_lesson_length: typeof computedSlotData.unit_lesson === 'string' ? computedSlotData.unit_lesson.length : 'N/A',
            objective: computedSlotData.objective,
            objective_type: typeof computedSlotData.objective,
            objective_keys: typeof computedSlotData.objective === 'object' ? Object.keys(computedSlotData.objective || {}) : null,
            tailored_instruction: computedSlotData.tailored_instruction,
            tailored_instruction_type: typeof computedSlotData.tailored_instruction,
            tailored_instruction_keys: typeof computedSlotData.tailored_instruction === 'object' ? Object.keys(computedSlotData.tailored_instruction || {}) : null,
            tailored_instruction_original_content: computedSlotData.tailored_instruction?.original_content,
            tailored_instruction_original_content_type: typeof computedSlotData.tailored_instruction?.original_content,
            tailored_instruction_original_content_length: typeof computedSlotData.tailored_instruction?.original_content === 'string' ? computedSlotData.tailored_instruction.original_content.length : 'N/A',
            tailored_instruction_co_teaching: computedSlotData.tailored_instruction?.co_teaching_model,
            tailored_instruction_co_teaching_keys: computedSlotData.tailored_instruction?.co_teaching_model ? Object.keys(computedSlotData.tailored_instruction.co_teaching_model || {}) : null,
            all_keys: Object.keys(computedSlotData),
          }, null, 2));
        }
      }

      // If not found by slot number, try planSlotIndex as fallback
      if (!computedSlotData && typeof planSlotIndex === 'number' && planSlotIndex >= 0 && planSlotIndex < dayData.slots.length) {
        const indexSlot = dayData.slots[planSlotIndex];
        if (indexSlot) {
          console.log('[LessonDetailView] Using planSlotIndex as fallback:', planSlotIndex, 'slot_number:', indexSlot.slot_number);
          computedSlotData = indexSlot;
        }
      }

      // If still not found, try the schedule entry's slot number as last resort
      if (!computedSlotData && scheduleEntry.slot_number !== targetSlotNumber) {
        const scheduleSlotData = dayData.slots.find((s: any) => {
          const slotNum = typeof s.slot_number === 'number' ? s.slot_number : parseInt(s.slot_number);
          const entryNum = typeof scheduleEntry.slot_number === 'number' ? scheduleEntry.slot_number : parseInt(scheduleEntry.slot_number);
          return slotNum === entryNum;
        });
        if (scheduleSlotData) {
          console.log('[LessonDetailView] Using schedule entry slot as fallback:', scheduleEntry.slot_number);
          computedSlotData = scheduleSlotData;
        }
      }

      // Last resort: use first slot if nothing matched
      if (!computedSlotData && dayData.slots.length > 0) {
        console.log('[LessonDetailView] No slot match found, using first slot as last resort');
        computedSlotData = dayData.slots[0];
      }
    } else if (dayData && (!dayData.slots || !Array.isArray(dayData.slots) || dayData.slots.length === 0)) {
      // If dayData exists but has no slots array or empty slots array, use day-level data directly
      // This handles legacy plans or plans where content is stored at day level
      console.log('[LessonDetailView] Day data has no slots array, using day-level data directly');
      computedSlotData = {
        ...dayData,
        slot_number: targetSlotNumber || scheduleEntry.slot_number,
      };
    }

    // If not found by slot number, try by planSlotIndex
    if (
      !computedSlotData &&
      typeof planSlotIndex === 'number' &&
      dayData?.slots &&
      Array.isArray(dayData.slots) &&
      planSlotIndex >= 0 &&
      planSlotIndex < dayData.slots.length
    ) {
      computedSlotData = dayData.slots[planSlotIndex];
    }

    // Fallback: try to match by subject, grade, and homeroom
    if (!computedSlotData && dayData?.slots && Array.isArray(dayData.slots)) {
      computedSlotData = dayData.slots.find(
        (s: any) =>
          s.subject === scheduleEntry.subject &&
          (!s.grade || s.grade === scheduleEntry.grade) &&
          (!s.homeroom || s.homeroom === scheduleEntry.homeroom)
      );
    }

    // CRITICAL: If we found slotData from lessonPlan, use it (it's fresh from database)
    // If not found, fall back to initialSlotData (from plan matching, might have empty content)
    if (!computedSlotData && initialSlotData) {
      console.log('[LessonDetailView] No slotData found in lessonPlan, using initialSlotData as fallback');
      computedSlotData = initialSlotData;
    } else if (computedSlotData && initialSlotData) {
      // If we found slotData from lessonPlan AND have initialSlotData, merge them:
      // Use slotData's content (fresh from database) but keep initialSlotData's vocabulary/frames
      // (from plan matching, might be more complete)
      console.log('[LessonDetailView] Merging initialSlotData vocabulary/frames with slotData content');
      computedSlotData = {
        ...computedSlotData,
        // Prefer slotData content, but use initialSlotData if slotData is empty
        vocabulary_cognates: (computedSlotData.vocabulary_cognates &&
          Array.isArray(computedSlotData.vocabulary_cognates) &&
          computedSlotData.vocabulary_cognates.length > 0)
          ? computedSlotData.vocabulary_cognates
          : (initialSlotData.vocabulary_cognates || computedSlotData.vocabulary_cognates),
        sentence_frames: (computedSlotData.sentence_frames &&
          Array.isArray(computedSlotData.sentence_frames) &&
          computedSlotData.sentence_frames.length > 0)
          ? computedSlotData.sentence_frames
          : (initialSlotData.sentence_frames || computedSlotData.sentence_frames),
      };
    }

    // Fallback: If slot-level data has empty/missing fields, merge with day-level data
    // This handles cases where slot data exists but fields are empty strings or missing
    if (computedSlotData && dayData) {
      const isEmpty = (value: any): boolean => {
        if (value === null || value === undefined) return true;
        if (typeof value === 'string') return value.trim() === '';
        if (typeof value === 'object') {
          // For objects, check if they have any non-empty properties
          // Empty object {} or object with only empty values should be considered empty
          const values = Object.values(value);
          if (values.length === 0) return true;
          return values.every(v => isEmpty(v));
        }
        return false;
      };

      // Check each field individually and merge if empty
      const fieldsToCheck = [
        'unit_lesson',
        'objective',
        'anticipatory_set',
        'tailored_instruction',
        'assessment',
        'misconceptions',
        'homework'
      ];

      const needsFallback = fieldsToCheck.some(field => isEmpty(computedSlotData[field]));

      // Also check if day-level has content for these fields
      const dayHasContent = fieldsToCheck.some(field => !isEmpty(dayData[field]));

      if (needsFallback && dayHasContent) {
        console.log('[LessonDetailView] Slot data has missing/empty fields, merging with day-level data', {
          slot_unit_lesson: computedSlotData.unit_lesson,
          day_unit_lesson: dayData.unit_lesson,
          slot_objective: computedSlotData.objective,
          day_objective: dayData.objective,
          slot_tailored_instruction: computedSlotData.tailored_instruction,
          day_tailored_instruction: dayData.tailored_instruction,
          day_has_content: dayHasContent,
          day_data_keys: Object.keys(dayData),
        });

        // Merge each field individually
        const merged: any = { ...computedSlotData };
        fieldsToCheck.forEach(field => {
          const slotValue = computedSlotData[field];
          const dayValue = dayData[field];
          const slotIsEmpty = isEmpty(slotValue);
          const dayIsEmpty = isEmpty(dayValue);

          console.log(`[LessonDetailView] Checking ${field}:`, {
            slot_is_empty: slotIsEmpty,
            day_is_empty: dayIsEmpty,
            slot_type: typeof slotValue,
            day_type: typeof dayValue,
            slot_keys: typeof slotValue === 'object' ? Object.keys(slotValue || {}) : null,
            day_keys: typeof dayValue === 'object' ? Object.keys(dayValue || {}) : null,
          });

          if (slotIsEmpty && !dayIsEmpty) {
            merged[field] = dayValue;
            console.log(`[LessonDetailView] ✓ Merged ${field} from day-level data`);
          } else if (!slotIsEmpty && !dayIsEmpty) {
            // Both have content - check if we should merge nested fields
            if (typeof slotValue === 'object' && typeof dayValue === 'object' && !Array.isArray(slotValue) && !Array.isArray(dayValue)) {
              // Merge nested objects - use day-level values for empty slot-level nested fields
              const mergedNested: any = { ...slotValue };
              Object.keys(dayValue).forEach(nestedKey => {
                if (isEmpty(mergedNested[nestedKey]) && !isEmpty(dayValue[nestedKey])) {
                  mergedNested[nestedKey] = dayValue[nestedKey];
                  console.log(`[LessonDetailView] ✓ Merged nested ${field}.${nestedKey} from day-level data`);
                }
              });
              merged[field] = mergedNested;
            }
          }
        });

        computedSlotData = merged;

        console.log('[LessonDetailView] After merge:', {
          unit_lesson: computedSlotData.unit_lesson,
          has_objective: !!computedSlotData.objective && !isEmpty(computedSlotData.objective),
          objective_keys: typeof computedSlotData.objective === 'object' ? Object.keys(computedSlotData.objective || {}) : null,
          has_tailored_instruction: !!computedSlotData.tailored_instruction && !isEmpty(computedSlotData.tailored_instruction),
          tailored_instruction_keys: typeof computedSlotData.tailored_instruction === 'object' ? Object.keys(computedSlotData.tailored_instruction || {}) : null,
        });
      } else if (needsFallback && !dayHasContent) {
        console.log('[LessonDetailView] Slot data has empty fields but day-level data also has no content', {
          day_data_keys: Object.keys(dayData),
          slot_data_sample: {
            unit_lesson: computedSlotData.unit_lesson,
            objective: computedSlotData.objective,
            tailored_instruction: computedSlotData.tailored_instruction ? Object.keys(computedSlotData.tailored_instruction) : null,
            tailored_instruction_original_content: computedSlotData.tailored_instruction?.original_content,
            tailored_instruction_co_teaching: computedSlotData.tailored_instruction?.co_teaching_model ? Object.keys(computedSlotData.tailored_instruction.co_teaching_model) : null,
          },
        });
      } else {
        console.log('[LessonDetailView] No fallback needed - slot data has content');
      }
    }

    // Extract vocabulary and sentence frames from lesson steps if slotData doesn't have them
    if (computedSlotData && lessonSteps.length > 0) {
      // Find vocabulary step
      const vocabStep = lessonSteps.find(
        (step) =>
          step.step_name?.toLowerCase().includes('vocabulary') ||
          step.step_name?.toLowerCase().includes('cognate')
      );

      // Find sentence frames step
      const framesStep = lessonSteps.find(
        (step) => step.content_type === 'sentence_frames'
      );

      // Merge vocabulary from lesson steps if not already in slotData
      if (!computedSlotData.vocabulary_cognates || !Array.isArray(computedSlotData.vocabulary_cognates) || computedSlotData.vocabulary_cognates.length === 0) {
        if (vocabStep?.vocabulary_cognates && Array.isArray(vocabStep.vocabulary_cognates) && vocabStep.vocabulary_cognates.length > 0) {
          console.log('[LessonDetailView] Using vocabulary_cognates from lesson steps:', vocabStep.vocabulary_cognates.length, 'items');
          computedSlotData = { ...computedSlotData, vocabulary_cognates: vocabStep.vocabulary_cognates };
        } else if (vocabStep?.display_content) {
          // Fallback: Parse from display_content (same logic as VocabularyDisplay component)
          // This is needed because vocabulary_cognates is None in DB but display_content has the data
          console.log('[LessonDetailView] Parsing vocabulary from display_content');
          const lines = vocabStep.display_content
            .split('\n')
            .map((line: string) => line.trim())
            .filter((line: string) => line.startsWith('-') || line.startsWith('•'));

          if (lines.length > 0) {
            const parsedVocab = lines.map((line: string) => {
              const content = line.replace(/^[-•]\s*/, '');
              const parts = content.split('->').map((part: string) => part.trim());
              const english = parts[0] || '';
              const portuguese = parts[1] || '';
              return { english, portuguese, is_cognate: false };
            });
            console.log('[LessonDetailView] Parsed', parsedVocab.length, 'vocabulary items from display_content');
            computedSlotData = { ...computedSlotData, vocabulary_cognates: parsedVocab };
          }
        }
      }

      // Merge sentence frames from lesson steps if not already in slotData
      if (!computedSlotData.sentence_frames || !Array.isArray(computedSlotData.sentence_frames) || computedSlotData.sentence_frames.length === 0) {
        if (framesStep?.sentence_frames && Array.isArray(framesStep.sentence_frames) && framesStep.sentence_frames.length > 0) {
          console.log('[LessonDetailView] Using sentence_frames from lesson steps:', framesStep.sentence_frames.length, 'items');
          computedSlotData = { ...computedSlotData, sentence_frames: framesStep.sentence_frames };
        }
      }
    }

    // Debug: Log the found slotData and check for vocabulary/sentence frames
    if (computedSlotData) {
      const hasVocab = Array.isArray(computedSlotData.vocabulary_cognates) && computedSlotData.vocabulary_cognates.length > 0;
      const hasFrames = Array.isArray(computedSlotData.sentence_frames) && computedSlotData.sentence_frames.length > 0;

      // Check if content fields are empty
      const hasUnitLesson = computedSlotData.unit_lesson && computedSlotData.unit_lesson.trim() !== '';
      const hasObjective = computedSlotData.objective && (
        computedSlotData.objective.content_objective ||
        computedSlotData.objective.student_goal ||
        computedSlotData.objective.wida_objective
      );
      const hasAnticipatorySet = computedSlotData.anticipatory_set && (
        computedSlotData.anticipatory_set.original_content ||
        computedSlotData.anticipatory_set.bilingual_bridge
      );
      const hasTailoredInstruction = computedSlotData.tailored_instruction && (
        computedSlotData.tailored_instruction.original_content ||
        computedSlotData.tailored_instruction.co_teaching_model ||
        (Array.isArray(computedSlotData.tailored_instruction.ell_support) && computedSlotData.tailored_instruction.ell_support.length > 0)
      );

      console.log('[LessonDetailView] Found slotData:', {
        slot_number: computedSlotData.slot_number,
        has_unit_lesson: hasUnitLesson,
        has_objective: hasObjective,
        has_anticipatory_set: hasAnticipatorySet,
        has_tailored_instruction: hasTailoredInstruction,
        has_vocabulary: hasVocab,
        vocab_count: Array.isArray(computedSlotData.vocabulary_cognates) ? computedSlotData.vocabulary_cognates.length : 0,
        vocab_type: typeof computedSlotData.vocabulary_cognates,
        vocab_value: computedSlotData.vocabulary_cognates,
        has_sentence_frames: hasFrames,
        frames_count: Array.isArray(computedSlotData.sentence_frames) ? computedSlotData.sentence_frames.length : 0,
        frames_type: typeof computedSlotData.sentence_frames,
        frames_value: computedSlotData.sentence_frames,
        all_keys: Object.keys(computedSlotData),
        unit_lesson_value: computedSlotData.unit_lesson,
        objective_value: computedSlotData.objective,
        tailored_instruction_keys: computedSlotData.tailored_instruction ? Object.keys(computedSlotData.tailored_instruction) : null,
      });

      // If slotData doesn't have vocabulary/sentence frames, try planSlotIndex as fallback
      // This handles cases where the slot number match found a slot without these fields
      if (!hasVocab && !hasFrames && typeof planSlotIndex === 'number' && dayData?.slots) {
        const indexSlot = dayData.slots[planSlotIndex];
        if (indexSlot) {
          const indexHasVocab = Array.isArray(indexSlot.vocabulary_cognates) && indexSlot.vocabulary_cognates.length > 0;
          const indexHasFrames = Array.isArray(indexSlot.sentence_frames) && indexSlot.sentence_frames.length > 0;

          console.log('[LessonDetailView] Checking planSlotIndex slot:', {
            planSlotIndex,
            index_slot_number: indexSlot.slot_number,
            index_has_vocab: indexHasVocab,
            index_has_frames: indexHasFrames,
            index_vocab_value: indexSlot.vocabulary_cognates,
            index_frames_value: indexSlot.sentence_frames,
          });

          if (indexHasVocab || indexHasFrames) {
            console.log('[LessonDetailView] Switching to planSlotIndex slot for vocabulary/frames');
            computedSlotData = indexSlot;
          }
        }
      }
    }

    // Final fallback: If no slot data found but day data exists, use day-level data directly
    // This handles cases where the lesson plan doesn't have slot-level structure
    // Also try to get dayData again if it wasn't set earlier
    if (!computedSlotData) {
      // Re-check dayData if it wasn't set earlier
      if (!dayData && lessonJson?.days) {
        dayData = lessonJson.days[normalizedDay];
        if (!dayData) {
          const availableDays = Object.keys(lessonJson.days);
          const matchingDay = availableDays.find(d => d.toLowerCase() === normalizedDay);
          if (matchingDay) {
            dayData = lessonJson.days[matchingDay];
          }
        }
      }

      if (dayData) {
        console.log('[LessonDetailView] No slot data found, using day-level data as fallback', {
          day_data_keys: Object.keys(dayData),
          has_slots: Array.isArray(dayData.slots),
          slots_length: dayData.slots?.length || 0,
        });
        // Use day-level data but preserve slot-specific fields if they exist
        computedSlotData = {
          ...dayData,
          // Keep any slot-specific identifiers
          slot_number: targetSlotNumber || scheduleEntry.slot_number,
        };
      }
    }

    if (!computedSlotData) {
      console.warn('[LessonDetailView] No slotData found for slot:', slot, 'day:', day, {
        has_day_data: !!dayData,
        day_data_keys: dayData ? Object.keys(dayData) : null,
        has_slots_array: Array.isArray(dayData?.slots),
        slots_length: dayData?.slots?.length || 0,
        has_lesson_json: !!lessonJson,
        has_days: !!lessonJson?.days,
        available_days: lessonJson?.days ? Object.keys(lessonJson.days) : null,
      });
    } else {
      // Final debug: Log what we're returning
      console.log('[LessonDetailView] Final computedSlotData:', {
        slot_number: computedSlotData.slot_number,
        has_unit_lesson: !!computedSlotData.unit_lesson,
        has_objective: !!computedSlotData.objective,
        has_anticipatory_set: !!computedSlotData.anticipatory_set,
        has_tailored_instruction: !!computedSlotData.tailored_instruction,
        has_assessment: !!computedSlotData.assessment,
        has_misconceptions: !!computedSlotData.misconceptions,
        has_homework: !!computedSlotData.homework,
        all_keys: Object.keys(computedSlotData),
      });
    }

    return computedSlotData;
  }, [lessonPlan, lessonSteps, day, slot, planSlotIndex, initialSlotData, scheduleEntry]);

  const renderParagraphs = (text?: string) => {
    if (!text) return null;
    return text
      .split(/\n+/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean)
      .map((paragraph, idx) => (
        <div key={`paragraph-${idx}`} className="text-sm leading-relaxed mb-2">
          {parseMarkdown(paragraph)}
        </div>
      ));
  };

  // Early returns must come AFTER all hooks
  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-lg font-semibold mb-2">Loading lesson details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-lg font-semibold text-destructive mb-2">Error</div>
        <div className="text-muted-foreground mb-4">{error}</div>
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b h-8 flex-shrink-0">
        <div className="flex items-center gap-4">
          {/* Previous/Next Buttons */}
          <div className="flex items-center gap-2">
            <Button
              onClick={() => {
                if (onPreviousLesson) {
                  onPreviousLesson();
                }
              }}
              disabled={!canGoPrevious || !onPreviousLesson}
              variant="outline"
              size="sm"
              className="h-7"
            >
              <ChevronLeft className="w-3 h-3 mr-1" />
              Previous
            </Button>
            <Button
              onClick={() => {
                if (onNextLesson) {
                  onNextLesson();
                }
              }}
              disabled={!canGoNext || !onNextLesson}
              variant="outline"
              size="sm"
              className="h-7"
            >
              Next
              <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>

          {/* Metadata */}
          <LessonMetadataDisplay
            scheduleEntry={scheduleEntry}
            day={day}
            weekOf={weekOf}
            showStatusBadge={true}
            className="text-base"
          />

          {scheduleEntry.plan_slot_group_id && (
            <div className="inline-flex items-center rounded-full border border-muted px-2 py-0.5 text-xs uppercase tracking-wide text-muted-foreground">
              Linked group: {scheduleEntry.plan_slot_group_id}
            </div>
          )}
        </div>
        <div className="flex gap-2 items-center">
          {onEnterLessonMode && (
            <Button
              onClick={() => onEnterLessonMode(scheduleEntry, day, slot, lessonPlan?.id, 'lesson', weekOf)}
              size="sm"
              className="h-7"
            >
              Enter Lesson Mode
            </Button>
          )}
          <Button
            onClick={onBack}
            variant="outline"
            size="sm"
            className="h-7"
          >
            <ArrowLeft className="w-3 h-3 mr-1" />
            Back
          </Button>
        </div>
      </div>

      {/* Grid Layout */}
      {slotData ? (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-6">
              {/* Unit/Lesson */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Unit/Lesson</h3>
                <div>{parseMarkdown(slotData.unit_lesson?.trim()) || 'N/A'}</div>
              </Card>

              {/* Objectives */}
              <Card className="p-4">
                <h3 className="font-semibold mb-3">Objectives</h3>
                <div className="space-y-3">
                  {slotData.objective?.content_objective?.trim() && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        Content Objective
                      </div>
                      <div>{parseMarkdown(slotData.objective.content_objective)}</div>
                    </div>
                  )}
                  {slotData.objective?.student_goal?.trim() && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        Student Goal
                      </div>
                      <div>{parseMarkdown(slotData.objective.student_goal)}</div>
                    </div>
                  )}
                  {slotData.objective?.wida_objective?.trim() && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        WIDA Objective
                      </div>
                      <div>{parseMarkdown(slotData.objective.wida_objective)}</div>
                    </div>
                  )}
                  {!slotData.objective?.content_objective?.trim() &&
                    !slotData.objective?.student_goal?.trim() &&
                    !slotData.objective?.wida_objective?.trim() && (
                      <div className="text-sm text-muted-foreground italic">No objectives provided</div>
                    )}
                </div>
              </Card>

              {/* Anticipatory Set */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Anticipatory Set</h3>
                {slotData.anticipatory_set?.original_content?.trim() && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Original
                    </div>
                    <div>{parseMarkdown(slotData.anticipatory_set.original_content)}</div>
                  </div>
                )}
                {slotData.anticipatory_set?.bilingual_bridge?.trim() && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Bilingual Bridge
                    </div>
                    <div>{parseMarkdown(slotData.anticipatory_set.bilingual_bridge)}</div>
                  </div>
                )}
                {!slotData.anticipatory_set?.original_content?.trim() &&
                  !slotData.anticipatory_set?.bilingual_bridge?.trim() && (
                    <div className="text-sm text-muted-foreground italic">No anticipatory set provided</div>
                  )}
              </Card>

              {/* Vocabulary / Cognates */}
              {Array.isArray(slotData.vocabulary_cognates) && slotData.vocabulary_cognates.length > 0 && (
                <Card className="p-4">
                  <h3 className="font-semibold mb-3">Vocabulary / Cognates</h3>
                  <div className="space-y-2">
                    {slotData.vocabulary_cognates.map((vocab: any, idx: number) => (
                      <div key={idx} className="flex items-baseline justify-between border-b border-border/40 pb-2 last:border-0">
                        <div>
                          <span className="font-medium">{vocab.english}</span>
                          <span className="mx-2 text-muted-foreground">→</span>
                          <span className="italic text-muted-foreground">{vocab.portuguese}</span>
                        </div>
                        <span
                          className={getCognateBadgeClasses(vocab.is_cognate, 'sm')}
                          style={{
                            color: vocab.is_cognate ? '#15803d' : '#dc2626' // green-700 : red-700
                          }}
                        >
                          {getCognateBadgeLabel(vocab.is_cognate)}
                        </span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Assessment */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Assessment</h3>
                {slotData.assessment?.primary_assessment && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Primary Assessment
                    </div>
                    <div>{parseMarkdown(slotData.assessment.primary_assessment)}</div>
                  </div>
                )}
                {slotData.assessment?.bilingual_check && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Bilingual Check
                    </div>
                    <div>{parseMarkdown(slotData.assessment.bilingual_check)}</div>
                  </div>
                )}
              </Card>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Tailored Instruction */}
              <Card className="p-4">
                <h3 className="font-semibold mb-3">Tailored Instruction</h3>
                {slotData.tailored_instruction ? (
                  <div className="space-y-4">
                    {(slotData.tailored_instruction.original_content?.trim() ||
                      (process.env.NODE_ENV === 'development' && slotData.tailored_instruction.original_content)) && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">
                            Original Content
                          </div>
                          <div className="space-y-2">
                            {slotData.tailored_instruction.original_content?.trim() ? (
                              renderParagraphs(slotData.tailored_instruction.original_content)
                            ) : (
                              <div className="text-sm text-muted-foreground italic">
                                {process.env.NODE_ENV === 'development' && 'Empty string detected'}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                    {slotData.tailored_instruction.co_teaching_model && (
                      <div className="space-y-2">
                        <div className="text-xs font-semibold text-muted-foreground">
                          Co-Teaching Model
                        </div>
                        <div className="font-medium">
                          {slotData.tailored_instruction.co_teaching_model.model_name || 'N/A'}
                        </div>
                        {slotData.tailored_instruction.co_teaching_model.rationale && (
                          <div className="text-sm text-muted-foreground">
                            {parseMarkdown(slotData.tailored_instruction.co_teaching_model.rationale)}
                          </div>
                        )}
                        {slotData.tailored_instruction.co_teaching_model.wida_context && (
                          <div className="text-xs text-muted-foreground">
                            {parseMarkdown(slotData.tailored_instruction.co_teaching_model.wida_context)}
                          </div>
                        )}
                        {Array.isArray(slotData.tailored_instruction.co_teaching_model.implementation_notes) &&
                          slotData.tailored_instruction.co_teaching_model.implementation_notes.length > 0 && (
                            <div>
                              <div className="text-xs font-semibold text-muted-foreground mb-1">
                                Implementation Notes
                              </div>
                              <ul className="list-disc list-inside space-y-1 text-sm">
                                {slotData.tailored_instruction.co_teaching_model.implementation_notes.map(
                                  (note: string, idx: number) => (
                                    <li key={`implementation-note-${idx}`}>{parseMarkdown(note)}</li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}
                        {Array.isArray(slotData.tailored_instruction.co_teaching_model.phase_plan) &&
                          slotData.tailored_instruction.co_teaching_model.phase_plan.length > 0 && (
                            <div>
                              <div className="text-xs font-semibold text-muted-foreground mb-1">
                                Phase Plan
                              </div>
                              <ol className="space-y-2">
                                {slotData.tailored_instruction.co_teaching_model.phase_plan.map(
                                  (phase: any, idx: number) => (
                                    <li
                                      key={`phase-${phase?.phase_name || idx}`}
                                      className="rounded-md border border-border/60 bg-muted/40 p-3"
                                    >
                                      <div className="font-semibold text-sm">
                                        {phase?.phase_name || `Phase ${idx + 1}`}
                                        {phase?.minutes ? ` (${phase.minutes} min)` : ''}
                                      </div>
                                      <div className="space-y-1 text-xs text-muted-foreground mt-1">
                                        {phase?.bilingual_teacher_role && (
                                          <div>
                                            <span className="font-semibold text-foreground">Bilingual:</span>{' '}
                                            {parseMarkdown(phase.bilingual_teacher_role)}
                                          </div>
                                        )}
                                        {phase?.primary_teacher_role && (
                                          <div>
                                            <span className="font-semibold text-foreground">Primary:</span>{' '}
                                            {parseMarkdown(phase.primary_teacher_role)}
                                          </div>
                                        )}
                                        {phase?.details && (
                                          <div>
                                            <span className="font-semibold text-foreground">Details:</span>{' '}
                                            {parseMarkdown(phase.details)}
                                          </div>
                                        )}
                                      </div>
                                    </li>
                                  )
                                )}
                              </ol>
                            </div>
                          )}
                      </div>
                    )}

                    {Array.isArray(slotData.tailored_instruction.ell_support) &&
                      slotData.tailored_instruction.ell_support.length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">ELL Support</div>
                          <div className="space-y-3">
                            {slotData.tailored_instruction.ell_support.map((support: any, idx: number) => {
                              if (typeof support === 'string') {
                                return (
                                  <div key={`ell-support-${idx}`} className="text-sm">
                                    {parseMarkdown(support)}
                                  </div>
                                );
                              }
                              return (
                                <div key={`ell-support-${support?.strategy_id || idx}`} className="rounded-md border border-border/60 p-3">
                                  <div className="text-sm font-semibold">
                                    {parseMarkdown(support?.strategy_name || support?.description || 'ELL Support')}
                                  </div>
                                  {support?.proficiency_levels && (
                                    <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                                      {support.proficiency_levels}
                                    </div>
                                  )}
                                  {support?.implementation && (
                                    <div className="text-sm text-muted-foreground">{parseMarkdown(support.implementation)}</div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                    {Array.isArray(slotData.tailored_instruction.special_needs_support) &&
                      slotData.tailored_instruction.special_needs_support.length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">
                            Special Needs Support
                          </div>
                          <ul className="list-disc list-inside space-y-1 text-sm">
                            {slotData.tailored_instruction.special_needs_support.map(
                              (support: string, idx: number) => (
                                <li key={`special-support-${idx}`}>{parseMarkdown(support)}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}

                    {Array.isArray(slotData.tailored_instruction.materials) &&
                      slotData.tailored_instruction.materials.length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-muted-foreground mb-1">Materials</div>
                          <ul className="list-disc list-inside space-y-1 text-sm">
                            {slotData.tailored_instruction.materials.map((material: string, idx: number) => (
                              <li key={`material-${idx}`}>{parseMarkdown(material)}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                    {/* Show message if all tailored instruction content is empty */}
                    {!slotData.tailored_instruction.original_content?.trim() &&
                      (!slotData.tailored_instruction.co_teaching_model ||
                        (!slotData.tailored_instruction.co_teaching_model.model_name &&
                          !slotData.tailored_instruction.co_teaching_model.rationale &&
                          (!Array.isArray(slotData.tailored_instruction.co_teaching_model.phase_plan) ||
                            slotData.tailored_instruction.co_teaching_model.phase_plan.length === 0))) &&
                      (!Array.isArray(slotData.tailored_instruction.ell_support) ||
                        slotData.tailored_instruction.ell_support.length === 0) &&
                      (!Array.isArray(slotData.tailored_instruction.special_needs_support) ||
                        slotData.tailored_instruction.special_needs_support.length === 0) &&
                      (!Array.isArray(slotData.tailored_instruction.materials) ||
                        slotData.tailored_instruction.materials.length === 0) && (
                        <div className="text-sm text-muted-foreground italic">
                          No tailored instruction content available for this slot.
                        </div>
                      )}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground italic">
                    No tailored instruction provided for this slot.
                  </div>
                )}
              </Card>

              {/* Sentence Frames */}
              {Array.isArray(slotData.sentence_frames) && slotData.sentence_frames.length > 0 && (
                <Card className="p-4">
                  <h3 className="font-semibold mb-3">Sentence Frames</h3>
                  <div className="space-y-6">
                    {([
                      { key: 'levels_1_2', label: 'Levels 1-2' },
                      { key: 'levels_3_4', label: 'Levels 3-4' },
                      { key: 'levels_5_6', label: 'Levels 5-6' },
                    ] as const).map((group) => {
                      const frames = slotData.sentence_frames.filter(
                        (f: any) => f.proficiency_level === group.key
                      );
                      if (frames.length === 0) return null;

                      return (
                        <div key={group.key} className="space-y-2">
                          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground border-b pb-1">
                            {group.label}
                          </div>
                          <div className="space-y-3">
                            {frames.map((frame: any, idx: number) => {
                              // Extract vocabulary words for highlighting
                              const vocabWords = extractVocabularyWords(slotData.vocabulary_cognates);

                              return (
                                <div key={idx} className="text-sm">
                                  <div className="font-medium">
                                    {highlightVocabularyWords(frame.english, vocabWords)}
                                  </div>
                                  <div className="text-muted-foreground italic">{frame.portuguese}</div>
                                  {frame.language_function && (
                                    <div className="mt-1 inline-block text-[10px] uppercase tracking-wide text-muted-foreground bg-muted px-1.5 rounded">
                                      {frame.language_function.replace(/_/g, ' ')}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Misconceptions */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Misconceptions</h3>
                {slotData.misconceptions?.original_content && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Original Content
                    </div>
                    <div>{parseMarkdown(slotData.misconceptions.original_content)}</div>
                  </div>
                )}
                {slotData.misconceptions?.linguistic_note && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Linguistic Note
                    </div>
                    <div className="space-y-2">
                      {typeof slotData.misconceptions.linguistic_note === 'string' ? (
                        <div>{parseMarkdown(slotData.misconceptions.linguistic_note)}</div>
                      ) : (
                        <>
                          {slotData.misconceptions.linguistic_note.pattern_id && (
                            <div>
                              <span className="font-semibold">Pattern: </span>
                              {slotData.misconceptions.linguistic_note.pattern_id.replace(/_/g, ' ')}
                            </div>
                          )}
                          {slotData.misconceptions.linguistic_note.note && (
                            <div>
                              <span className="font-semibold">Note: </span>
                              {parseMarkdown(slotData.misconceptions.linguistic_note.note)}
                            </div>
                          )}
                          {slotData.misconceptions.linguistic_note.prevention_tip && (
                            <div>
                              <span className="font-semibold">Prevention Tip: </span>
                              {parseMarkdown(slotData.misconceptions.linguistic_note.prevention_tip)}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                )}
                {/* Fallback for old structure */}
                {slotData.misconceptions?.linguistic_misconceptions && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Linguistic Misconceptions
                    </div>
                    <div>{parseMarkdown(slotData.misconceptions.linguistic_misconceptions)}</div>
                  </div>
                )}
                {slotData.misconceptions?.content_misconceptions && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Content Misconceptions
                    </div>
                    <div>{parseMarkdown(slotData.misconceptions.content_misconceptions)}</div>
                  </div>
                )}
                {/* Show if misconceptions is a string instead of object */}
                {typeof slotData.misconceptions === 'string' && slotData.misconceptions && (
                  <div>{parseMarkdown(slotData.misconceptions)}</div>
                )}
                {/* Show message if no misconceptions data */}
                {!slotData.misconceptions && (
                  <div className="text-sm text-muted-foreground italic">
                    No misconceptions identified
                  </div>
                )}
              </Card>

              {/* Homework */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Homework</h3>
                {slotData.homework?.original_content && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Original
                    </div>
                    <div>{parseMarkdown(slotData.homework.original_content)}</div>
                  </div>
                )}
                {slotData.homework?.family_connection && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Family Connection
                    </div>
                    <div>{parseMarkdown(slotData.homework.family_connection)}</div>
                  </div>
                )}
              </Card>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-16 text-muted-foreground">
          <p>Lesson plan data not available</p>
          <p className="text-sm mt-2">Generate a lesson plan for this week to view details</p>
        </div>
      )}
    </div>
  );
}

