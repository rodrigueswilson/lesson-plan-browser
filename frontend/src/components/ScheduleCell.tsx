import { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Label } from './ui/Label';
import { getSubjectColors } from '@lesson-browser/utils/scheduleColors';

interface ScheduleCell {
  subject: string;
  grade: string | null;
  homeroom: string | null;
  plan_slot_group_id?: string | null;
}

interface ScheduleCellProps {
  cell: ScheduleCell | null;
  timeSlot: string;  // "8:15 - 8:30"
  dayOfWeek: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  onChange: (cell: ScheduleCell | null) => void;
  existingGroups: string[];
  hasGroupConflict?: boolean;
}

const NON_CLASS_PERIODS = [
  'PREP',
  'PREP TIME',
  'Prep Time',
  'Prep',
  'A.M. Routine',
  'AM Routine',
  'Morning Routine',
  'Lunch',
  'LUNCH',
  'Dismissal',
  'DISMISSAL'
];

function isNonClassPeriod(subject: string): boolean {
  if (!subject) return false;
  return NON_CLASS_PERIODS.includes(subject.trim().toUpperCase());
}

function normalizeSubject(subject: string): string {
  if (!subject) return '';
  
  const normalized = subject.trim().toUpperCase();
  
  if (normalized === 'PREP' || normalized === 'PREP TIME') {
    return 'PREP';
  }
  
  if (normalized === 'A.M. ROUTINE' || normalized === 'AM ROUTINE' || normalized === 'MORNING ROUTINE') {
    return 'A.M. Routine';
  }
  
  if (normalized === 'LUNCH') {
    return 'Lunch';
  }
  
  if (normalized === 'DISMISSAL') {
    return 'Dismissal';
  }
  
  return subject.trim();
}

function formatCellDisplay(subject: string, grade: string | null, homeroom: string | null): string {
  if (!subject) return '';
  
  if (isNonClassPeriod(subject)) {
    return subject;
  }
  
  const parts = [subject];
  if (grade) parts.push(`(${grade})`);
  if (homeroom) parts.push(homeroom);
  
  return parts.join(' ');
}

export function ScheduleCell({
  cell,
  timeSlot,
  dayOfWeek,
  onChange,
  existingGroups,
  hasGroupConflict = false,
}: ScheduleCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [subject, setSubject] = useState(cell?.subject || '');
  const [grade, setGrade] = useState(cell?.grade || '');
  const [homeroom, setHomeroom] = useState(cell?.homeroom || '');
  const [planSlotGroupId, setPlanSlotGroupId] = useState(cell?.plan_slot_group_id || '');
  
  useEffect(() => {
    if (cell) {
      setSubject(cell.subject || '');
      setGrade(cell.grade || '');
      setHomeroom(cell.homeroom || '');
      setPlanSlotGroupId(cell.plan_slot_group_id || '');
    } else {
      setSubject('');
      setGrade('');
      setHomeroom('');
      setPlanSlotGroupId('');
    }
  }, [cell]);
  
  const isNonClass = isNonClassPeriod(subject);
  const displayText = cell ? formatCellDisplay(cell.subject, cell.grade, cell.homeroom) : '';
  const cellColors = getSubjectColors(cell?.subject, cell?.grade, cell?.homeroom);
  
  const handleSave = () => {
    const normalizedSubject = normalizeSubject(subject);
    
    if (!normalizedSubject) {
      onChange(null);
      setIsEditing(false);
      return;
    }
    
    const isNonClass = isNonClassPeriod(normalizedSubject);
    
    const normalizedGroup = planSlotGroupId.trim();

    const newCell: ScheduleCell = {
      subject: normalizedSubject,
      grade: isNonClass ? null : (grade.trim() || null),
      homeroom: isNonClass ? null : (homeroom.trim() || null),
      plan_slot_group_id: isNonClass ? null : (normalizedGroup || null),
    };
    
    onChange(newCell);
    setIsEditing(false);
  };
  
  const handleCancel = () => {
    setSubject(cell?.subject || '');
    setGrade(cell?.grade || '');
    setHomeroom(cell?.homeroom || '');
    setIsEditing(false);
  };
  
  const handleClearCell = () => {
    setSubject('');
    setGrade('');
    setHomeroom('');
    setPlanSlotGroupId('');
    onChange(null);
    setIsEditing(false);
  };

  const handleSubjectChange = (newSubject: string) => {
    setSubject(newSubject);
    
    if (isNonClassPeriod(newSubject)) {
      setGrade('');
      setHomeroom('');
    }

    if (isNonClassPeriod(newSubject)) {
      setPlanSlotGroupId('');
    }
  };
  
  const sanitizedTimeSlot = timeSlot.replace(/[^a-z0-9]/gi, '-').toLowerCase();
  const groupOptionsId = `group-options-${dayOfWeek}-${sanitizedTimeSlot}`;
  
  if (isEditing) {
    return (
      <td className="border p-2 bg-card">
        <div className="space-y-2 min-w-[200px]">
          <div>
            <Label htmlFor={`subject-${dayOfWeek}-${timeSlot}`} className="text-xs">Subject/Time</Label>
            <Input
              id={`subject-${dayOfWeek}-${timeSlot}`}
              type="text"
              placeholder="ELA, PREP, Lunch..."
              value={subject}
              onChange={(e) => handleSubjectChange(e.target.value)}
              className="h-8 text-sm"
              autoFocus
            />
          </div>
          <div>
            <Label htmlFor={`grade-${dayOfWeek}-${timeSlot}`} className="text-xs">Grade</Label>
            <Input
              id={`grade-${dayOfWeek}-${timeSlot}`}
              type="text"
              placeholder="5, 2, K..."
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
              disabled={isNonClass}
              className="h-8 text-sm"
            />
          </div>
          <div>
            <Label htmlFor={`homeroom-${dayOfWeek}-${timeSlot}`} className="text-xs">Homeroom</Label>
            <Input
              id={`homeroom-${dayOfWeek}-${timeSlot}`}
              type="text"
              placeholder="T5, 209, T2..."
              value={homeroom}
              onChange={(e) => setHomeroom(e.target.value)}
              disabled={isNonClass}
              className="h-8 text-sm"
            />
          </div>
          <div>
            <Label htmlFor={`group-${dayOfWeek}-${timeSlot}`} className="text-xs">
              Linked Lesson Group
            </Label>
            <div className="flex gap-2">
              <Input
                id={`group-${dayOfWeek}-${timeSlot}`}
                type="text"
                placeholder="e.g., Morning ELA Block"
                value={planSlotGroupId}
                onChange={(e) => setPlanSlotGroupId(e.target.value)}
                disabled={isNonClass}
                className="h-8 text-sm"
                list={groupOptionsId}
              />
              <datalist id={groupOptionsId}>
                {existingGroups
                  .filter((group) => group !== planSlotGroupId)
                  .map((group) => (
                    <option key={`${groupOptionsId}-${group}`} value={group} />
                  ))}
              </datalist>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-8 text-xs"
                onClick={() => setPlanSlotGroupId('')}
                disabled={!planSlotGroupId}
                aria-label="Remove linked lesson group label"
              >
                <span className="sr-only">Remove linked lesson group label</span>
                <span aria-hidden="true">&times;</span>
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              Use the same label for every period that should share one lesson plan slot.
            </p>
            {hasGroupConflict && (
              <p className="text-[11px] text-destructive mt-1">
                This group has mismatched subject/grade/homeroom in another period.
              </p>
            )}
          </div>
          <div className="flex gap-1">
            <Button
              size="sm"
              onClick={handleSave}
              className="flex-1 h-7 text-xs"
            >
              Save
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
              className="flex-1 h-7 text-xs"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={handleClearCell}
              className="flex-1 h-7 text-xs"
            >
              Clear Cell
            </Button>
          </div>
        </div>
      </td>
    );
  }
  
  // Apply color coding based on subject
  const cellClasses = cell 
    ? `${cellColors.bg} ${cellColors.border} ${cellColors.text} border p-2 cursor-pointer hover:opacity-80 min-w-[150px] transition-opacity`
    : "border p-2 cursor-pointer hover:bg-accent min-w-[150px]";
  
  return (
    <td
      className={cellClasses}
      onClick={() => setIsEditing(true)}
      title={cell ? `Click to edit ${cell.subject}` : "Click to add"}
    >
      <div className={`text-sm font-medium ${cell ? cellColors.text : ''}`}>
        {displayText || (
          <span className="text-muted-foreground italic">Click to add</span>
        )}
      </div>
      {cell?.plan_slot_group_id && (
        <div
          className={`mt-1 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${
            hasGroupConflict
              ? 'border-destructive/40 bg-destructive/10 text-destructive'
              : 'border-muted bg-muted/60 text-muted-foreground'
          }`}
        >
          Linked: {cell.plan_slot_group_id}
          {hasGroupConflict && <span className="ml-1 font-semibold">• Fix mismatch</span>}
        </div>
      )}
    </td>
  );
}

