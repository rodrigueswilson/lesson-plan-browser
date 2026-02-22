import { Save, Trash2, Upload } from 'lucide-react';
import { Button } from '../ui/Button';

interface ScheduleInputHeaderProps {
  isLoading: boolean;
  isSaving: boolean;
  onLoadExisting: () => void;
  onClear: () => void;
  onSave: () => void;
}

export function ScheduleInputHeader({
  isLoading,
  isSaving,
  onLoadExisting,
  onClear,
  onSave,
}: ScheduleInputHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-xl font-semibold">Schedule Input</h2>
        <p className="text-sm text-muted-foreground">
          Click on any cell to add subject, grade, and homeroom
        </p>
      </div>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onLoadExisting}
          disabled={isLoading}
        >
          <Upload className="w-4 h-4 mr-2" />
          Load Existing
        </Button>
        <Button variant="outline" size="sm" onClick={onClear}>
          <Trash2 className="w-4 h-4 mr-2" />
          Clear All
        </Button>
        <Button onClick={onSave} disabled={isSaving}>
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save Schedule'}
        </Button>
      </div>
    </div>
  );
}
