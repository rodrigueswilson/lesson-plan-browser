import { Progress } from '../ui/Progress';

interface ProgressSectionProps {
  isProcessing: boolean;
  progress: { current: number; total: number; message: string };
  progressPercentage: number;
}

export function ProgressSection({ isProcessing, progress, progressPercentage }: ProgressSectionProps) {
  if (!isProcessing) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{progress.message}</span>
        <span className="font-medium">
          {progress.current} / {progress.total}
        </span>
      </div>
      <Progress value={progressPercentage} max={100} />
    </div>
  );
}
