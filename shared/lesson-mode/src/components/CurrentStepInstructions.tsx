import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { LessonStep } from '@lesson-api';
import { Card } from '@lesson-ui/Card';
import { Button } from '@lesson-ui/Button';
import { parseMarkdown } from '../utils/markdownUtils';

interface CurrentStepInstructionsProps {
  step: LessonStep;
  currentStepIndex: number;
  totalSteps: number;
  onPrevious: () => void;
  onNext: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

export function CurrentStepInstructions({
  step,
  currentStepIndex,
  totalSteps,
  onPrevious,
  onNext,
  isCollapsed = false,
  onToggleCollapse,
  className = '',
}: CurrentStepInstructionsProps) {
  // Extract the instructional text from display_content
  // For now, show the full display_content
  // Later, when we have structured fields, we'll show just the instruction part

  const instructionText = step.display_content || 'No instructions available for this step.';
  const canGoBack = currentStepIndex > 0;
  const canGoForward = currentStepIndex < totalSteps - 1;
  const CollapseIcon = isCollapsed ? ChevronRight : ChevronLeft;

  return (
    <div className={`border-r bg-card flex flex-col h-full overflow-hidden ${className}`}>
      <Card className="rounded-none border-0 border-r shadow-none flex-1 flex flex-col overflow-hidden">
        <div className="p-2 border-b bg-muted/30 flex items-center">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex-1">
            Current Step Instructions
          </div>
          <div className="flex items-center gap-2">
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
                className="p-1"
                title={isCollapsed ? 'Expand instructions panel' : 'Collapse instructions panel'}
              >
                <CollapseIcon className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-base leading-relaxed whitespace-pre-wrap">
            {parseMarkdown(instructionText)}
          </div>
        </div>
        {/* Navigation buttons at bottom */}
        <div className="p-3 border-t bg-muted/30 flex items-center justify-between gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onPrevious}
            disabled={!canGoBack}
            className="flex-1"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <div className="text-xs text-muted-foreground px-2">
            {currentStepIndex + 1} / {totalSteps}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onNext}
            disabled={!canGoForward}
            className="flex-1"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </Card>
    </div>
  );
}

