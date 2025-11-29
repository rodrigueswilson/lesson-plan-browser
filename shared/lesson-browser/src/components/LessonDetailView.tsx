import { useState, useEffect, useMemo } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import { lessonApi, LessonPlanDetail, ScheduleEntry } from '@lesson-api';
import { useStore } from '../store/useStore';
import { highlightVocabularyWords, extractVocabularyWords, getCognateBadgeClasses, getCognateBadgeLabel } from '@lesson-mode/utils/vocabularyHighlight';

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

  useEffect(() => {
    const loadLessonPlan = async () => {
      if (!currentUser) {
        setError('No user selected');
        setLoading(false);
        return;
      }

      try {
        // Find plan for this week
        const { planApi } = await import('@lesson-api');
        const plansResponse = await planApi.list(currentUser.id, 10, currentUser.id);
        const plans = plansResponse.data || [];
        const plan = plans.find(p => p.week_of === weekOf);
        
        if (!plan) {
          setError('No lesson plan found for this week');
          setLoading(false);
          return;
        }

        const planDetailResponse = await lessonApi.getPlanDetail(plan.id, currentUser.id);
        setLessonPlan(planDetailResponse.data);
        
        // Load lesson steps to get vocabulary and sentence frames
        try {
          const stepsResponse = await lessonApi.getLessonSteps(plan.id, day, slot, currentUser.id);
          if (stepsResponse.data && stepsResponse.data.length > 0) {
            setLessonSteps(stepsResponse.data);
          } else {
            // Try to generate steps if they don't exist
            try {
              const generateResponse = await lessonApi.generateLessonSteps(plan.id, day, slot, currentUser.id);
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

  // Calculate the actual date for this day
  const getLessonDate = () => {
    if (!weekOf) return null;
    
    // weekOf format is "MM-DD-MM-DD" (Monday to Friday)
    const [startMonth, startDay] = weekOf.split('-').slice(0, 2).map(Number);
    const year = new Date().getFullYear();
    const mondayDate = new Date(year, startMonth - 1, startDay);
    
    const dayIndex = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].indexOf(day.toLowerCase());
    if (dayIndex === -1) return null;
    
    const lessonDate = new Date(mondayDate);
    lessonDate.setDate(mondayDate.getDate() + dayIndex);
    
    return lessonDate.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };
  
  // Format date as MM/DD/YY
  const formatDateShort = (date: Date | null): string | null => {
    if (!date || isNaN(date.getTime())) {
      console.error('[LessonDetailView] Invalid date object:', date);
      return null;
    }
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    return `${month}/${day}/${year}`;
  };
  
  // Get day name (capitalize first letter)
  const getDayName = (day: string): string => {
    return day.charAt(0).toUpperCase() + day.slice(1);
  };
  
  // Helper function to get Monday of a given week number
  const getMondayOfWeek = (weekNumber: number, year: number): Date => {
    // January 1st of the year
    const jan1 = new Date(year, 0, 1);
    // Get the day of week (0 = Sunday, 1 = Monday, etc.)
    const dayOfWeek = jan1.getDay();
    // Calculate days to subtract to get to Monday of week 1
    // If Jan 1 is Sunday (0), we go back 6 days to get Monday of previous week
    // If Jan 1 is Monday (1), we're already at Monday
    // If Jan 1 is Tuesday (2), we go back 1 day
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    // Monday of week 1
    const mondayOfWeek1 = new Date(jan1);
    mondayOfWeek1.setDate(jan1.getDate() - daysToMonday);
    // Add weeks (weekNumber - 1) because week 1 starts at mondayOfWeek1
    const mondayOfTargetWeek = new Date(mondayOfWeek1);
    mondayOfTargetWeek.setDate(mondayOfWeek1.getDate() + (weekNumber - 1) * 7);
    return mondayOfTargetWeek;
  };

  // Get the Date object for the lesson
  const getLessonDateObject = (): Date | null => {
    if (!weekOf || !day) {
      console.warn('[LessonDetailView] Missing weekOf or day:', { weekOf, day });
      return null;
    }
    
    try {
      let mondayDate: Date;
      
      // Check if weekOf is in "W47" format (week number)
      if (weekOf.startsWith('W') || weekOf.startsWith('w')) {
        const weekNumber = parseInt(weekOf.substring(1), 10);
        if (isNaN(weekNumber) || weekNumber < 1 || weekNumber > 53) {
          console.error('[LessonDetailView] Invalid week number:', { weekOf, weekNumber });
          return null;
        }
        
        const year = new Date().getFullYear();
        mondayDate = getMondayOfWeek(weekNumber, year);
        
        if (isNaN(mondayDate.getTime())) {
          console.error('[LessonDetailView] Invalid mondayDate from week number:', { weekNumber, year });
          return null;
        }
      } else {
        // weekOf format is "MM-DD-MM-DD" (Monday to Friday)
        const parts = weekOf.split('-');
        if (parts.length < 2) {
          console.error('[LessonDetailView] Invalid weekOf format:', weekOf);
          return null;
        }
        
        const [startMonth, startDay] = parts.slice(0, 2).map(Number);
        
        if (isNaN(startMonth) || isNaN(startDay) || startMonth < 1 || startMonth > 12 || startDay < 1 || startDay > 31) {
          console.error('[LessonDetailView] Invalid month or day:', { startMonth, startDay, weekOf });
          return null;
        }
        
        const year = new Date().getFullYear();
        mondayDate = new Date(year, startMonth - 1, startDay);
        
        if (isNaN(mondayDate.getTime())) {
          console.error('[LessonDetailView] Invalid mondayDate:', { year, startMonth, startDay });
          return null;
        }
      }
      
      const dayIndex = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].indexOf(day.toLowerCase());
      if (dayIndex === -1) {
        console.error('[LessonDetailView] Invalid day:', day);
        return null;
      }
      
      const lessonDate = new Date(mondayDate);
      lessonDate.setDate(mondayDate.getDate() + dayIndex);
      
      if (isNaN(lessonDate.getTime())) {
        console.error('[LessonDetailView] Invalid lessonDate after calculation');
        return null;
      }
      
      return lessonDate;
    } catch (error) {
      console.error('[LessonDetailView] Error in getLessonDateObject:', error);
      return null;
    }
  };
  
  const lessonDate = getLessonDate();
  const lessonDateObject = getLessonDateObject();
  const formattedDate = lessonDateObject ? formatDateShort(lessonDateObject) : null;
  
  // Debug logging
  if (!formattedDate && weekOf && day) {
    console.warn('[LessonDetailView] Could not format date:', {
      weekOf,
      day,
      lessonDateObject,
      hasLessonDateObject: !!lessonDateObject
    });
  }
  
  // Compute slotData with vocabulary/sentence frames extracted from lesson steps
  // Use useMemo so it recalculates when lessonSteps becomes available
  // IMPORTANT: All hooks must be called before any conditional returns
  const slotData = useMemo(() => {
    // Always prefer data from lessonPlan (fresh from database) over initialSlotData (might be stale)
    // This ensures we show the latest vocabulary_cognates and sentence_frames
    let computedSlotData = null;
    
    // Compute dayData inside useMemo to avoid dependency issues
    const dayData = lessonPlan?.lesson_json?.days?.[day];
  
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
    if (dayData?.slots && Array.isArray(dayData.slots)) {
      if (targetSlotNumber !== undefined) {
        computedSlotData = dayData.slots.find((s: any) => s.slot_number === targetSlotNumber);
      }
      
      // If not found by slot number, try planSlotIndex as fallback
      if (!computedSlotData && typeof planSlotIndex === 'number') {
        const indexSlot = dayData.slots[planSlotIndex];
        if (indexSlot) {
          console.log('[LessonDetailView] Using planSlotIndex as fallback:', planSlotIndex);
          computedSlotData = indexSlot;
        }
      }
      
      // If still not found, try the schedule entry's slot number as last resort
      if (!computedSlotData && scheduleEntry.slot_number !== targetSlotNumber) {
        const scheduleSlotData = dayData.slots.find((s: any) => s.slot_number === scheduleEntry.slot_number);
        if (scheduleSlotData) {
          console.log('[LessonDetailView] Using schedule entry slot as fallback:', scheduleEntry.slot_number);
          computedSlotData = scheduleSlotData;
        }
      }
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
    
    // CRITICAL: Prioritize initialSlotData if it exists - it comes from plan matching
    // and should have the correct vocabulary/frames for the matched slot
    if (initialSlotData) {
      // If we found slotData by slot number but initialSlotData exists,
      // merge them: use initialSlotData's vocabulary/frames (from plan matching)
      // but keep other data from slotData (fresh from database)
      if (computedSlotData) {
        console.log('[LessonDetailView] Merging initialSlotData with slotData');
        computedSlotData = {
          ...computedSlotData,
          vocabulary_cognates: initialSlotData.vocabulary_cognates || computedSlotData.vocabulary_cognates,
          sentence_frames: initialSlotData.sentence_frames || computedSlotData.sentence_frames,
        };
      } else {
        // If no slotData found, use initialSlotData directly
        console.log('[LessonDetailView] Using initialSlotData as primary source');
        computedSlotData = initialSlotData;
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
      
      console.log('[LessonDetailView] Found slotData:', {
        slot_number: computedSlotData.slot_number,
        has_vocabulary: hasVocab,
        vocab_count: Array.isArray(computedSlotData.vocabulary_cognates) ? computedSlotData.vocabulary_cognates.length : 0,
        vocab_type: typeof computedSlotData.vocabulary_cognates,
        vocab_value: computedSlotData.vocabulary_cognates,
        has_sentence_frames: hasFrames,
        frames_count: Array.isArray(computedSlotData.sentence_frames) ? computedSlotData.sentence_frames.length : 0,
        frames_type: typeof computedSlotData.sentence_frames,
        frames_value: computedSlotData.sentence_frames,
        all_keys: Object.keys(computedSlotData),
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

    if (!computedSlotData) {
      console.warn('[LessonDetailView] No slotData found for slot:', slot, 'day:', day);
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
        <p key={`paragraph-${idx}`} className="text-sm leading-relaxed">
          {paragraph}
        </p>
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
          
          {/* Metadata with light gray background */}
          <div className="px-2 py-1 bg-muted/50 rounded-md">
            <div className="text-base text-muted-foreground">
              <span className="font-bold">{scheduleEntry.subject}</span>
              {scheduleEntry.grade && ` • Grade ${scheduleEntry.grade}`}
              {scheduleEntry.homeroom && ` • ${scheduleEntry.homeroom}`}
              {` • ${getDayName(day)}`}
              {formattedDate && ` • ${formattedDate}`}
              {` • ${scheduleEntry.start_time} - ${scheduleEntry.end_time}`}
            </div>
          </div>
          
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
                <div>{slotData.unit_lesson || 'N/A'}</div>
              </Card>

              {/* Objectives */}
              <Card className="p-4">
                <h3 className="font-semibold mb-3">Objectives</h3>
                <div className="space-y-3">
                  {slotData.objective?.content_objective && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        Content Objective
                      </div>
                      <div>{slotData.objective.content_objective}</div>
                    </div>
                  )}
                  {slotData.objective?.student_goal && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        Student Goal
                      </div>
                      <div>{slotData.objective.student_goal}</div>
                    </div>
                  )}
                  {slotData.objective?.wida_objective && (
                    <div>
                      <div className="text-xs font-semibold text-muted-foreground mb-1">
                        WIDA Objective
                      </div>
                      <div>{slotData.objective.wida_objective}</div>
                    </div>
                  )}
                </div>
              </Card>

              {/* Anticipatory Set */}
              <Card className="p-4">
                <h3 className="font-semibold mb-2">Anticipatory Set</h3>
                {slotData.anticipatory_set?.original_content && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Original
                    </div>
                    <div>{slotData.anticipatory_set.original_content}</div>
                  </div>
                )}
                {slotData.anticipatory_set?.bilingual_bridge && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Bilingual Bridge
                    </div>
                    <div>{slotData.anticipatory_set.bilingual_bridge}</div>
                  </div>
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
                        <span className={`text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded ${getCognateBadgeClasses(vocab.is_cognate, 'sm')}`}>
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
                    <div>{slotData.assessment.primary_assessment}</div>
                  </div>
                )}
                {slotData.assessment?.bilingual_check && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Bilingual Check
                    </div>
                    <div>{slotData.assessment.bilingual_check}</div>
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
                    {slotData.tailored_instruction.original_content && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground mb-1">
                          Original Content
                        </div>
                        <div className="space-y-2">
                          {renderParagraphs(slotData.tailored_instruction.original_content)}
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
                          <p className="text-sm text-muted-foreground">
                            {slotData.tailored_instruction.co_teaching_model.rationale}
                          </p>
                        )}
                        {slotData.tailored_instruction.co_teaching_model.wida_context && (
                          <p className="text-xs text-muted-foreground">
                            {slotData.tailored_instruction.co_teaching_model.wida_context}
                          </p>
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
                                    <li key={`implementation-note-${idx}`}>{note}</li>
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
                                            {phase.bilingual_teacher_role}
                                          </div>
                                        )}
                                        {phase?.primary_teacher_role && (
                                          <div>
                                            <span className="font-semibold text-foreground">Primary:</span>{' '}
                                            {phase.primary_teacher_role}
                                          </div>
                                        )}
                                        {phase?.details && (
                                          <div>
                                            <span className="font-semibold text-foreground">Details:</span>{' '}
                                            {phase.details}
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
                                    {support}
                                  </div>
                                );
                              }
                              return (
                                <div key={`ell-support-${support?.strategy_id || idx}`} className="rounded-md border border-border/60 p-3">
                                  <div className="text-sm font-semibold">
                                    {support?.strategy_name || support?.description || 'ELL Support'}
                                  </div>
                                  {support?.proficiency_levels && (
                                    <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                                      {support.proficiency_levels}
                                    </div>
                                  )}
                                  {support?.implementation && (
                                    <div className="text-sm text-muted-foreground">{support.implementation}</div>
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
                                <li key={`special-support-${idx}`}>{support}</li>
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
                              <li key={`material-${idx}`}>{material}</li>
                            ))}
                          </ul>
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
                    <div>{slotData.misconceptions.original_content}</div>
                  </div>
                )}
                {slotData.misconceptions?.linguistic_note && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Linguistic Note
                    </div>
                    <div className="space-y-2">
                      {typeof slotData.misconceptions.linguistic_note === 'string' ? (
                        <div>{slotData.misconceptions.linguistic_note}</div>
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
                              {slotData.misconceptions.linguistic_note.note}
                            </div>
                          )}
                          {slotData.misconceptions.linguistic_note.prevention_tip && (
                            <div>
                              <span className="font-semibold">Prevention Tip: </span>
                              {slotData.misconceptions.linguistic_note.prevention_tip}
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
                    <div>{slotData.misconceptions.linguistic_misconceptions}</div>
                  </div>
                )}
                {slotData.misconceptions?.content_misconceptions && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Content Misconceptions
                    </div>
                    <div>{slotData.misconceptions.content_misconceptions}</div>
                  </div>
                )}
                {/* Show if misconceptions is a string instead of object */}
                {typeof slotData.misconceptions === 'string' && slotData.misconceptions && (
                  <div>{slotData.misconceptions}</div>
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
                    <div>{slotData.homework.original_content}</div>
                  </div>
                )}
                {slotData.homework?.family_connection && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Family Connection
                    </div>
                    <div>{slotData.homework.family_connection}</div>
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

