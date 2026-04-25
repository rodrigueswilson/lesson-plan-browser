import { Progress } from '../ui/Progress';

interface ProgressSectionProps {
  isProcessing: boolean;
  progress: { current: number; total: number; message: string };
  progressPercentage: number;
  stageLabel: string;
  completedSlots: number;
  totalSlots: number;
  lastUpdateAt: string | null;
  isStalled: boolean;
}

export function ProgressSection({
  isProcessing,
  progress,
  progressPercentage,
  stageLabel,
  completedSlots,
  totalSlots,
  lastUpdateAt,
  isStalled,
}: ProgressSectionProps) {
  if (!isProcessing) return null;

  const lastUpdateText = lastUpdateAt
    ? `${Math.max(0, Math.floor((Date.now() - new Date(lastUpdateAt).getTime()) / 1000))}s ago`
    : 'just now';

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {stageLabel}: {progress.message}
        </span>
        <span className="font-medium">
          {completedSlots} / {totalSlots || progress.total}
        </span>
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{Math.round(progressPercentage)}% complete</span>
        <span>
          Last update {lastUpdateText}
          {isStalled ? ' - reconnecting' : ''}
        </span>
      </div>
      <Progress value={progressPercentage} max={100} />
    </div>
  );
}
