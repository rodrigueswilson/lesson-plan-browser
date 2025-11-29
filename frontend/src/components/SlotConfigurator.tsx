import React, { useState, useEffect, useMemo } from 'react';
import { GripVertical, Trash2, Plus } from 'lucide-react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useStore } from '@lesson-browser';
import { slotApi, ClassSlot, scheduleApi, ScheduleEntry } from '@lesson-api';
import { Button } from './ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { Label } from './ui/Label';
import { SUBJECTS, GRADES } from '../lib/utils';

const MAX_SLOTS = 6;

interface SortableSlotItemProps {
  slot: ClassSlot;
  index: number;
  onUpdate: (slotId: string, data: Partial<ClassSlot>) => void;
  onSave: (slotId: string) => void;
  onDelete: (slotId: string) => void;
  linkedCount?: number;
}

const SortableSlotItem: React.FC<SortableSlotItemProps> = ({ slot, index, onUpdate, onSave, onDelete, linkedCount }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: slot.id });
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
              onChange={(e) => onUpdate(slot.id, { 
                primary_teacher_first_name: e.target.value,
                primary_teacher_last_name: slot.primary_teacher_last_name 
              })}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor={`teacher-last-${slot.id}`}>Teacher Last Name</Label>
            <Input
              id={`teacher-last-${slot.id}`}
              name={`teacher-last-${slot.id}`}
              placeholder="e.g., Lang"
              value={slot.primary_teacher_last_name || ''}
              onChange={(e) => onUpdate(slot.id, { 
                primary_teacher_first_name: slot.primary_teacher_first_name,
                primary_teacher_last_name: e.target.value 
              })}
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
                onClick={() =>
                  onUpdate(slot.id, { plan_group_label: suggestedGroupLabel || '' })
                }
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteConfirm(false)}
                >
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
          Slot {slot.slot_number} {slot.display_order !== null && `(Display order: ${slot.display_order})`}
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

export const SlotConfigurator: React.FC = () => {
  const { currentUser, slots, setSlots, updateSlot, removeSlot, addSlot } = useStore();
  const [isAdding, setIsAdding] = useState(false);
  const [scheduleEntries, setScheduleEntries] = useState<ScheduleEntry[]>([]);
  
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    if (!currentUser) {
      setScheduleEntries([]);
      return;
    }

    let isMounted = true;
    (async () => {
      try {
        const data = await scheduleApi.getSchedule(currentUser.id);
        if (isMounted) {
          setScheduleEntries(data);
        }
      } catch (error) {
        console.warn('Failed to load schedule for slot context', error);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [currentUser?.id]);

  const groupUsageCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    scheduleEntries.forEach((entry) => {
      const label = entry.plan_slot_group_id?.trim();
      if (!label) return;
      counts[label] = (counts[label] || 0) + 1;
    });
    return counts;
  }, [scheduleEntries]);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (!over || active.id === over.id) return;
    
    const oldIndex = slots.findIndex((s) => s.id === active.id);
    const newIndex = slots.findIndex((s) => s.id === over.id);
    
    const reorderedSlots = arrayMove(slots, oldIndex, newIndex);
    
    // Update display_order for all slots
    const updatedSlots = reorderedSlots.map((slot, index) => ({
      ...slot,
      display_order: index + 1,
    }));
    
    setSlots(updatedSlots);
    
    // Update on server
    try {
      await Promise.all(
        updatedSlots.map((slot) =>
          slotApi.update(slot.id, { display_order: slot.display_order })
        )
      );
    } catch (error) {
      console.error('Failed to update slot order:', error);
    }
  };

  const handleUpdateSlot = async (slotId: string, data: Partial<ClassSlot>) => {
    // Update local state immediately (optimistic update)
    updateSlot(slotId, data);
    
    // Debounce API call to avoid too many requests
    try {
      // Pass currentUser.id for authorization (slot operations don't have userId in URL)
      await slotApi.update(slotId, data, currentUser?.id);
    } catch (error: any) {
      // Silently ignore 404 errors (slot might not exist yet)
      if (error?.response?.status !== 404) {
        console.error('Failed to update slot:', error);
      }
    }
  };

  const handleDeleteSlot = async (slotId: string) => {
    if (!currentUser) return;

    const previousSlots = [...slots];
    removeSlot(slotId);
    
    try {
      // Pass currentUser.id for authorization (slot operations don't have userId in URL)
      await slotApi.delete(slotId, currentUser.id);
    } catch (error) {
      console.error('Failed to delete slot:', error);
      // Restore local state so the user sees that the slot still exists
      setSlots(previousSlots);
      alert('Failed to delete slot. Please try again.');
    }
  };

  const handleSaveSlot = async (slotId: string) => {
    if (!currentUser) return;
    const slot = slots.find((s) => s.id === slotId);
    if (!slot) return;

    const payload: Partial<ClassSlot> = {
      slot_number: slot.slot_number,
      subject: slot.subject,
      grade: slot.grade,
      homeroom: slot.homeroom,
      plan_group_label: slot.plan_group_label,
      display_order: slot.display_order,
      primary_teacher_first_name: slot.primary_teacher_first_name,
      primary_teacher_last_name: slot.primary_teacher_last_name,
      primary_teacher_file_pattern: slot.primary_teacher_file_pattern,
      proficiency_levels: slot.proficiency_levels,
    };

    try {
      await slotApi.update(slotId, payload, currentUser.id);
    } catch (error) {
      console.error('Failed to save slot:', error);
      alert('Failed to save slot. Please try again.');
    }
  };

  const getNextAvailableSlotNumber = () => {
    const usedSlots = new Set(slots.map((s) => s.slot_number));
    return Array.from({ length: MAX_SLOTS }, (_, idx) => idx + 1).find(
      (slotNumber) => !usedSlots.has(slotNumber)
    );
  };

  const handleAddSlot = async () => {
    if (!currentUser) return;
    
    const nextSlotNumber = getNextAvailableSlotNumber();

    if (!nextSlotNumber) {
      alert(`You already have ${MAX_SLOTS} slots configured. Delete one before adding another.`);
      return;
    }
    
    try {
      const response = await slotApi.create(currentUser.id, {
        slot_number: nextSlotNumber,
        subject: '',
        grade: '',
        homeroom: '',
        display_order: slots.length + 1,
      });
      
      addSlot(response.data);
      setIsAdding(false);
    } catch (error) {
      console.error('Failed to add slot:', error);
    }
  };

  if (!currentUser) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please select a user to configure class slots
        </CardContent>
      </Card>
    );
  }

  const sortedSlots = [...slots].sort((a, b) => {
    const orderA = a.display_order ?? a.slot_number;
    const orderB = b.display_order ?? b.slot_number;
    return orderA - orderB;
  });

  const nextAvailableSlotNumber = getNextAvailableSlotNumber();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Class Slots Configuration</CardTitle>
            <CardDescription>
              Configure up to {MAX_SLOTS} class slots. Drag to reorder and add linked lesson group labels for schedule coupling.
            </CardDescription>
          </div>
          <div className="text-sm font-medium">
            {Math.min(slots.length, MAX_SLOTS)} / {MAX_SLOTS} slots
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {sortedSlots.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No slots configured. Click "Add Slot" to get started.
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={sortedSlots.map((s) => s.id)}
              strategy={verticalListSortingStrategy}
            >
              {sortedSlots.map((slot, index) => (
                <SortableSlotItem
                  key={slot.id}
                  slot={slot}
                  index={index}
                  onUpdate={handleUpdateSlot}
                  onSave={handleSaveSlot}
                  onDelete={handleDeleteSlot}
                  linkedCount={
                    slot.plan_group_label?.trim()
                      ? groupUsageCounts[slot.plan_group_label.trim()] || 0
                      : undefined
                  }
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
        
        {nextAvailableSlotNumber && (
          <Button
            variant="outline"
            className="w-full mt-4"
            onClick={handleAddSlot}
            disabled={isAdding}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Slot {nextAvailableSlotNumber}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
