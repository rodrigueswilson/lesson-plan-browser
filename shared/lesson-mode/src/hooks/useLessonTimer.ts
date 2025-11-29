import { useState, useEffect, useRef, useCallback } from 'react';
import type { LessonStep, ScheduleEntry } from '@lesson-api';
import { playEarlyWarningSound, playWarningSound, playWarningDoubleSound, playCompletionSound, playStartSound } from '../utils/timerSounds';

export interface TimerState {
  remainingTime: number; // seconds
  isRunning: boolean;
  isPaused: boolean;
  isSynced: boolean; // true if synced with actual time
  currentStepIndex: number;
  lessonStartTime: Date | null; // when lesson started (from schedule)
  timerStartTime: Date | null; // when timer was started
  pausedAt: number | null; // seconds remaining when paused
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
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const originalStepDurations = useRef<Map<number, number>>(new Map());

  // Store original durations when steps change
  useEffect(() => {
    if (steps.length > 0) {
      steps.forEach((step, index) => {
        originalStepDurations.current.set(index, step.duration_minutes * 60);
      });
      
      // Initialize timer state
      // In Preview Mode (isLiveMode=false), always start at step 0
      const shouldSync = autoSync && isLiveMode && scheduleEntry !== null;
      const initialStepIndex = calculateCurrentStepIndex(steps, scheduleEntry, shouldSync);
      const remaining = calculateRemainingTimeForStep(
        steps,
        initialStepIndex,
        scheduleEntry,
        shouldSync
      );

      setTimerState(prev => ({
        ...prev,
        currentStepIndex: initialStepIndex,
        remainingTime: remaining,
        isSynced: shouldSync,
      }));
    } else {
      // Reset timer state when steps are empty
      setTimerState(prev => ({
        ...prev,
        currentStepIndex: 0,
        remainingTime: 0,
        isSynced: false,
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps.length, autoSync, isLiveMode, scheduleEntry?.id]);

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
  }, []);

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
  }, []);

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
   * Starts the timer.
   */
  const start = useCallback(() => {
    setTimerState(prev => {
      if (prev.isRunning) return prev;

      // Play start sound when timer begins
      playStartSound();

      const now = new Date();
      return {
        ...prev,
        isRunning: true,
        isPaused: false,
        timerStartTime: now,
        pausedAt: null,
      };
    });
  }, []);

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
    
    setTimerState(prev => ({
      ...prev,
      remainingTime: duration,
      isRunning: false,
      isPaused: false,
      currentStepIndex: targetIndex,
      timerStartTime: null,
      pausedAt: null,
      isSynced: false, // Reset loses sync
    }));
  }, [steps, timerState.currentStepIndex]);

  /**
   * Changes to a different step.
   */
  const changeStep = useCallback((newIndex: number) => {
    if (newIndex < 0 || newIndex >= steps.length) return;

    const newStep = steps[newIndex];
    const duration = newStep.duration_minutes * 60;

    setTimerState(prev => ({
      ...prev,
      currentStepIndex: newIndex,
      remainingTime: duration,
      isRunning: false,
      isPaused: false,
      timerStartTime: null,
      pausedAt: null,
      isSynced: false, // Manual step change loses sync
    }));
  }, [steps]);

  /**
   * Syncs timer with actual time.
   */
  const syncWithActualTime = useCallback(() => {
    // Only sync in Live Mode
    if (!scheduleEntry || !autoSync || !isLiveMode) return;

    const currentIndex = calculateCurrentStepIndex(steps, scheduleEntry, true);
    const remaining = calculateRemainingTimeForStep(steps, currentIndex, scheduleEntry, true);

    setTimerState(prev => ({
      ...prev,
      currentStepIndex: currentIndex,
      remainingTime: remaining,
      isSynced: true,
      isRunning: remaining > 0, // Auto-start if time remaining
    }));
  }, [steps, scheduleEntry, autoSync, isLiveMode, calculateCurrentStepIndex, calculateRemainingTimeForStep]);

  // Timer countdown effect
  useEffect(() => {
    console.log('[useLessonTimer] useEffect triggered:', {
      isRunning: timerState.isRunning,
      remainingTime: timerState.remainingTime,
      currentStepIndex: timerState.currentStepIndex,
      hasInterval: intervalRef.current !== null,
    });
    
    // Keep interval running if timer is running
    // Note: remainingTime can be 0 during auto-advance transitions, so we only check isRunning
    if (timerState.isRunning) {
      // Only create interval if one doesn't exist
      // This prevents recreating the interval unnecessarily
      if (!intervalRef.current) {
        console.log('[useLessonTimer] Creating new interval');
        intervalRef.current = setInterval(() => {
          setTimerState(prev => {
            // If remainingTime is already 0 and we're not auto-advancing, stop
            // But if we're auto-advancing, the state should have been updated to nextDuration
            if (prev.remainingTime <= 0 && !prev.isRunning) {
              console.log('[useLessonTimer] Timer stopped, remainingTime is 0');
              return prev;
            }
            
            const newRemaining = Math.max(0, prev.remainingTime - 1);
            
            console.log('[useLessonTimer] Interval tick:', {
              prevRemaining: prev.remainingTime,
              newRemaining,
              currentStepIndex: prev.currentStepIndex,
              isRunning: prev.isRunning,
            });

            // Play warning sounds following professional escalation patterns
            // Calculate total duration for this step to determine if we need early warnings
            const currentStep = steps[prev.currentStepIndex];
            const stepTotalDuration = currentStep ? currentStep.duration_minutes * 60 : 0;
            
            // For timers >60s: warnings at 30s, 20s, 15s
            if (stepTotalDuration > 60) {
              if (newRemaining === 30 || newRemaining === 20 || newRemaining === 15) {
                playEarlyWarningSound();
              }
            }
            
            // Regular countdown warnings
            if (newRemaining === 20) {
              playEarlyWarningSound();
            } else if (newRemaining === 15) {
              playEarlyWarningSound();
            } else if (newRemaining <= 5 && newRemaining > 0) {
              // Two beeps per second from 5 to 0 (increased urgency)
              playWarningDoubleSound();
            } else if (newRemaining <= 10 && newRemaining > 5) {
              // Single beep per second from 10 to 6
              playWarningSound();
            }

            // Check if step is complete
            // Only trigger completion once when we transition from >0 to 0
            if (newRemaining === 0 && prev.remainingTime > 0) {
              console.log('[useLessonTimer] Step completed, checking auto-advance:', {
                currentStepIndex: prev.currentStepIndex,
                totalSteps: steps.length,
                autoAdvance,
              });
              // Play completion sound
              playCompletionSound();
              
              onStepComplete?.(prev.currentStepIndex);

              // Auto-advance if enabled and not last step
              if (autoAdvance && prev.currentStepIndex < steps.length - 1) {
                const nextStep = steps[prev.currentStepIndex + 1];
                const nextDuration = nextStep.duration_minutes * 60;
                
                console.log('[useLessonTimer] Auto-advancing to next step:', {
                  fromStep: prev.currentStepIndex,
                  toStep: prev.currentStepIndex + 1,
                  nextDuration,
                  nextStepName: nextStep.step_name,
                  currentRemainingTime: prev.remainingTime,
                });
                
                // Play start sound for new step after completion sound
                // Delay ensures completion sound finishes before start sound plays
                setTimeout(() => {
                  console.log('[useLessonTimer] Playing start sound for next step');
                  playStartSound();
                }, 400);
                
                // IMPORTANT: Return new state with next step's duration IMMEDIATELY
                // This ensures the interval continues without interruption
                // The interval callback will use this new state on the next tick
                const newState = {
                  ...prev,
                  remainingTime: nextDuration,
                  currentStepIndex: prev.currentStepIndex + 1,
                  timerStartTime: new Date(),
                  isRunning: true, // Continue running for next step
                };
                
                console.log('[useLessonTimer] Returning new state for auto-advance:', {
                  remainingTime: newState.remainingTime,
                  currentStepIndex: newState.currentStepIndex,
                  isRunning: newState.isRunning,
                });
                
                return newState;
              } else {
                // Last step complete or auto-advance disabled
                if (prev.currentStepIndex >= steps.length - 1) {
                  onLessonComplete?.();
                }
                return {
                  ...prev,
                  isRunning: false,
                  remainingTime: 0,
                };
              }
            }
            
            // Continue countdown if not at zero
            return {
              ...prev,
              remainingTime: newRemaining,
            };
          });
        }, 1000);
      }
    } else {
      // Only clear interval if timer is not running
      console.log('[useLessonTimer] Timer not running, clearing interval:', {
        isRunning: timerState.isRunning,
        remainingTime: timerState.remainingTime,
      });
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [timerState.isRunning, timerState.remainingTime, timerState.currentStepIndex, steps, autoAdvance, onStepComplete, onLessonComplete]);

  // Auto-sync effect when autoSync is enabled and in Live Mode
  useEffect(() => {
    if (autoSync && isLiveMode && scheduleEntry && steps.length > 0) {
      // Sync on mount and periodically
      syncWithActualTime();

      const syncInterval = setInterval(() => {
        syncWithActualTime();
      }, 5000); // Sync every 5 seconds

      return () => clearInterval(syncInterval);
    }
  }, [autoSync, isLiveMode, scheduleEntry, steps.length, syncWithActualTime]);

  return {
    timerState,
    start,
    stop,
    reset,
    changeStep,
    syncWithActualTime,
  };
}

