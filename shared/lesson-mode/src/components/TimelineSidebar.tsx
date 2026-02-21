import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import type { LessonStep } from '@lesson-api';
import { TimerState } from '../hooks/useLessonTimer';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import { TimerDisplay } from './TimerDisplay';

interface TimelineSidebarProps {
  steps: LessonStep[];
  currentStepIndex: number;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onStepComplete: (stepIndex: number) => void;
  onStepSelect: (stepIndex: number) => void;
  timerState: TimerState;
  onTimerStart: () => void;
  onTimerStop: () => void;
  onTimerReset: () => void;
  onTimerAdjust: () => void;
  onTimeAdjust?: (newRemainingTime: number) => void; // Callback when time is adjusted via drag
  totalDuration: number;
  originalDuration?: number;
}

export function TimelineSidebar({
  steps,
  currentStepIndex,
  isCollapsed,
  onToggleCollapse,
  onStepComplete,
  onStepSelect,
  timerState,
  onTimerStart,
  onTimerStop,
  onTimerReset,
  onTimerAdjust,
  onTimeAdjust,
  totalDuration,
  originalDuration,
}: TimelineSidebarProps) {
  // Filter out vocabulary and sentence frames steps from timeline
  const isResourceStep = (step: LessonStep | null | undefined) => {
    if (!step) return false;
    const stepNameLower = (step.step_name || '').toLowerCase();
    return (
      step.content_type === 'sentence_frames' ||
      stepNameLower.includes('vocabulary') ||
      stepNameLower.includes('cognate') ||
      stepNameLower.includes('sentence frame')
    );
  };

  // Safety checks
  if (!steps || steps.length === 0) {
    return (
      <div className="w-1/5 border-r bg-muted/30 flex flex-col items-center justify-center p-4">
        <div className="text-sm text-muted-foreground">No steps available</div>
      </div>
    );
  }

  if (currentStepIndex < 0 || currentStepIndex >= steps.length) {
    return (
      <div className="w-1/5 border-r bg-muted/30 flex flex-col items-center justify-center p-4">
        <div className="text-sm text-muted-foreground">Invalid step index</div>
      </div>
    );
  }

  const currentStep = steps[currentStepIndex];
  const upcomingSteps = steps.slice(currentStepIndex + 1).filter(step => step && !isResourceStep(step));

  if (isCollapsed) {
    return (
      <div className="w-12 border-r bg-muted/30 flex flex-col items-center py-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="p-2"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-1/5 border-r bg-muted/30 flex flex-col h-full overflow-y-auto">
      {/* Column Header */}
      <div className="p-2 border-b bg-muted/30 flex items-center">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex-1">
          Lesson Pacing
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="p-1"
          title="Collapse lesson pacing panel"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex-1 p-4 space-y-6 overflow-y-auto">
        {/* Previous Activities */}
        {currentStepIndex > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Previous Steps
              </div>
              {currentStepIndex > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onStepSelect(0)}
                  className="h-6 px-2 text-xs"
                  title="Go to beginning of lesson"
                >
                  Beginning
                </Button>
              )}
            </div>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {steps
                .slice(0, currentStepIndex)
                .filter(step => step && !isResourceStep(step))
                .sort((a, b) => (a.step_number || 0) - (b.step_number || 0))
                .map((step) => (
                  <Card
                    key={step.id}
                    className="p-3 bg-muted/50 opacity-75 cursor-pointer hover:bg-muted/70 hover:opacity-100 transition-all"
                    onClick={() => onStepSelect(step.step_number - 1)}
                    title={`Click to go back to: ${step.step_name || 'Step'}`}
                  >
                    <div className="text-sm font-medium">
                      {step.step_name || 'Unnamed Step'}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Step {step.step_number} • Click to return
                    </div>
                  </Card>
                ))}
            </div>
          </div>
        )}

        {/* Current Activity */}
        <div className="space-y-3">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Current
          </div>
          <Card className={`p-4 border-2 ${
            timerState.scheduleStatus === 'current' 
              ? 'border-blue-500 bg-blue-50/50' 
              : timerState.scheduleStatus === 'past' 
              ? 'border-green-500 bg-green-50/50' 
              : timerState.scheduleStatus === 'future'
              ? 'border-orange-500 bg-orange-50/50'
              : 'border-primary'
          }`}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="text-sm font-semibold">
                  {currentStep?.step_name || 'Current Step'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Step {currentStep?.step_number || currentStepIndex + 1} of {steps.length}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onStepComplete(currentStepIndex)}
                className="ml-2"
                title="Mark as complete"
              >
                <Check className="w-4 h-4" />
              </Button>
            </div>

            {/* Timer in Sidebar */}
            <div className="mt-3">
              <TimerDisplay
                totalDuration={totalDuration}
                remainingTime={timerState.remainingTime}
                isRunning={timerState.isRunning}
                onStart={onTimerStart}
                onStop={onTimerStop}
                onReset={onTimerReset}
                onAdjust={onTimerAdjust}
                onTimeAdjust={onTimeAdjust}
                isSynced={timerState.isSynced}
                originalDuration={originalDuration}
                onComplete={() => onStepComplete(currentStepIndex)}
              />
            </div>
          </Card>
        </div>

        {/* Upcoming Activities */}
        {upcomingSteps.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Upcoming
            </div>
            <div className="space-y-2">
              {upcomingSteps.map((step) => (
                step && (
                  <Card
                    key={step.id}
                    className="p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => onStepSelect(step.step_number - 1)}
                  >
                    <div className="text-sm font-medium">{step.step_name || 'Unnamed Step'}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {step.duration_minutes || 0} min
                    </div>
                  </Card>
                )
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

