import { Play, CheckCircle2, Loader2, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import type { ButtonState } from './useBatchProcessor';
import type { RecentWeek } from './useBatchProcessor';

interface WeekSectionProps {
  weekOf: string;
  setWeekOf: (value: string) => void;
  recentWeeks: RecentWeek[];
  isProcessing: boolean;
  buttonState: ButtonState;
  selectedSlotsSize: number;
  onProcessClick: () => void;
}

export function WeekSection({
  weekOf,
  setWeekOf,
  recentWeeks,
  isProcessing,
  buttonState,
  selectedSlotsSize,
  onProcessClick,
}: WeekSectionProps) {
  const disabled = buttonState === 'processing' || isProcessing || !weekOf || selectedSlotsSize === 0;

  return (
    <div className="space-y-2">
      <Label htmlFor="week">Week Of (MM-DD-MM-DD)</Label>

      {recentWeeks.length > 0 && (
        <div className="mb-2">
          <Label className="text-xs text-muted-foreground">Recent Weeks:</Label>
          <div className="flex gap-2 mt-1">
            {recentWeeks.map((week) => (
              <Button
                key={week.week_of}
                variant="outline"
                size="sm"
                onClick={() => setWeekOf(week.week_of)}
                disabled={isProcessing}
                className="text-xs"
              >
                {week.display}
              </Button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Input
          id="week"
          placeholder="e.g., 10-06-10-10"
          value={weekOf}
          onChange={(e) => setWeekOf(e.target.value)}
          disabled={isProcessing}
          className="flex-1"
        />
        <Button
          onClick={onProcessClick}
          disabled={disabled}
          className={`min-w-[140px] ${buttonState === 'success' ? 'bg-green-600 hover:bg-green-700 text-white' : buttonState === 'error' ? 'bg-red-600 hover:bg-red-700 text-white' : ''}`}
        >
          {buttonState === 'processing' && (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          )}
          {buttonState === 'success' && (
            <>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Done!
            </>
          )}
          {buttonState === 'error' && (
            <>
              <X className="w-4 h-4 mr-2" />
              Failed
            </>
          )}
          {buttonState === 'idle' && (
            <>
              <Play className="w-4 h-4 mr-2" />
              Generate
            </>
          )}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Format: Month-Day-Month-Day (e.g., 10-06-10-10 for Oct 6 - Oct 10)
      </p>
    </div>
  );
}
