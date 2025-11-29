import type { LessonStep } from '@lesson-api';
import { TimerAdjustment } from '../components/TimerAdjustmentDialog';

export interface RecalculatedStep extends LessonStep {
  adjustedDuration: number; // seconds (adjusted duration)
  originalDuration: number; // seconds (original duration)
}

/**
 * Recalculates remaining step durations proportionally when timer is adjusted.
 */
export function recalculateStepDurations(
  steps: LessonStep[],
  currentStepIndex: number,
  adjustment: TimerAdjustment,
  originalSteps?: LessonStep[] // Optional: true original steps from API
): RecalculatedStep[] {
  if (steps.length === 0 || currentStepIndex < 0 || currentStepIndex >= steps.length) {
    return steps.map(step => ({
      ...step,
      adjustedDuration: step.duration_minutes * 60,
      originalDuration: step.duration_minutes * 60,
    }));
  }

  // Use originalSteps if provided, otherwise use steps as the source of truth for originalDuration
  const sourceForOriginal = originalSteps || steps;

  const result: RecalculatedStep[] = steps.map((step, index) => {
    // Always use the original step's duration_minutes as the true originalDuration
    // This ensures that even after multiple adjustments, we always reference the true original
    const trueOriginalStep = sourceForOriginal[index] || step;
    const trueOriginalDuration = trueOriginalStep.duration_minutes * 60;
    
    // For the current step being adjusted, we need to calculate the new adjustedDuration
    // For other steps, use their current adjustedDuration (if they were previously adjusted)
    // or their originalDuration (if they haven't been adjusted yet)
    const isCurrentStep = index === currentStepIndex;
    let adjustedDuration: number;
    
    if (isCurrentStep) {
      // For the current step, we'll calculate the new adjustedDuration in the switch statement below
      // For now, initialize it to the current step's duration (which may already be adjusted)
      adjustedDuration = step.duration_minutes * 60;
    } else {
      // For other steps, preserve their current adjustedDuration if they have one
      // Otherwise use their originalDuration
      adjustedDuration = ('adjustedDuration' in step && step.adjustedDuration) 
        ? step.adjustedDuration 
        : trueOriginalDuration;
    }
    
    return {
      ...step,
      adjustedDuration: adjustedDuration,
      originalDuration: trueOriginalDuration,
      // For the current step, duration_minutes will be updated in the switch statement below
      // For other steps, set it based on their adjustedDuration
      duration_minutes: isCurrentStep ? step.duration_minutes : Math.ceil(adjustedDuration / 60),
    };
  });

  const currentStep = result[currentStepIndex];
  const remainingSteps = result.slice(currentStepIndex + 1);

  switch (adjustment.type) {
    case 'set': {
      // Set the duration directly to the specified amount (in minutes, can be decimal)
      if (adjustment.amount !== undefined) {
        const targetSeconds = adjustment.amount * 60;
        console.log('[recalculateStepDurations] Setting time:', {
          targetMinutes: adjustment.amount,
          targetSeconds,
          targetSecondsRounded: Math.round(targetSeconds),
          originalDuration: currentStep.originalDuration,
          originalDurationMinutes: currentStep.originalDuration / 60,
          currentDurationMinutes: currentStep.duration_minutes,
          currentAdjustedDuration: currentStep.adjustedDuration,
        });
        // Use exact seconds (round to nearest second for display, but keep decimal minutes)
        currentStep.adjustedDuration = Math.round(targetSeconds);
        currentStep.duration_minutes = adjustment.amount; // Keep exact decimal minutes
      }
      break;
    }

    case 'add': {
      // Add time to current step (kept for backward compatibility)
      if (adjustment.amount) {
        const addedSeconds = adjustment.amount * 60;
        const newAdjustedDuration = currentStep.originalDuration + addedSeconds;
        console.log('[recalculateStepDurations] Adding time:', {
          adjustmentAmount: adjustment.amount,
          addedSeconds,
          originalDuration: currentStep.originalDuration,
          originalDurationMinutes: currentStep.originalDuration / 60,
          currentDurationMinutes: currentStep.duration_minutes,
          currentAdjustedDuration: currentStep.adjustedDuration,
          newAdjustedDuration: newAdjustedDuration,
          newDurationMinutes: Math.ceil(newAdjustedDuration / 60),
        });
        currentStep.adjustedDuration = newAdjustedDuration;
        currentStep.duration_minutes = Math.ceil(currentStep.adjustedDuration / 60);
      }
      break;
    }

    case 'subtract': {
      // Subtract time from current step (kept for backward compatibility)
      if (adjustment.amount) {
        const subtractedSeconds = adjustment.amount * 60;
        currentStep.adjustedDuration = Math.max(
          60, // Minimum 1 minute
          currentStep.originalDuration - subtractedSeconds
        );
        currentStep.duration_minutes = Math.ceil(currentStep.adjustedDuration / 60);
      }
      break;
    }

    case 'reset': {
      // Restore original durations for all steps
      result.forEach(step => {
        step.adjustedDuration = step.originalDuration;
        step.duration_minutes = Math.ceil(step.originalDuration / 60);
      });
      return result;
    }

    case 'skip': {
      // Skip to next step - no duration adjustment needed
      break;
    }
  }

  // If we set, added, or subtracted time, proportionally adjust remaining steps
  if ((adjustment.type === 'set' || adjustment.type === 'add' || adjustment.type === 'subtract') && remainingSteps.length > 0) {
    let adjustmentAmount: number;
    if (adjustment.type === 'set') {
      // Calculate the difference between the new duration and the original duration
      adjustmentAmount = currentStep.adjustedDuration - currentStep.originalDuration;
    } else if (adjustment.type === 'add') {
      adjustmentAmount = (adjustment.amount || 0) * 60;
    } else {
      adjustmentAmount = -(adjustment.amount || 0) * 60;
    }

    console.log('[recalculateStepDurations] Proportional adjustment starting:', {
      adjustmentType: adjustment.type,
      adjustmentAmount: adjustmentAmount,
      adjustmentAmountMinutes: adjustmentAmount / 60,
      currentStepOriginalDuration: currentStep.originalDuration,
      currentStepAdjustedDuration: currentStep.adjustedDuration,
      remainingStepsCount: remainingSteps.length,
    });

    // Calculate total original duration of remaining steps
    const totalRemainingOriginal = remainingSteps.reduce(
      (sum, step) => sum + step.originalDuration,
      0
    );
    
    console.log('[recalculateStepDurations] Remaining steps original durations:', {
      totalRemainingOriginal: totalRemainingOriginal,
      totalRemainingOriginalMinutes: totalRemainingOriginal / 60,
      stepDetails: remainingSteps.map((step, idx) => ({
        index: currentStepIndex + 1 + idx,
        name: step.step_name,
        originalDuration: step.originalDuration,
        originalDurationMinutes: step.originalDuration / 60,
      })),
    });

    if (totalRemainingOriginal > 0) {
      // IMPORTANT: When we adjust the current step, the remaining steps get the OPPOSITE adjustment
      // - If we REDUCE current step (negative adjustmentAmount), we ADD time to remaining steps
      // - If we INCREASE current step (positive adjustmentAmount), we SUBTRACT time from remaining steps
      // This maintains the total lesson duration
      const remainingStepsAdjustment = -adjustmentAmount; // Flip the sign
      
      console.log('[recalculateStepDurations] Distributing to remaining steps:', {
        currentStepAdjustment: adjustmentAmount,
        currentStepAdjustmentMinutes: adjustmentAmount / 60,
        remainingStepsAdjustment: remainingStepsAdjustment,
        remainingStepsAdjustmentMinutes: remainingStepsAdjustment / 60,
      });
      
      // Distribute adjustment proportionally
      remainingSteps.forEach((step, idx) => {
        const proportion = step.originalDuration / totalRemainingOriginal;
        const adjustmentForStep = remainingStepsAdjustment * proportion;

        // Calculate new duration
        const newDuration = step.originalDuration + adjustmentForStep;
        
        // Ensure no step goes below 1 minute
        const finalDuration = Math.max(60, newDuration);
        step.adjustedDuration = finalDuration;
        step.duration_minutes = Math.ceil(finalDuration / 60);
        
        console.log('[recalculateStepDurations] Adjusting remaining step:', {
          stepIndex: currentStepIndex + 1 + idx,
          stepName: step.step_name,
          originalDuration: step.originalDuration,
          originalDurationMinutes: step.originalDuration / 60,
          adjustmentForStep: adjustmentForStep,
          adjustmentForStepMinutes: adjustmentForStep / 60,
          proportion: proportion,
          newDuration: finalDuration,
          newDurationMinutes: step.duration_minutes,
        });

        // Update start_time_offset for subsequent steps
        if (idx === 0) {
          // First remaining step starts after adjusted current step
          const previousOffset = currentStepIndex > 0
            ? result[currentStepIndex - 1].start_time_offset
            : 0;
          const previousDuration = currentStepIndex > 0
            ? result[currentStepIndex - 1].duration_minutes
            : 0;
          
          step.start_time_offset = previousOffset + previousDuration + currentStep.duration_minutes;
        } else {
          // Subsequent steps adjust based on previous step
          const previousStep = remainingSteps[idx - 1];
          step.start_time_offset = previousStep.start_time_offset + previousStep.duration_minutes;
        }
      });
    }
  }

  return result;
}

/**
 * Gets the original duration for a step (before any adjustments).
 */
export function getOriginalDuration(step: RecalculatedStep | LessonStep): number {
  if ('originalDuration' in step && step.originalDuration) {
    return step.originalDuration;
  }
  return step.duration_minutes * 60;
}

/**
 * Gets the adjusted duration for a step (after adjustments).
 */
export function getAdjustedDuration(step: RecalculatedStep | LessonStep): number {
  if ('adjustedDuration' in step && step.adjustedDuration) {
    return step.adjustedDuration;
  }
  return step.duration_minutes * 60;
}

