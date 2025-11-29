import { useState, useEffect, useRef } from 'react';
import { X, RotateCcw, SkipForward, Check } from 'lucide-react';
import { Dialog } from '@lesson-ui/Dialog';
import { Button } from '@lesson-ui/Button';
import type { LessonStep } from '@lesson-api';

export interface TimerAdjustment {
  type: 'set' | 'reset' | 'skip';
  amount?: number; // minutes (for 'set' type, this is the target duration)
  targetStep?: number; // if skipping
}

interface TimerAdjustmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentStep: LessonStep;
  currentStepIndex: number;
  totalSteps: number;
  currentRemainingTime: number; // seconds
  originalDuration: number; // seconds
  onAdjust: (adjustment: TimerAdjustment) => void;
}

export function TimerAdjustmentDialog({
  open,
  onOpenChange,
  currentStep,
  currentStepIndex,
  totalSteps,
  currentRemainingTime,
  originalDuration,
  onAdjust,
}: TimerAdjustmentDialogProps) {
  const [targetMinutes, setTargetMinutes] = useState(0); // target duration in minutes
  const initializedRef = useRef(false); // Track if we've initialized for this dialog session

  // Initialize target minutes to current remaining time ONLY when dialog first opens
  // Don't reset when currentRemainingTime changes (timer counting down)
  useEffect(() => {
    if (open && !initializedRef.current) {
      const currentMins = Math.floor(currentRemainingTime / 60);
      setTargetMinutes(currentMins);
      initializedRef.current = true;
    } else if (!open) {
      // Reset the ref when dialog closes so it initializes again next time
      initializedRef.current = false;
    }
  }, [open]); // Only depend on 'open', not 'currentRemainingTime'

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAddMinute = () => {
    setTargetMinutes((prev) => prev + 1);
  };

  const handleSubtractMinute = () => {
    // Prevent going below 1 minute
    setTargetMinutes((prev) => Math.max(1, prev - 1));
  };

  const handleConfirm = () => {
    const targetSeconds = targetMinutes * 60;
    // Only adjust if the target duration (in seconds) is different from current remaining time
    // This allows setting to 1 minute even if current time is 1:30 (both show as 1 minute, but different seconds)
    if (targetSeconds !== currentRemainingTime) {
      onAdjust({ type: 'set', amount: targetMinutes });
    }
    onOpenChange(false);
  };

  const handleReset = () => {
    onAdjust({ type: 'reset' });
    onOpenChange(false);
  };

  const handleSkip = () => {
    onAdjust({ type: 'skip', targetStep: currentStepIndex + 1 });
    onOpenChange(false);
  };

  const handleClose = () => {
    setTargetMinutes(0);
    onOpenChange(false);
  };

  const currentMinutes = Math.floor(currentRemainingTime / 60);
  const previewTotalSeconds = targetMinutes * 60;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Adjust Timer</h2>
          <Button variant="ghost" size="icon" onClick={handleClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4 mb-6">
          <div className="text-sm text-muted-foreground">
            Current Step: {currentStep.step_name} (Step {currentStepIndex + 1} of {totalSteps})
          </div>
          <div className="flex flex-row gap-4 items-start">
            <div className="flex-1">
              <div className="text-xs text-muted-foreground mb-1">Original Duration</div>
              <div className="text-lg font-semibold">{formatTime(originalDuration)}</div>
            </div>
            <div className="flex-1">
              <div className="text-xs text-muted-foreground mb-1">Current Remaining</div>
              <div className="text-lg font-semibold">{formatTime(currentRemainingTime)}</div>
            </div>
            <div className="flex-1">
              <div className="text-xs text-muted-foreground mb-1">New Time</div>
              <div className={`text-lg font-semibold ${previewTotalSeconds !== currentRemainingTime ? 'text-primary' : ''}`}>
                {formatTime(previewTotalSeconds)}
              </div>
              {previewTotalSeconds !== currentRemainingTime && (
                <div className="text-xs text-muted-foreground mt-1">
                  {targetMinutes > currentMinutes ? '+' : ''}{targetMinutes - currentMinutes} min
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Adjust Time */}
          <div>
            <div className="text-sm font-semibold mb-3">Adjust Time</div>
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="lg"
                onClick={handleSubtractMinute}
                disabled={targetMinutes <= 1}
                className="w-16 h-16 flex items-center justify-center hover:bg-muted disabled:opacity-50"
                title="Decrease by 1 minute"
              >
                <span className="text-3xl font-bold leading-none">−</span>
              </Button>
              <div className="text-center min-w-[120px]">
                <div className="text-2xl font-bold">{targetMinutes}</div>
                <div className="text-xs text-muted-foreground">minutes</div>
              </div>
              <Button
                variant="outline"
                size="lg"
                onClick={handleAddMinute}
                className="w-16 h-16 flex items-center justify-center hover:bg-muted"
                title="Increase by 1 minute"
              >
                <span className="text-3xl font-bold leading-none">+</span>
              </Button>
            </div>
          </div>

          {/* Other Options */}
          <div>
            <div className="text-sm font-semibold mb-2">Other Options</div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleReset} className="flex-1">
                <RotateCcw className="w-4 h-4 mr-2" />Reset to Original
              </Button>
              {currentStepIndex < totalSteps - 1 && (
                <Button variant="outline" size="sm" onClick={handleSkip} className="flex-1">
                  <SkipForward className="w-4 h-4 mr-2" />Skip to Next
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t">
          <div className="text-xs text-muted-foreground mb-4">
            ⚠️ Warning: Adjusting will affect remaining steps. Remaining steps will be recalculated proportionally.
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handleConfirm}
              disabled={targetMinutes * 60 === currentRemainingTime}
            >
              <Check className="w-4 h-4 mr-2" />
              OK
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
