import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { ArrowLeft, ChevronRight } from 'lucide-react';
import type { LessonStep, ScheduleEntry, WeeklyPlan, LessonModeSessionCreate, User } from '@lesson-api';
import { lessonApi, planApi, scheduleApi, lessonModeSessionApi, healthCheck } from '@lesson-api';
import { TimerAdjustmentDialog, TimerAdjustment } from './TimerAdjustmentDialog';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import { TimelineSidebar } from './TimelineSidebar';
import { CurrentStepInstructions } from './CurrentStepInstructions';
import { ResourceDisplayArea } from './ResourceDisplayArea';
import { resolvePlanIdFromScheduleEntry } from '../utils/planIdResolver';
import { useLessonTimer } from '../hooks/useLessonTimer';
import { recalculateStepDurations, RecalculatedStep } from '../utils/lessonStepRecalculation';
import { TopNavigationBar } from '@lesson-browser';

export interface LessonModeProps {
  currentUser: User | null;
  scheduleEntry?: ScheduleEntry;
  planId?: string;
  day?: string;
  slot?: number;
  weekOf?: string; // Week identifier (e.g., "11-24-11-28") for date calculation
  onExit?: (day?: string, slot?: number) => void;
}

export function LessonMode({ currentUser, scheduleEntry, planId, day, slot, weekOf, onExit }: LessonModeProps) {
  const [steps, setSteps] = useState<LessonStep[]>([]);
  const [adjustedSteps, setAdjustedSteps] = useState<RecalculatedStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const autoAdvance = true;
  const [adjustDialogOpen, setAdjustDialogOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastSaveTimeRef = useRef<number>(0);
  const isSavingRef = useRef<boolean>(false);
  const rateLimitErrorRef = useRef<boolean>(false);
  const isInitialMountRef = useRef(true); // Track if this is the initial mount
  const adjustmentMadeRef = useRef<number | null>(null); // Track step index that was adjusted
  const sliderAdjustmentTimeRef = useRef<number | null>(null); // Store exact dragged time from slider
  const wasRunningBeforeSliderAdjustRef = useRef<boolean>(false); // Track if timer was running before slider adjustment
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [instructionsCollapsed, setInstructionsCollapsed] = useState(false);
  const [lessonPlanData, setLessonPlanData] = useState<WeeklyPlan | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Determine lesson context
  const [currentLesson, setCurrentLesson] = useState<ScheduleEntry | null>(scheduleEntry || null);
  
  // Calculate if we're in Live Mode (within 30 mins of slot time)
  const isLiveMode = useMemo(() => {
    if (!currentLesson || !currentLesson.start_time || !currentLesson.end_time) {
      return false;
    }
    
    try {
      const now = new Date();
      const startTimeParts = currentLesson.start_time.split(':');
      const endTimeParts = currentLesson.end_time.split(':');
      
      if (startTimeParts.length < 2 || endTimeParts.length < 2) {
        return false;
      }
      
      const [startH, startM] = startTimeParts.map(Number);
      const [endH, endM] = endTimeParts.map(Number);
      
      if (isNaN(startH) || isNaN(startM) || isNaN(endH) || isNaN(endM)) {
        return false;
      }
      
      const start = new Date(now);
      start.setHours(startH, startM, 0, 0);
      
      const end = new Date(now);
      end.setHours(endH, endM, 0, 0);
      
      // Check if within 30 minutes before start or during lesson
      const thirtyMinsBefore = new Date(start.getTime() - 30 * 60 * 1000);
      
      return now >= thirtyMinsBefore && now <= end;
    } catch (error) {
      console.error('Error calculating isLiveMode:', error);
      return false;
    }
  }, [currentLesson]);
  const [lessonPlanId, setLessonPlanId] = useState<string | null>(planId || null);
  const [lessonDay, setLessonDay] = useState<string | null>(day || null);
  const [lessonSlot, setLessonSlot] = useState<number | null>(slot || null);

  // Use timer hook for automatic synchronization
  const {
    timerState,
    start: startTimer,
    stop: stopTimer,
    reset: resetTimer,
    changeStep: changeStepTimer,
  } = useLessonTimer({
    steps,
    scheduleEntry: currentLesson,
    autoSync: true,
    autoAdvance: autoAdvance,
    isLiveMode: isLiveMode,
    onStepComplete: (stepIndex) => {
      console.log(`Step ${stepIndex + 1} completed`);
      // Auto-advance is handled by the hook based on autoAdvance setting
    },
    onLessonComplete: () => {
      console.log('Lesson completed!');
      // Could show a completion message here
    },
  });

  // Initialize lesson context when component mounts or props change
  useEffect(() => {
    const initializeLesson = async () => {
      if (!currentUser) {
        setError('No user selected');
        setLoading(false);
        return;
      }

      try {
        // Use props if provided, otherwise use state
        let entry = scheduleEntry || currentLesson;

        // If no schedule entry provided, get current lesson
        if (!entry) {
          const response = await scheduleApi.getCurrentLesson(currentUser.id);
          if (response.data) {
            entry = response.data;
            setCurrentLesson(entry);
          } else {
            setError('No current lesson found');
            setLoading(false);
            return;
          }
        } else if (!currentLesson && entry) {
          setCurrentLesson(entry);
        }

        // If planId and slot are provided, use them directly as they are authoritative
        // Otherwise fallback to state or resolving from schedule entry
        let resolvedPlanId = planId || lessonPlanId;
        let resolvedDay = day || lessonDay;
        let resolvedSlot = slot !== undefined ? slot : lessonSlot;
        
        // Only attempt to resolve from schedule entry if we don't have explicit props
        // or if we're missing critical information
        const hasExplicitProps = !!planId && slot !== undefined;

        if (entry && !hasExplicitProps) {
          // Fetch plans to pass to resolver
          const plansResponse = await planApi.list(currentUser.id, 100, currentUser.id);
          const plans = plansResponse.data || [];

          // Resolve plan ID, day, and slot from schedule entry (authoritative)
          const resolved = await resolvePlanIdFromScheduleEntry(entry, currentUser.id, plans);

          if (resolved) {
            // Always use resolved values - they are authoritative
            resolvedPlanId = resolved.planId;
            resolvedDay = resolved.day;
            resolvedSlot = resolved.slot;

            // Always update state with resolved values
            // This ensures we use the correct slot even if props were incorrect
            setLessonPlanId(resolvedPlanId);
            setLessonDay(resolvedDay);
            setLessonSlot(resolvedSlot);
          } else if (!resolvedPlanId || !resolvedDay || resolvedSlot === null) {
            // Only error if we don't have fallback values
            setError('Could not find matching lesson plan for this schedule entry');
            setLoading(false);
            return;
          }
        } else if (hasExplicitProps) {
             // We have explicit props, update state to match
             setLessonPlanId(resolvedPlanId);
             setLessonDay(resolvedDay);
             setLessonSlot(resolvedSlot);
        }

        // Ensure we have all required values
        if (!resolvedPlanId || !resolvedDay || resolvedSlot === null) {
          setError('Missing lesson plan information');
          setLoading(false);
          return;
        }

        // Load steps once we have plan ID, day, and slot
        await loadSteps(resolvedPlanId, resolvedDay, resolvedSlot);

        // Load active session if exists
        if (currentUser) {
          await loadActiveSession(currentUser.id, resolvedPlanId, resolvedDay, resolvedSlot);
        }
      } catch (err: any) {
        console.error('Failed to initialize lesson:', err);
        setError(err.message || 'Failed to load lesson');
        setLoading(false);
      }
    };

    initializeLesson();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser, scheduleEntry, planId, day, slot]);

  // Load active session and restore state
  const loadActiveSession = async (
    userId: string,
    planId: string,
    day: string,
    slot: number
  ) => {
    try {
      const response = await lessonModeSessionApi.getActive(
        userId,
        { lesson_plan_id: planId, day_of_week: day, slot_number: slot },
        userId
      );

      if (response.data && steps.length > 0) {
        const session = response.data;
        setSessionId(session.id);

        // Restore timer state
        if (session.current_step_index < steps.length) {
          changeStepTimer(session.current_step_index);
        }

        // Restore adjusted durations if present
        if (session.adjusted_durations) {
          const updatedSteps = steps.map((step, index) => {
            const adjustedDur = session.adjusted_durations?.[index.toString()];
            if (adjustedDur !== undefined) {
              return {
                ...step,
                duration_minutes: Math.ceil(adjustedDur / 60),
              };
            }
            return step;
          });
          setSteps(updatedSteps);
        }

        console.log('Restored session state:', session);
      }
    } catch (err: any) {
      console.error('Failed to load active session:', err);
      // Don't show error - session might not exist yet
    }
  };

  const loadSteps = async (planId: string, day: string, slot: number) => {
    try {
      setLoading(true);
      setError(null);

      // Check if backend is accessible (only in browser, Tauri handles this differently)
      if (typeof window !== 'undefined' && !('__TAURI_INTERNALS__' in window)) {
        try {
          await healthCheck();
        } catch (healthErr: any) {
          console.error('Backend health check failed:', healthErr);
          const errorMsg = healthErr?.message || 'Unknown error';
          if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError') || errorMsg.includes('CORS')) {
            setError('Cannot connect to backend server. Please ensure the backend is running on port 8000 and accessible at http://localhost:8000');
          } else {
            setError(`Backend connection error: ${errorMsg}`);
          }
          setLoading(false);
          return;
        }
      }

      // Load lesson plan data to access objective
      try {
        console.log('[LessonMode] Loading lesson plan data for planId:', planId, 'day:', day, 'slot:', slot);
        // Use lessonApi.getPlanDetail instead of planApi.getWeeklyPlan
        const planResponse = await lessonApi.getPlanDetail(planId, currentUser?.id);
        if (planResponse.data) {
          console.log('[LessonMode] Lesson plan data loaded:', planResponse.data);
          console.log('[LessonMode] Has lesson_json:', !!planResponse.data.lesson_json);
          console.log('[LessonMode] Requested day:', day, 'slot:', slot);
          // Convert LessonPlanDetail to WeeklyPlan format
          // WeeklyPlan interface expects lesson_json but it's not in the base interface
          // We'll create a compatible object
          const weeklyPlan: WeeklyPlan & { lesson_json?: any } = {
            id: planResponse.data.id,
            user_id: planResponse.data.user_id || '',
            week_of: planResponse.data.week_of || '',
            generated_at: planResponse.data.generated_at || '',
            status: planResponse.data.status as any || 'completed',
            lesson_json: planResponse.data.lesson_json,
          };
          setLessonPlanData(weeklyPlan as WeeklyPlan);
        } else {
          console.warn('[LessonMode] No data in plan response');
        }
      } catch (planErr) {
        console.error('[LessonMode] Failed to load lesson plan data:', planErr);
        // Continue even if plan data fails to load
      }

      // Try to get existing steps
      const response = await lessonApi.getLessonSteps(planId, day, slot, currentUser?.id);

      if (response.data && response.data.length > 0) {
        setSteps(response.data);
        // Initialize adjusted steps with original durations
        const initialAdjusted: RecalculatedStep[] = response.data.map(step => ({
          ...step,
          adjustedDuration: step.duration_minutes * 60,
          originalDuration: step.duration_minutes * 60,
        }));
        setAdjustedSteps(initialAdjusted);
      } else {
        // No steps found, try to generate them
        try {
          const generateResponse = await lessonApi.generateLessonSteps(planId, day, slot, currentUser?.id);
          if (generateResponse.data && generateResponse.data.length > 0) {
            setSteps(generateResponse.data);
            // Initialize adjusted steps with original durations
            const initialAdjusted: RecalculatedStep[] = generateResponse.data.map(step => ({
              ...step,
              adjustedDuration: step.duration_minutes * 60,
              originalDuration: step.duration_minutes * 60,
            }));
            setAdjustedSteps(initialAdjusted);
          } else {
            setError('No lesson steps available. Please generate a lesson plan first.');
          }
        } catch (genErr: any) {
          const errorMsg = genErr.message || 'Unknown error';
          if (errorMsg.includes('phase_plan') || errorMsg.includes('No phase_plan')) {
            console.log('[LessonMode] No phase_plan found, using default lesson steps');
            // Use fallback default steps when phase_plan is missing
            const { createDefaultLessonSteps } = await import('../utils/defaultLessonSteps');
            const defaultSteps = createDefaultLessonSteps(planId, day, slot);
            setSteps(defaultSteps);
            // Initialize adjusted steps with original durations
            const initialAdjusted: RecalculatedStep[] = defaultSteps.map(step => ({
              ...step,
              adjustedDuration: step.duration_minutes * 60,
              originalDuration: step.duration_minutes * 60,
            }));
            setAdjustedSteps(initialAdjusted);
            console.log('[LessonMode] Created default lesson steps:', defaultSteps.length, 'steps');
          } else {
            setError(`Failed to generate steps: ${errorMsg}`);
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to load steps:', err);
      setError(err.message || 'Failed to load lesson steps');
    } finally {
      setLoading(false);
    }
  };

  const handleStepChange = (newIndex: number) => {
    if (newIndex >= 0 && newIndex < steps.length) {
      changeStepTimer(newIndex);
    }
  };

  const handleTimerStart = () => {
    startTimer();
  };

  const handleTimerStop = () => {
    stopTimer();
  };

  const handleTimerReset = () => {
    resetTimer();
  };

  const handleTimeAdjust = (newRemainingTime: number) => {
    // When user drags the slider, adjust the current step's duration
    const currentIndex = timerState.currentStepIndex;
    const wasRunning = timerState.isRunning; // Remember if timer was running
    
    // Store the exact remaining time the user dragged to
    sliderAdjustmentTimeRef.current = newRemainingTime;
    // Store if timer was running so we can restart it after adjustment
    wasRunningBeforeSliderAdjustRef.current = wasRunning;
    
    // Use exact time in minutes (as decimal, e.g., 1.8 minutes for 1:48, not rounded up)
    const exactDurationMinutes = newRemainingTime / 60;
    
    // Stop the timer if it's running so the adjustment takes effect
    if (wasRunning) {
      stopTimer();
    }
    
    // Use the same adjustment logic as the dialog, but with exact minutes (not rounded)
    handleTimerAdjust({ 
      type: 'set', 
      amount: exactDurationMinutes 
    });
    
    // Mark that we made an adjustment
    adjustmentMadeRef.current = currentIndex;
  };

  const handleStepComplete = (stepIndex: number) => {
    // Mark step as complete and advance to next
    if (stepIndex < steps.length - 1) {
      handleStepChange(stepIndex + 1);
    } else {
      // Last step - could show completion message
      console.log('Lesson completed!');
    }
  };

  const handleTimerAdjust = (adjustment: TimerAdjustment) => {
    const currentIndex = timerState.currentStepIndex;
    // Always pass the original steps array as the source of truth for originalDuration
    // This ensures that adjustments are always calculated from the true original durations
    const recalculated = recalculateStepDurations(
      adjustedSteps.length > 0 ? adjustedSteps : steps, 
      currentIndex, 
      adjustment,
      steps // Pass original steps as the source of truth
    );

    console.log('[LessonMode] Timer adjustment:', {
      type: adjustment.type,
      amount: adjustment.amount,
      currentIndex,
      originalStepDuration: steps[currentIndex]?.duration_minutes,
      adjustedStepsLength: adjustedSteps.length,
      currentStepDurationBefore: adjustedSteps.length > 0 ? adjustedSteps[currentIndex]?.duration_minutes : steps[currentIndex]?.duration_minutes,
      recalculatedStepDuration: recalculated[currentIndex]?.duration_minutes,
      recalculatedOriginalDuration: recalculated[currentIndex]?.originalDuration / 60,
      recalculatedAdjustedDuration: recalculated[currentIndex]?.adjustedDuration / 60,
    });

    // Update adjusted steps
    setAdjustedSteps(recalculated);

    // Update steps array with adjusted durations FIRST
    // This ensures the timer hook picks up the new durations
    const updatedSteps: LessonStep[] = recalculated.map(step => ({
      ...step,
      duration_minutes: step.duration_minutes, // Already updated in recalculation
    }));
    setSteps(updatedSteps);

    // Mark that we made an adjustment so useEffect can reset timer and start it
    if (adjustment.type === 'skip' && adjustment.targetStep !== undefined) {
      changeStepTimer(adjustment.targetStep);
    } else {
      // Store the step index that was adjusted
      // The useEffect will reset and start the timer after steps are updated
      adjustmentMadeRef.current = currentIndex;
    }

    // Save state after adjustment
    debouncedSaveSession();
  };

  // Reset timer after steps update from an adjustment
  useEffect(() => {
    if (adjustmentMadeRef.current !== null && steps.length > 0) {
      const adjustedIndex = adjustmentMadeRef.current;
      const wasSliderAdjustment = sliderAdjustmentTimeRef.current !== null;
      const exactTime = sliderAdjustmentTimeRef.current;
      
      adjustmentMadeRef.current = null; // Clear the flag
      sliderAdjustmentTimeRef.current = null; // Clear the slider time
      
      // Reset timer now that steps have been updated
      if (steps[adjustedIndex]) {
        const currentStep = steps[adjustedIndex];
        const newDurationMinutes = currentStep.duration_minutes;
        const newDurationSeconds = newDurationMinutes * 60;
        
        console.log('[LessonMode] Resetting timer after adjustment:', {
          stepIndex: adjustedIndex,
          stepName: currentStep.step_name,
          durationMinutes: newDurationMinutes,
          durationSeconds: newDurationSeconds,
          wasSliderAdjustment,
          exactTime,
          stepsArrayLength: steps.length,
          adjustedStepsLength: adjustedSteps.length,
          timerStateRemainingTime: timerState.remainingTime,
        });
        
        // Reset timer - it will read from steps array which should have the updated duration
        // The reset function uses steps[adjustedIndex].duration_minutes, so it should get the updated value
        // Use a small delay to ensure steps state has propagated
        setTimeout(() => {
          resetTimer(adjustedIndex);
          
          // If this was a slider adjustment, update the step duration to match the exact dragged time
          if (wasSliderAdjustment && exactTime !== null) {
            // Update the step's duration to match the exact dragged time (in minutes, can be decimal)
            const exactMinutes = exactTime / 60;
            const updatedSteps = steps.map((step, idx) => 
              idx === adjustedIndex 
                ? { ...step, duration_minutes: exactMinutes }
                : step
            );
            setSteps(updatedSteps);
            
            // Reset again with the exact time
            setTimeout(() => {
              resetTimer(adjustedIndex);
              
              // If timer was running before slider adjustment, restart it
              if (wasRunningBeforeSliderAdjustRef.current) {
                setTimeout(() => {
                  console.log('[LessonMode] Restarting timer after slider adjustment');
                  startTimer();
                }, 50);
              }
            }, 50);
          } else {
            // Start the timer after reset (only for dialog adjustments, not slider)
            setTimeout(() => {
              console.log('[LessonMode] Starting timer after reset');
              startTimer();
            }, 100);
          }
        }, 50);
      }
    }
  }, [steps, adjustedSteps, resetTimer, startTimer, timerState.remainingTime]);

  // Save session state (debounced to avoid excessive API calls)
  const saveSession = useCallback(async () => {
    if (!currentUser || !lessonPlanId || lessonDay === null || lessonSlot === null || steps.length === 0) {
      return;
    }

    // Prevent concurrent saves
    if (isSavingRef.current) {
      return;
    }

    // Skip save if we're at rate limit (wait for cooldown)
    if (rateLimitErrorRef.current) {
      const timeSinceRateLimit = Date.now() - lastSaveTimeRef.current;
      if (timeSinceRateLimit < 60000) { // Wait 60 seconds after rate limit
        return;
      }
      // Reset rate limit flag after cooldown
      rateLimitErrorRef.current = false;
    }

    isSavingRef.current = true;
    try {
      const adjustedDurations: Record<string, number> = {};
      adjustedSteps.forEach((step, index) => {
        if (step.adjustedDuration !== step.originalDuration) {
          // Backend expects integers (whole seconds), so round to nearest integer
          adjustedDurations[index.toString()] = Math.round(step.adjustedDuration);
        }
      });

      // Validate required fields before creating session
      if (!lessonPlanId || !lessonDay || lessonSlot === null || lessonSlot === undefined) {
        console.error('[LessonMode] Missing required fields for session:', {
          lessonPlanId,
          lessonDay,
          lessonSlot,
        });
        return;
      }

      const sessionData: LessonModeSessionCreate = {
        user_id: currentUser.id,
        lesson_plan_id: lessonPlanId,
        schedule_entry_id: currentLesson?.id || null,
        day_of_week: lessonDay,
        slot_number: lessonSlot,
        current_step_index: timerState.currentStepIndex ?? 0,
        remaining_time: Math.round(timerState.remainingTime ?? 0), // Ensure integer
        is_running: timerState.isRunning ?? false,
        is_paused: timerState.isPaused ?? false,
        is_synced: timerState.isSynced ?? false,
        timer_start_time: timerState.timerStartTime?.toISOString() || null,
        paused_at: timerState.pausedAt !== null ? Math.round(timerState.pausedAt) : null, // Ensure integer
        adjusted_durations: Object.keys(adjustedDurations).length > 0 ? adjustedDurations : null,
      };
      
      console.log('[LessonMode] Creating session with data:', sessionData);

      const response = await lessonModeSessionApi.create(sessionData, currentUser.id);
      if (response.data) {
        setSessionId(response.data.id);
        lastSaveTimeRef.current = Date.now();
        rateLimitErrorRef.current = false; // Reset rate limit flag on success
      }
    } catch (err: any) {
      // Handle rate limit errors
      if (err?.message?.includes('429') || err?.message?.includes('Rate limit')) {
        console.warn('[LessonMode] Rate limit hit, pausing saves for 65 seconds');
        rateLimitErrorRef.current = true;
        lastSaveTimeRef.current = Date.now(); // Track when rate limit occurred
        // Silently handle rate limit - will retry after cooldown
        return;
      }
      console.error('Failed to save session:', err);
      // Don't show error to user - persistence failures shouldn't block UI
    } finally {
      isSavingRef.current = false;
    }
  }, [
    currentUser,
    lessonPlanId,
    lessonDay,
    lessonSlot,
    currentLesson,
    timerState,
    adjustedSteps,
    steps.length,
  ]);

  // Debounced save function (saves max once every 30 seconds to avoid rate limits)
  const debouncedSaveSession = useCallback(() => {
    // Skip if we're at rate limit
    if (rateLimitErrorRef.current) {
      const timeSinceRateLimit = Date.now() - lastSaveTimeRef.current;
      if (timeSinceRateLimit < 65000) { // Wait 65 seconds after rate limit (1 minute + buffer)
        return;
      }
      // Reset rate limit flag after cooldown
      rateLimitErrorRef.current = false;
    }

    const now = Date.now();
    const timeSinceLastSave = now - lastSaveTimeRef.current;
    const SAVE_INTERVAL = 30000; // 30 seconds (increased to reduce rate limit errors)

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    if (timeSinceLastSave >= SAVE_INTERVAL) {
      // Save immediately if enough time has passed
      saveSession();
    } else {
      // Schedule save after remaining time
      saveTimeoutRef.current = setTimeout(() => {
        saveSession();
      }, SAVE_INTERVAL - timeSinceLastSave);
    }
  }, [saveSession]);

  // Auto-save session periodically and on significant events
  // Only save on significant state changes, not on every timer tick
  useEffect(() => {
    if (steps.length === 0 || !currentUser) return;

    // Skip save on initial mount - only save after user interactions
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      return;
    }

    // Skip save if we're already rate limited
    if (rateLimitErrorRef.current) {
      return;
    }

    // Save on significant state changes (debounced)
    // Note: We intentionally don't include remainingTime in dependencies
    // because it changes every second and would trigger too many saves
    debouncedSaveSession();

    // Cleanup timeout on unmount
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [
    timerState.currentStepIndex, // Save on step change
    timerState.isRunning, // Save on play/pause
    timerState.isPaused, // Save on pause state change
    // Don't include remainingTime - it changes every second and causes rate limits
    steps.length,
    currentUser,
    // Don't include debouncedSaveSession in deps - it's stable via useCallback
  ]);

  // Save session on component unmount (exit)
  useEffect(() => {
    return () => {
      // Skip save on unmount if we're at rate limit to avoid spamming API
      if (rateLimitErrorRef.current) {
        console.log('[LessonMode] Skipping unmount save - rate limited');
        return;
      }
      
      // Check time since last save - don't save if we just saved recently
      const timeSinceLastSave = Date.now() - lastSaveTimeRef.current;
      if (timeSinceLastSave < 5000) { // Skip if saved in last 5 seconds
        console.log('[LessonMode] Skipping unmount save - saved recently');
        return;
      }
      
      // Save final state on unmount (don't end session, just save)
      // This allows resuming if the user accidentally navigates away or refreshes
      // Skip save if we're already at rate limit or if save is in progress
      if (sessionId && currentUser && !isSavingRef.current) {
        // Use a non-blocking save that silently handles rate limit errors
        saveSession().catch((err) => {
          // Silently ignore rate limit errors on unmount
          if (!err?.message?.includes('429') && !err?.message?.includes('Rate limit')) {
            console.error('Failed to save session on unmount:', err);
          }
        });
      }
    };
  }, [sessionId, currentUser, saveSession]);

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Format time as HH:MM:SS
  const formatTime = (date: Date): string => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  // Format date as MM/DD/YY
  const formatDate = (date: Date): string => {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${month}/${day}/${year}`;
  };

  // Get day name (capitalize first letter)
  const getDayName = (dayStr: string): string => {
    if (!dayStr) return '';
    return dayStr.charAt(0).toUpperCase() + dayStr.slice(1);
  };

  // Calculate lesson date from week_of and day_of_week
  const formattedDate = useMemo((): string | null => {
    // Priority: weekOf prop > currentLesson.week_of > lessonPlanData.week_of
    const weekOfToUse = weekOf || currentLesson?.week_of || lessonPlanData?.week_of;
    const dayToUse = day || currentLesson?.day_of_week || lessonDay;
    
    console.log('[LessonMode] Calculating formatted date:', {
      weekOfProp: weekOf,
      weekOfToUse,
      dayToUse,
      day,
      currentLessonDay: currentLesson?.day_of_week,
      lessonDay,
      hasCurrentLesson: !!currentLesson,
      hasLessonPlanData: !!lessonPlanData,
      currentLessonWeekOf: currentLesson?.week_of,
      lessonPlanWeekOf: lessonPlanData?.week_of,
      lessonPlanDataId: lessonPlanData?.id
    });
    
    if (!weekOfToUse || !dayToUse) {
      console.log('[LessonMode] Missing date info - will retry when data loads:', { 
        weekOfProp: weekOf,
        weekOfToUse, 
        dayToUse, 
        hasCurrentLesson: !!currentLesson, 
        hasLessonPlanData: !!lessonPlanData,
        currentLessonWeekOf: currentLesson?.week_of,
        lessonPlanDataWeekOf: lessonPlanData?.week_of
      });
      return null;
    }
    
    try {
      // weekOf format is "MM-DD-MM-DD" (Monday to Friday)
      const parts = weekOfToUse.split('-');
      if (parts.length < 2) {
        console.error('[LessonMode] Invalid week_of format (not enough parts):', weekOfToUse);
        return null;
      }
      
      const [startMonth, startDay] = parts.slice(0, 2).map(Number);
      
      if (isNaN(startMonth) || isNaN(startDay) || startMonth < 1 || startMonth > 12 || startDay < 1 || startDay > 31) {
        console.error('[LessonMode] Invalid month or day:', { startMonth, startDay, weekOfToUse });
        return null;
      }
      
      const year = new Date().getFullYear();
      const mondayDate = new Date(year, startMonth - 1, startDay);
      
      if (isNaN(mondayDate.getTime())) {
        console.error('[LessonMode] Invalid mondayDate created:', { year, startMonth, startDay });
        return null;
      }
      
      const dayIndex = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].indexOf(dayToUse.toLowerCase());
      if (dayIndex === -1) {
        console.error('[LessonMode] Invalid day:', dayToUse);
        return null;
      }
      
      const lessonDate = new Date(mondayDate);
      lessonDate.setDate(mondayDate.getDate() + dayIndex);
      
      if (isNaN(lessonDate.getTime())) {
        console.error('[LessonMode] Invalid lessonDate after calculation');
        return null;
      }
      
      const formatted = formatDate(lessonDate);
      console.log('[LessonMode] ✅ Formatted date SUCCESS:', formatted, 'from lessonDate:', lessonDate.toISOString());
      return formatted;
    } catch (error) {
      console.error('[LessonMode] Error calculating lesson date:', error);
      return null;
    }
  }, [weekOf, currentLesson?.week_of, lessonPlanData?.week_of, day, currentLesson?.day_of_week, lessonDay, formatDate, lessonPlanData?.id]);

  // Get day abbreviation (MON, TUE, WED, etc.)
  const getDayAbbreviation = (date: Date): string => {
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    return days[date.getDay()];
  };

  // Handle exit - end session
  const handleExit = useCallback(async () => {
    if (sessionId && currentUser) {
      try {
        await lessonModeSessionApi.end(sessionId, currentUser.id);
      } catch (err) {
        console.error('Failed to end session:', err);
      }
    }
    if (onExit) {
      // Pass the resolved day and slot back to the parent
      onExit(lessonDay || undefined, lessonSlot || undefined);
    }
  }, [sessionId, currentUser, onExit, lessonDay, lessonSlot]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading lesson...</div>
          <div className="text-sm text-muted-foreground">Preparing your lesson steps</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-lg font-semibold text-destructive mb-2">Error</div>
          <div className="text-muted-foreground mb-4">{error}</div>
          {onExit && (
            <Button onClick={() => onExit(day, slot)} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          )}
        </div>
      </Card>
    );
  }

  if (steps.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">No Steps Available</div>
          <div className="text-muted-foreground mb-4">
            This lesson doesn't have any steps yet. Generate a lesson plan first.
          </div>
          {onExit && (
            <Button onClick={() => onExit(day, slot)} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          )}
        </div>
      </Card>
    );
  }

  const currentStep = steps[timerState.currentStepIndex] || steps[0];
  
  // Safety check - should not happen due to earlier checks, but defensive coding
  if (!currentStep) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-lg font-semibold text-destructive mb-2">Error</div>
          <div className="text-muted-foreground mb-4">
            Unable to load current step. Please try again.
          </div>
          {onExit && (
            <Button onClick={() => onExit(day, slot)} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          )}
        </div>
      </Card>
    );
  }
  
  const totalDuration = currentStep.duration_minutes * 60;

  // Always use the true original duration from the steps array, not from adjustedSteps
  // This ensures the dialog always shows the correct original duration even after adjustments
  const originalStep = steps[timerState.currentStepIndex] || currentStep;
  const originalDuration = originalStep.duration_minutes * 60;

  return (
    <div className="h-full flex flex-col">
      {/* Top Bar */}
      <TopNavigationBar
        currentTime={currentTime}
        formatTime={formatTime}
        formatDate={formatDate}
        getDayAbbreviation={getDayAbbreviation}
        lessonMetadata={(() => {
          const metadata = {
            subject: currentLesson?.subject || undefined,
            grade: currentLesson?.grade || undefined,
            homeroom: currentLesson?.homeroom || undefined,
            start_time: currentLesson?.start_time || undefined,
            end_time: currentLesson?.end_time || undefined,
            day_of_week: (day || currentLesson?.day_of_week || lessonDay) ? getDayName(day || currentLesson?.day_of_week || lessonDay || '') : undefined,
            formatted_date: formattedDate || undefined,
          };
          console.log('[LessonMode] Passing lessonMetadata to TopNavigationBar:', metadata);
          return metadata;
        })()}
        viewMode="lesson-mode"
        onExitLessonMode={onExit ? handleExit : undefined}
        showLessonModeButton={true}
      />

      {/* Main Content Area - Three Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Timeline Sidebar (1/5 width, collapsible) */}
        <TimelineSidebar
          steps={steps}
          currentStepIndex={timerState.currentStepIndex}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onStepComplete={handleStepComplete}
          onStepSelect={handleStepChange}
          timerState={timerState}
          onTimerStart={handleTimerStart}
          onTimerStop={handleTimerStop}
          onTimerReset={handleTimerReset}
          onTimerAdjust={() => setAdjustDialogOpen(true)}
          onTimeAdjust={handleTimeAdjust}
          totalDuration={totalDuration}
          originalDuration={originalDuration}
        />

        {/* Middle: Current Step Instructions (narrower - about half the previous size) */}
        {instructionsCollapsed ? (
          <div className="w-12 border-r bg-card flex flex-col items-center py-4 h-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setInstructionsCollapsed(false)}
              className="p-2"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <div className="w-1/6 h-full flex flex-col" style={{ minWidth: '200px', maxWidth: '300px' }}>
            <CurrentStepInstructions
              step={currentStep}
              currentStepIndex={timerState.currentStepIndex}
              totalSteps={steps.length}
              onPrevious={() => handleStepChange(timerState.currentStepIndex - 1)}
              onNext={() => handleStepChange(timerState.currentStepIndex + 1)}
              onGoToBeginning={() => handleStepChange(0)}
              isCollapsed={instructionsCollapsed}
              onToggleCollapse={() => setInstructionsCollapsed(!instructionsCollapsed)}
            />
          </div>
        )}

        {/* Right: Resources Area (remaining width) */}
        <div className="flex-1 flex flex-col min-w-0">
          <ResourceDisplayArea
            currentStep={currentStep}
            steps={steps}
            lessonPlanData={lessonPlanData}
            day={lessonDay || ''}
            slot={lessonSlot || 0}
          />
        </div>
      </div>

      {/* Timer Adjustment Dialog */}
      <TimerAdjustmentDialog
        open={adjustDialogOpen}
        onOpenChange={setAdjustDialogOpen}
        currentStep={currentStep}
        currentStepIndex={timerState.currentStepIndex}
        totalSteps={steps.length}
        currentRemainingTime={timerState.remainingTime}
        originalDuration={originalDuration}
        onAdjust={handleTimerAdjust}
      />
    </div>
  );
}

