import { useState, useEffect, useRef, useCallback } from 'react';
import type { LessonStep, ScheduleEntry } from '@lesson-api';
import { playEarlyWarningSound, playWarningSound, playWarningDoubleSound, playCompletionSound, playStartSound } from '../utils/timerSounds';

export type ScheduleStatus = 'past' | 'current' | 'future';

export interface TimerState {
  remainingTime: number; // seconds
  isRunning: boolean;
  isPaused: boolean;
  isSynced: boolean; // true if synced with actual time
  currentStepIndex: number;
  lessonStartTime: Date | null; // when lesson started (from schedule)
  timerStartTime: Date | null; // when timer was started
  pausedAt: number | null; // seconds remaining when paused
  scheduleStatus: ScheduleStatus; // past, current, or future
  performanceStartTime: number | null; // performance.now() when timer started (for Android accuracy)
}

export interface UseLessonTimerOptions {
  steps: LessonStep[];
  scheduleEntry: ScheduleEntry | null;
  autoSync?: boolean; // automatically sync with actual time
  autoAdvance?: boolean; // automatically advance to next step when timer expires
  isLiveMode?: boolean; // if false, disable wall-clock sync (Preview Mode)
  onStepComplete?: (stepIndex: number) => void; // called when a step completes
  onLessonComplete?: () => void; // called when all steps complete
}

export function useLessonTimer({
  steps,
  scheduleEntry,
  autoSync = true,
  autoAdvance = true,
  isLiveMode = true,
  onStepComplete,
  onLessonComplete,
}: UseLessonTimerOptions) {
  const [timerState, setTimerState] = useState<TimerState>({
    remainingTime: 0,
    isRunning: false,
    isPaused: false,
    isSynced: false,
    currentStepIndex: 0,
    lessonStartTime: null,
    timerStartTime: null,
    pausedAt: null,
    scheduleStatus: 'future',
    performanceStartTime: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const originalStepDurations = useRef<Map<number, number>>(new Map());
  const stepsRef = useRef<LessonStep[]>(steps);
  const remainingTimeRef = useRef<number>(0);
  const soundTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const soundActiveRef = useRef<boolean>(false);
  const isRunningRef = useRef<boolean>(false);
  const initializationPhaseRef = useRef<boolean>(true); // Track initialization phase to prevent step 1 bug
  // Use refs for callbacks to prevent effect re-runs
  const onStepCompleteRef = useRef(onStepComplete);
  const onLessonCompleteRef = useRef(onLessonComplete);
  const autoAdvanceRef = useRef(autoAdvance);
  const advanceToStepRef = useRef<((prev: TimerState, nextIndex: number) => TimerState) | null>(null);
  
  // Keep stepsRef in sync with steps
  useEffect(() => {
    stepsRef.current = steps;
  }, [steps]);
  
  // Keep remainingTimeRef in sync with timerState.remainingTime
  useEffect(() => {
    remainingTimeRef.current = timerState.remainingTime;
  }, [timerState.remainingTime]);

  // Keep isRunningRef in sync with timerState.isRunning
  useEffect(() => {
    isRunningRef.current = timerState.isRunning;
  }, [timerState.isRunning]);

  // Keep callback refs in sync
  useEffect(() => {
    onStepCompleteRef.current = onStepComplete;
    onLessonCompleteRef.current = onLessonComplete;
    autoAdvanceRef.current = autoAdvance;
  }, [onStepComplete, onLessonComplete, autoAdvance]);

  /**
   * Gets the lesson start time from schedule entry.
   */
  const getLessonStartTime = useCallback((entry: ScheduleEntry, now: Date): Date => {
    const [hours, minutes] = entry.start_time.split(':').map(Number);
    const startTime = new Date(now);
    startTime.setHours(hours, minutes, 0, 0);

    // If start time is earlier today, assume it's today
    // If start time is later today, it's today
    // Otherwise, we'd need to check if lesson is tomorrow
    if (startTime > now) {
      // Start time hasn't happened yet today
      return startTime;
    }

    // Check if lesson has already ended today
    const [endHours, endMinutes] = entry.end_time.split(':').map(Number);
    const endTime = new Date(now);
    endTime.setHours(endHours, endMinutes, 0, 0);

    if (endTime < now) {
      // Lesson has ended, return start time from today
      return startTime;
    }

    // Lesson is active or hasn't started yet today
    return startTime;
  }, []);

  /**
   * Calculates the current step index based on elapsed time since lesson start.
   */
  const calculateCurrentStepIndex = useCallback((
    stepList: LessonStep[],
    entry: ScheduleEntry | null,
    sync: boolean
  ): number => {
    // In Preview Mode, always start at first step
    if (!sync || !entry || stepList.length === 0) {
      return 0;
    }

    const now = new Date();
    const lessonStart = getLessonStartTime(entry, now);
    const elapsedSeconds = Math.max(0, (now.getTime() - lessonStart.getTime()) / 1000);

    // Find the step based on start_time_offset
    for (let i = stepList.length - 1; i >= 0; i--) {
      const step = stepList[i];
      const stepStartOffset = step.start_time_offset * 60; // convert to seconds
      
      if (elapsedSeconds >= stepStartOffset) {
        return i;
      }
    }

    return 0;
  }, [getLessonStartTime]);

  /**
   * Calculates remaining time for the current step based on elapsed time.
   */
  const calculateRemainingTimeForStep = useCallback((
    stepList: LessonStep[],
    stepIndex: number,
    entry: ScheduleEntry | null,
    sync: boolean
  ): number => {
    if (stepList.length === 0 || stepIndex < 0 || stepIndex >= stepList.length) {
      return 0;
    }

    const currentStep = stepList[stepIndex];
    const stepDuration = currentStep.duration_minutes * 60;

    // In Preview Mode, return full duration (no wall-clock sync)
    if (!sync || !entry) {
      return stepDuration;
    }

    const now = new Date();
    const lessonStart = getLessonStartTime(entry, now);
    const elapsedSeconds = Math.max(0, (now.getTime() - lessonStart.getTime()) / 1000);
    const stepStartOffset = currentStep.start_time_offset * 60; // convert to seconds
    const timeIntoStep = elapsedSeconds - stepStartOffset;

    if (timeIntoStep < 0) {
      // Lesson hasn't reached this step yet
      return stepDuration;
    }

    const remaining = Math.max(0, stepDuration - timeIntoStep);
    return Math.ceil(remaining);
  }, [getLessonStartTime]);

  /**
   * Determines the schedule status (past, current, or future) based on current time.
   */
  // Helper function to get Monday of a given week number
  const getMondayOfWeek = (weekNumber: number, year: number): Date => {
    const jan1 = new Date(year, 0, 1);
    const dayOfWeek = jan1.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    const mondayOfWeek1 = new Date(jan1);
    mondayOfWeek1.setDate(jan1.getDate() - daysToMonday);
    const mondayOfTargetWeek = new Date(mondayOfWeek1);
    mondayOfTargetWeek.setDate(mondayOfWeek1.getDate() + (weekNumber - 1) * 7);
    return mondayOfTargetWeek;
  };

  // Calculate the actual lesson date from week_of and day_of_week
  const calculateLessonDate = useCallback((entry: ScheduleEntry, now: Date): Date | null => {
    if (!entry.week_of || !entry.day_of_week) {
      // If no date info, return null to fall back to time-only comparison
      return null;
    }

    try {
      let mondayDate: Date;
      const weekOf = entry.week_of;
      const dayOfWeek = entry.day_of_week;

      // Check if weekOf is in "W47" format (week number)
      if (weekOf.startsWith('W') || weekOf.startsWith('w')) {
        const weekNumber = parseInt(weekOf.substring(1), 10);
        if (isNaN(weekNumber) || weekNumber < 1 || weekNumber > 53) {
          return null;
        }
        const year = now.getFullYear();
        mondayDate = getMondayOfWeek(weekNumber, year);
        if (isNaN(mondayDate.getTime())) {
          return null;
        }
      } else {
        // weekOf format is "MM-DD-MM-DD" (Monday to Friday)
        const parts = weekOf.split('-');
        if (parts.length < 2) {
          return null;
        }
        const [startMonth, startDay] = parts.slice(0, 2).map(Number);
        if (isNaN(startMonth) || isNaN(startDay) || startMonth < 1 || startMonth > 12 || startDay < 1 || startDay > 31) {
          return null;
        }
        const year = now.getFullYear();
        mondayDate = new Date(year, startMonth - 1, startDay);
        if (isNaN(mondayDate.getTime())) {
          return null;
        }
      }

      const dayIndex = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].indexOf(dayOfWeek.toLowerCase());
      if (dayIndex === -1) {
        return null;
      }

      const lessonDate = new Date(mondayDate);
      lessonDate.setDate(mondayDate.getDate() + dayIndex);
      if (isNaN(lessonDate.getTime())) {
        return null;
      }

      return lessonDate;
    } catch (error) {
      console.error('[useLessonTimer] Error calculating lesson date:', error);
      return null;
    }
  }, []);

  const getScheduleStatus = useCallback((entry: ScheduleEntry | null, now: Date): ScheduleStatus => {
    if (!entry) return 'future';

    const [startHours, startMinutes] = entry.start_time.split(':').map(Number);
    const [endHours, endMinutes] = entry.end_time.split(':').map(Number);

    // Try to calculate the actual lesson date
    const lessonDate = calculateLessonDate(entry, now);
    
    // Use lesson date if available, otherwise fall back to today's date
    const baseDate = lessonDate || now;

    const startTime = new Date(baseDate);
    startTime.setHours(startHours, startMinutes, 0, 0);

    const endTime = new Date(baseDate);
    endTime.setHours(endHours, endMinutes, 0, 0);

    if (now < startTime) {
      return 'future'; // Class hasn't started yet
    } else if (now >= startTime && now <= endTime) {
      return 'current'; // Class is happening now
    } else {
      return 'past'; // Class has already ended
    }
  }, [calculateLessonDate]);

  const advanceToStep = useCallback(
    (prev: TimerState, nextIndex: number): TimerState => {
      const nextStep = steps[nextIndex];
      if (!nextStep) {
        return {
          ...prev,
          isRunning: false,
          isPaused: false,
          remainingTime: 0,
        };
      }

      const nextDuration = Math.max(
        1,
        Number(nextStep.duration_minutes ?? 1) * 60
      );

      const now = new Date();
      const perfNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
      
      return {
        ...prev,
        currentStepIndex: nextIndex,
        remainingTime: nextDuration,
        isRunning: true,
        isPaused: false,
        timerStartTime: now,
        performanceStartTime: perfNow,
        pausedAt: null,
      };
    },
    [steps]
  );

  // Update advanceToStepRef after it's defined
  useEffect(() => {
    advanceToStepRef.current = advanceToStep;
  }, [advanceToStep]);

  // Store original durations when steps change
  useEffect(() => {
    if (steps.length > 0) {
      steps.forEach((step, index) => {
        originalStepDurations.current.set(index, step.duration_minutes * 60);
      });
      
      // Initialize timer state
      // Always start at step 0 when entering lesson mode
      // Sync will be applied later if autoSync is enabled
      const shouldSync = autoSync && isLiveMode && scheduleEntry !== null;
      // Always start at the first step (index 0) when initializing
      const initialStepIndex = 0;
      const remaining = calculateRemainingTimeForStep(
        steps,
        initialStepIndex,
        scheduleEntry,
        shouldSync
      );

      const now = new Date();
      const status = getScheduleStatus(scheduleEntry, now);

      console.log('[useLessonTimer] Initializing timer state:', {
        initialStepIndex,
        remaining,
        shouldSync,
        isLiveMode,
        autoSync,
        hasScheduleEntry: !!scheduleEntry,
        stepsLength: steps.length,
        firstStepName: steps[0]?.step_name,
      });

      setTimerState(prev => {
        // CRITICAL: Always start at step 0 when initializing, regardless of previous state
        // This ensures we never start on step 1 or any other step when entering lesson mode
        const newState = {
          ...prev,
          currentStepIndex: initialStepIndex, // Always 0
          remainingTime: remaining,
          isSynced: shouldSync,
          scheduleStatus: status,
        };
        
        if (prev.currentStepIndex !== initialStepIndex) {
          console.warn('[useLessonTimer] Correcting step index from', prev.currentStepIndex, 'to', initialStepIndex, {
            prevStepName: steps[prev.currentStepIndex]?.step_name,
            newStepName: steps[initialStepIndex]?.step_name,
            stepsLength: steps.length,
          });
        }
        
        // Double-check: if somehow we're not at step 0, force it
        if (newState.currentStepIndex !== 0) {
          console.error('[useLessonTimer] ERROR: Step index is not 0 after initialization! Forcing to 0.', {
            currentStepIndex: newState.currentStepIndex,
            initialStepIndex,
          });
          newState.currentStepIndex = 0;
        }
        
        return newState;
      });
    } else {
      // Reset timer state when steps are empty
      const now = new Date();
      const status = getScheduleStatus(scheduleEntry, now);
      
      setTimerState(prev => ({
        ...prev,
        currentStepIndex: 0,
        remainingTime: 0,
        isSynced: false,
        scheduleStatus: status,
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps.length, autoSync, isLiveMode, scheduleEntry?.id, getScheduleStatus, calculateCurrentStepIndex, calculateRemainingTimeForStep]);

  /**
   * Starts the timer.
   */
  const start = useCallback(() => {
    console.log('[useLessonTimer] start() called');
    setTimerState(prev => {
      console.log('[useLessonTimer] start() setTimerState with prev:', {
        isRunning: prev.isRunning,
        remainingTime: prev.remainingTime,
        currentStepIndex: prev.currentStepIndex,
      });
      
      if (prev.isRunning) {
        console.log('[useLessonTimer] Timer already running, ignoring start() call');
        return prev;
      }

      // If remainingTime is 0, recalculate from current step
      let newRemainingTime = prev.remainingTime;
      if (newRemainingTime <= 0 && steps.length > 0) {
        const currentStep = steps[prev.currentStepIndex];
        if (currentStep) {
          newRemainingTime = currentStep.duration_minutes * 60;
          console.log('[useLessonTimer] Recalculated remainingTime from step:', {
            stepIndex: prev.currentStepIndex,
            stepName: currentStep.step_name,
            durationMinutes: currentStep.duration_minutes,
            newRemainingTime,
          });
        }
      }

      // Play start sound when timer begins
      playStartSound();

      const now = new Date();
      const perfNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
      const newState = {
        ...prev,
        isRunning: true,
        isPaused: false,
        remainingTime: newRemainingTime,
        timerStartTime: now,
        performanceStartTime: perfNow,
        pausedAt: null,
      };
      
      console.log('[useLessonTimer] start() returning new state:', {
        isRunning: newState.isRunning,
        remainingTime: newState.remainingTime,
        currentStepIndex: newState.currentStepIndex,
      });
      
      return newState;
    });
  }, [steps]);

  /**
   * Stops/pauses the timer.
   */
  const stop = useCallback(() => {
    setTimerState(prev => {
      if (!prev.isRunning) return prev;

      return {
        ...prev,
        isRunning: false,
        isPaused: true,
        pausedAt: prev.remainingTime,
        timerStartTime: null,
        performanceStartTime: null,
      };
    });
  }, []);

  /**
   * Resets the timer for the current step.
   */
  const reset = useCallback((stepIndex?: number) => {
    const targetIndex = stepIndex !== undefined ? stepIndex : timerState.currentStepIndex;
    const targetStep = steps[targetIndex];

    if (!targetStep) return;

    const duration = targetStep.duration_minutes * 60;
    
    const now = new Date();
    const status = getScheduleStatus(scheduleEntry, now);
    
    setTimerState(prev => ({
      ...prev,
      remainingTime: duration,
      isRunning: false,
      isPaused: false,
      currentStepIndex: targetIndex,
      timerStartTime: null,
      performanceStartTime: null,
      pausedAt: null,
      isSynced: false, // Reset loses sync
      scheduleStatus: status,
    }));
  }, [steps, timerState.currentStepIndex]);

  // Track initialization phase to prevent step 1 bug
  useEffect(() => {
    // After 3 seconds, allow normal step changes
    const timeout = setTimeout(() => {
      initializationPhaseRef.current = false;
      console.log('[useLessonTimer] Initialization phase complete');
    }, 3000);
    return () => clearTimeout(timeout);
  }, []);

  /**
   * Changes to a different step.
   */
  const changeStep = useCallback((newIndex: number) => {
    if (newIndex < 0 || newIndex >= steps.length) {
      console.warn('[useLessonTimer] changeStep called with invalid index:', {
        newIndex,
        stepsLength: steps.length,
      });
      return;
    }

    const newStep = steps[newIndex];
    if (!newStep) {
      console.error('[useLessonTimer] changeStep: step not found at index:', newIndex);
      return;
    }

    // CRITICAL FIX: Prevent changing to step 1 during initialization phase
    if (initializationPhaseRef.current && newIndex === 1) {
      console.error('[useLessonTimer] BLOCKED: Attempted to change to step 1 during initialization! Forcing to step 0.', {
        fromIndex: timerState.currentStepIndex,
        attemptedIndex: newIndex,
        firstStepName: steps[0]?.step_name,
        secondStepName: steps[1]?.step_name,
        stackTrace: new Error().stack,
      });
      // Force to step 0 instead
      newIndex = 0;
      const step0 = steps[0];
      if (!step0) {
        console.error('[useLessonTimer] No step 0 available!');
        return;
      }
    }

    const duration = (newIndex === 0 && initializationPhaseRef.current) 
      ? steps[0].duration_minutes * 60 
      : newStep.duration_minutes * 60;

    const now = new Date();
    const status = getScheduleStatus(scheduleEntry, now);
    
    console.log('[useLessonTimer] changeStep called:', {
      fromIndex: timerState.currentStepIndex,
      toIndex: newIndex,
      stepName: steps[newIndex]?.step_name,
      duration,
      inInitializationPhase: initializationPhaseRef.current,
      stackTrace: new Error().stack,
    });
    
    setTimerState(prev => {
      // Safety check: if we're trying to change to step 1 during initialization, log it
      if (newIndex === 1 && prev.currentStepIndex === 0 && steps.length > 0) {
        console.warn('[useLessonTimer] WARNING: Changing from step 0 to step 1 - this might be the bug!', {
          fromStep: steps[0]?.step_name,
          toStep: steps[1]?.step_name,
          callStack: new Error().stack,
        });
      }
      
      return {
        ...prev,
        currentStepIndex: newIndex,
        remainingTime: duration,
        isRunning: false,
        isPaused: false,
        timerStartTime: null,
        performanceStartTime: null,
        pausedAt: null,
        isSynced: false, // Manual step change loses sync
        scheduleStatus: status,
      };
    });
  }, [steps, scheduleEntry, getScheduleStatus, timerState.currentStepIndex]);

  /**
   * Syncs timer with actual time.
   */
  const syncWithActualTime = useCallback(() => {
    // Only sync in Live Mode
    if (!scheduleEntry || !autoSync || !isLiveMode) return;

    const now = new Date();
    const currentIndex = calculateCurrentStepIndex(steps, scheduleEntry, true);
    const remaining = calculateRemainingTimeForStep(steps, currentIndex, scheduleEntry, true);
    const status = getScheduleStatus(scheduleEntry, now);
    const perfNow = typeof performance !== 'undefined' ? performance.now() : Date.now();

    setTimerState(prev => ({
      ...prev,
      currentStepIndex: currentIndex,
      remainingTime: remaining,
      isSynced: true,
      isRunning: remaining > 0 && status === 'current', // Auto-start if time remaining and class is current
      scheduleStatus: status,
      performanceStartTime: remaining > 0 && status === 'current' ? perfNow : null,
      timerStartTime: remaining > 0 && status === 'current' ? now : null,
    }));
  }, [steps, scheduleEntry, autoSync, isLiveMode, calculateCurrentStepIndex, calculateRemainingTimeForStep, getScheduleStatus]);

  // Timer countdown effect
  // CRITICAL: Do NOT include remainingTime in dependency array!
  // This causes the effect to re-run every second, clearing and recreating the interval
  useEffect(() => {
    const platform = typeof window !== 'undefined' ? (window.navigator?.userAgent || 'unknown') : 'server';
    const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
    console.log('[useLessonTimer] useEffect triggered:', {
      isRunning: timerState.isRunning,
      remainingTime: timerState.remainingTime,
      currentStepIndex: timerState.currentStepIndex,
      hasInterval: intervalRef.current !== null,
      stepsLength: steps.length,
      autoAdvance,
      platform: platform.substring(0, 50),
      isTauri,
      timestamp: new Date().toISOString(),
    });
    
    // Only manage interval lifecycle - don't recreate on every state change
    if (timerState.isRunning) {
      // Only create interval if one doesn't exist
      if (!intervalRef.current) {
        // Check if we have valid steps and calculate initial remainingTime
        const currentStep = stepsRef.current[timerState.currentStepIndex];
        let initialRemaining = timerState.remainingTime;
        
        // If remainingTime is 0 but we have a valid step, recalculate from step duration
        if (initialRemaining <= 0 && currentStep) {
          initialRemaining = currentStep.duration_minutes * 60;
          // Update state and ref
          remainingTimeRef.current = initialRemaining;
          setTimerState(prev => ({
            ...prev,
            remainingTime: initialRemaining,
          }));
        } else {
          remainingTimeRef.current = initialRemaining;
        }
        
        if (remainingTimeRef.current > 0) {
          const platform = typeof window !== 'undefined' ? (window.navigator?.userAgent || 'unknown') : 'server';
          const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
          console.log('[useLessonTimer] Creating new interval:', {
            initialRemaining: remainingTimeRef.current,
            currentStepIndex: timerState.currentStepIndex,
            stepName: currentStep?.step_name,
            stepsLength: stepsRef.current.length,
            platform: platform.substring(0, 50),
            isTauri,
            timestamp: new Date().toISOString(),
          });
          
          intervalRef.current = setInterval(() => {
            const tickTime = new Date().toISOString();
            // Use functional update to avoid stale closure issues
            setTimerState(prev => {
              // Decrement using previous value (functional update)
              const newRemaining = Math.max(0, prev.remainingTime - 1);
              
              // Update ref to keep it in sync
              remainingTimeRef.current = newRemaining;
              
              const platform = typeof window !== 'undefined' ? (window.navigator?.userAgent || 'unknown') : 'server';
              const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
              console.log('[useLessonTimer] Interval tick:', {
                prevRemaining: prev.remainingTime,
                newRemaining,
                currentStepIndex: prev.currentStepIndex,
                isRunning: prev.isRunning,
                platform: platform.substring(0, 50),
                isTauri,
                tickTime,
                intervalId: intervalRef.current,
              });
              
              // Play early warning sounds (outside 10-0 range)
              const currentStep = stepsRef.current[prev.currentStepIndex];
              const stepTotalDuration = currentStep ? currentStep.duration_minutes * 60 : 0;
              
              if (stepTotalDuration > 60) {
                if (newRemaining === 30 || newRemaining === 20 || newRemaining === 15) {
                  playEarlyWarningSound();
                }
              }
              
              if (newRemaining === 20) {
                playEarlyWarningSound();
              } else if (newRemaining === 15) {
                playEarlyWarningSound();
              }
              // Note: Sounds from 10 to 0 are handled by accelerating sound effect below

              // Check if step is complete
              if (newRemaining === 0 && prev.remainingTime > 0) {
                console.log('[useLessonTimer] Step completed, checking auto-advance:', {
                  currentStepIndex: prev.currentStepIndex,
                  totalSteps: stepsRef.current.length,
                  autoAdvance: autoAdvanceRef.current,
                });
                playCompletionSound();
                onStepCompleteRef.current?.(prev.currentStepIndex);

                // Auto-advance if enabled and not last step
                if (autoAdvanceRef.current && prev.currentStepIndex < stepsRef.current.length - 1) {
                  const nextIndex = prev.currentStepIndex + 1;
                  const nextStep = stepsRef.current[nextIndex];
                  console.log('[useLessonTimer] Auto-advancing to next step:', {
                    fromStep: prev.currentStepIndex,
                    toStep: nextIndex,
                    nextDuration: nextStep?.duration_minutes,
                    nextStepName: nextStep?.step_name,
                  });
                  
                  setTimeout(() => {
                    playStartSound();
                  }, 400);

                  if (advanceToStepRef.current) {
                    const newState = advanceToStepRef.current(prev, nextIndex);
                    remainingTimeRef.current = newState.remainingTime;
                    return newState;
                  }
                  // Fallback if advanceToStepRef is not set yet
                  return {
                    ...prev,
                    isRunning: false,
                    remainingTime: 0,
                  };
                } else {
                  if (prev.currentStepIndex >= stepsRef.current.length - 1) {
                    onLessonCompleteRef.current?.();
                  }
                  return {
                    ...prev,
                    isRunning: false,
                    remainingTime: 0,
                  };
                }
              }
              
              // Continue countdown
              return {
                ...prev,
                remainingTime: newRemaining,
              };
            });
          }, 1000);
        }
      }
    } else {
      // Clear interval when timer is not running
      if (intervalRef.current) {
        const platform = typeof window !== 'undefined' ? (window.navigator?.userAgent || 'unknown') : 'server';
        const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
        console.log('[useLessonTimer] Clearing interval - timer not running:', {
          intervalId: intervalRef.current,
          platform: platform.substring(0, 50),
          isTauri,
          timestamp: new Date().toISOString(),
        });
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    // Cleanup function
    return () => {
      // Always clear interval in cleanup - the effect will recreate it if needed
      // This is safe because the effect only runs when isRunning or currentStepIndex changes
      if (intervalRef.current) {
        const platform = typeof window !== 'undefined' ? (window.navigator?.userAgent || 'unknown') : 'server';
        const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);
        console.log('[useLessonTimer] Cleanup: clearing interval:', {
          intervalId: intervalRef.current,
          isRunning: timerState.isRunning,
          platform: platform.substring(0, 50),
          isTauri,
          timestamp: new Date().toISOString(),
        });
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // IMPORTANT: Only depend on isRunning and currentStepIndex, NOT remainingTime!
    // Including remainingTime causes the effect to re-run every second
    // Removed callbacks from deps - using refs instead to prevent unnecessary re-runs
  }, [timerState.isRunning, timerState.currentStepIndex, steps.length]);

  // Fallback guard to ensure we auto-advance even if the interval failed mid-transition
  useEffect(() => {
    if (!autoAdvanceRef.current) return;
    if (timerState.remainingTime > 0) return;
    if (steps.length === 0) return;

    const isLastStep = timerState.currentStepIndex >= steps.length - 1;
    if (isLastStep) {
      if (timerState.currentStepIndex === steps.length - 1 && timerState.remainingTime === 0) {
        onLessonCompleteRef.current?.();
      }
      return;
    }

    const nextIndex = Math.min(timerState.currentStepIndex + 1, steps.length - 1);
    if (!steps[nextIndex]) return;

    console.log('[useLessonTimer] Fallback auto-advance engaged:', {
      currentIndex: timerState.currentStepIndex,
      nextIndex,
    });

    onStepCompleteRef.current?.(timerState.currentStepIndex);
    playStartSound();

    if (advanceToStepRef.current) {
      setTimerState(prev => advanceToStepRef.current!(prev, nextIndex));
    }
  }, [
    timerState.isRunning,
    timerState.remainingTime,
    timerState.currentStepIndex,
    steps.length,
  ]);

  // Auto-sync effect when autoSync is enabled and in Live Mode
  useEffect(() => {
    if (autoSync && isLiveMode && scheduleEntry && steps.length > 0) {
      // Sync on mount and periodically
      syncWithActualTime();

      const syncInterval = setInterval(() => {
        syncWithActualTime();
      }, 3000); // Sync every 3 seconds for better accuracy on Android

      return () => clearInterval(syncInterval);
    }
  }, [autoSync, isLiveMode, scheduleEntry, steps.length, syncWithActualTime]);

  // Update schedule status periodically (even when not in Live Mode)
  useEffect(() => {
    if (!scheduleEntry) return;

    const updateStatus = () => {
      const now = new Date();
      const status = getScheduleStatus(scheduleEntry, now);
      setTimerState(prev => {
        if (prev.scheduleStatus !== status) {
          return { ...prev, scheduleStatus: status };
        }
        return prev;
      });
    };

    // Update immediately
    updateStatus();

    // Update every minute
    const statusInterval = setInterval(updateStatus, 60000);

    return () => clearInterval(statusInterval);
  }, [scheduleEntry, getScheduleStatus]);

  // Accelerating sound effect from 10 to 0 seconds
  useEffect(() => {
    // Clear any existing sound timeout
    if (soundTimeoutRef.current) {
      clearTimeout(soundTimeoutRef.current);
      soundTimeoutRef.current = null;
    }
    soundActiveRef.current = false;

    // Start accelerating sounds when 10 seconds or less remaining
    if (timerState.isRunning && timerState.remainingTime <= 10 && timerState.remainingTime > 0) {
      // Calculate interval with constant acceleration
      // At 10 seconds: 500ms interval, at 0 seconds: 100ms interval
      // Linear acceleration: interval = 100 + 40 * remainingTime
      const calculateInterval = (remaining: number): number => {
        const clampedRemaining = Math.max(0, Math.min(10, remaining));
        return 100 + 40 * clampedRemaining; // 100ms to 500ms
      };

      // Recursive function to schedule next sound with accelerating interval
      const scheduleNextSound = () => {
        const currentTime = remainingTimeRef.current;
        const currentlyRunning = isRunningRef.current;
        
        // Check if we should still be playing sounds
        if (!currentlyRunning || currentTime <= 0 || currentTime > 10) {
          soundActiveRef.current = false;
          return;
        }

        // Play warning sound
        playWarningSound();

        // Calculate interval based on current remaining time
        const interval = calculateInterval(currentTime);

        // Schedule next sound with updated interval
        soundTimeoutRef.current = setTimeout(() => {
          scheduleNextSound();
        }, interval);
      };

      // Start the accelerating sound sequence
      soundActiveRef.current = true;
      scheduleNextSound();
    } else {
      // Stop sounds when timer stops or goes above 10 seconds
      soundActiveRef.current = false;
    }

    return () => {
      if (soundTimeoutRef.current) {
        clearTimeout(soundTimeoutRef.current);
        soundTimeoutRef.current = null;
      }
      soundActiveRef.current = false;
    };
  }, [timerState.isRunning, timerState.remainingTime]);

  return {
    timerState,
    start,
    stop,
    reset,
    changeStep,
    syncWithActualTime,
  };
}

