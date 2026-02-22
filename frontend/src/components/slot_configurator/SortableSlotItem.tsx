import React, { useState } from 'react';
import { GripVertical, Trash2 } from 'lucide-react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ClassSlot } from '@lesson-api';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Label } from '../ui/Label';
import { SUBJECTS, GRADES } from '../../lib/utils';

export const MAX_SLOTS = 6;

export interface SortableSlotItemProps {
  slot: ClassSlot;
  index: number;
  onUpdate: (slotId: string, data: Partial<ClassSlot>) => void;
  onSave: (slotId: string) => void;
  onDelete: (slotId: string) => void;
  linkedCount?: number;
}

export const SortableSlotItem: React.FC<SortableSlotItemProps> = ({
  slot,
  index,
  onUpdate,
  onSave,
  onDelete,
  linkedCount,
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: slot.id,
  });
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const normalizedGroupLabel = slot.plan_group_label?.trim() || '';
  const suggestedGroupLabel = [slot.subject, slot.grade ? `Grade ${slot.grade}` : null, slot.homeroom]
    .filter(Boolean)
    .join(' - ');
  const slotBackgroundClass = index % 2 === 0 ? 'bg-card' : 'bg-muted/50';

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${slotBackgroundClass} border rounded-lg p-4 mb-3`}
    >
      <div className="flex items-start gap-3">
        <button
          className="mt-2 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="w-5 h-5" />
        </button>

        <div className="flex-1 grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor={`teacher-first-${slot.id}`}>Teacher First Name</Label>
            <Input
              id={`teacher-first-${slot.id}`}
              name={`teacher-first-${slot.id}`}
              placeholder="e.g., Sarah"
              value={slot.primary_teacher_first_name || ''}
              onChange={(e) =>
                onUpdate(slot.id, {
                  primary_teacher_first_name: e.target.value,
                  primary_teacher_last_name: slot.primary_teacher_last_name,
                })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`teacher-last-${slot.id}`}>Teacher Last Name</Label>
            <Input
              id={`teacher-last-${slot.id}`}
              name={`teacher-last-${slot.id}`}
              placeholder="e.g., Lang"
              value={slot.primary_teacher_last_name || ''}
              onChange={(e) =>
                onUpdate(slot.id, {
                  primary_teacher_first_name: slot.primary_teacher_first_name,
                  primary_teacher_last_name: e.target.value,
                })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`subject-${slot.id}`}>Subject</Label>
            <Select
              id={`subject-${slot.id}`}
              name={`subject-${slot.id}`}
              value={slot.subject}
              onChange={(e) => onUpdate(slot.id, { subject: e.target.value })}
            >
              <option value="">Select...</option>
              {SUBJECTS.map((subject) => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor={`grade-${slot.id}`}>Grade</Label>
            <Select
              id={`grade-${slot.id}`}
              name={`grade-${slot.id}`}
              value={slot.grade}
              onChange={(e) => onUpdate(slot.id, { grade: e.target.value })}
            >
              <option value="">Select...</option>
              {GRADES.map((grade) => (
                <option key={grade} value={grade}>
                  Grade {grade}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor={`homeroom-${slot.id}`}>Homeroom</Label>
            <Input
              id={`homeroom-${slot.id}`}
              name={`homeroom-${slot.id}`}
              placeholder="e.g., T5"
              value={slot.homeroom || ''}
              onChange={(e) => onUpdate(slot.id, { homeroom: e.target.value })}
            />
          </div>

          <div className="space-y-2 col-span-2">
            <Label htmlFor={`plan-group-${slot.id}`}>Linked Lesson Group Label</Label>
            <Input
              id={`plan-group-${slot.id}`}
              name={`plan-group-${slot.id}`}
              placeholder="e.g., ELA G3 Morning Block"
              value={slot.plan_group_label || ''}
              onChange={(e) => onUpdate(slot.id, { plan_group_label: e.target.value })}
            />
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span>
                Suggested:{' '}
                {suggestedGroupLabel || 'Add subject/grade/homeroom to generate a label'}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-6 px-2"
                onClick={() => onUpdate(slot.id, { plan_group_label: suggestedGroupLabel || '' })}
                disabled={!suggestedGroupLabel}
              >
                Use suggestion
              </Button>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 mt-2">
          <Button
            size="sm"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() => onSave(slot.id)}
          >
            Save
          </Button>
          {showDeleteConfirm ? (
            <div className="flex flex-col items-end gap-2">
              <p className="text-xs text-muted-foreground">
                Are you sure you want to delete this slot?
              </p>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setShowDeleteConfirm(false)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    onDelete(slot.id);
                  }}
                >
                  Delete
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => setShowDeleteConfirm(true)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      <div className="ml-8 mt-2 text-xs text-muted-foreground flex flex-wrap gap-3">
        <span>
          Slot {slot.slot_number}{' '}
          {slot.display_order !== null && `(Display order: ${slot.display_order})`}
        </span>
        {normalizedGroupLabel && typeof linkedCount === 'number' && (
          <span>
            Linked periods: <span className="font-semibold">{linkedCount}</span>
          </span>
        )}
      </div>
    </div>
  );
};
