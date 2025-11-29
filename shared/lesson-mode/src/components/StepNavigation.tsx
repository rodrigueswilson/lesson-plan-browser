import { CheckCircle2, Circle } from 'lucide-react';
import type { LessonStep } from '@lesson-api';
import { Button } from '@lesson-ui/Button';

interface StepNavigationProps {
  steps: LessonStep[];
  currentStepIndex: number;
  onStepSelect: (stepIndex: number) => void;
  allowSkip?: boolean;
}

export function StepNavigation({
  steps,
  currentStepIndex,
  onStepSelect,
  allowSkip = true,
}: StepNavigationProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {steps.map((step, index) => {
        const isCompleted = index < currentStepIndex;
        const isCurrent = index === currentStepIndex;
        const isUpcoming = index > currentStepIndex;

        return (
          <Button
            key={step.id}
            variant={isCurrent ? 'default' : 'outline'}
            size="sm"
            onClick={() => onStepSelect(index)}
            className={`flex items-center gap-2 ${
              isCurrent ? 'bg-primary text-primary-foreground' : ''
            }`}
            disabled={!allowSkip && isUpcoming}
          >
            {isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : isCurrent ? (
              <Circle className="w-4 h-4 fill-current" />
            ) : (
              <Circle className="w-4 h-4" />
            )}
            <span>
              {step.step_number}. {step.step_name}
            </span>
          </Button>
        );
      })}
    </div>
  );
}

