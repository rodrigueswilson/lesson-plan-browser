import { useState, useEffect, useMemo } from 'react';
import {
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import { arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useStore } from '@lesson-browser';
import { slotApi, ClassSlot, scheduleApi, ScheduleEntry } from '@lesson-api';
import { MAX_SLOTS } from './SortableSlotItem';

export function useSlotConfigurator() {
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
          setScheduleEntries(Array.isArray(data) ? data : []);
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

    const oldIndex = slots.findIndex((s: ClassSlot) => s.id === active.id);
    const newIndex = slots.findIndex((s: ClassSlot) => s.id === over.id);

    const reorderedSlots = arrayMove(slots, oldIndex, newIndex) as ClassSlot[];

    const updatedSlots: ClassSlot[] = reorderedSlots.map((slot, index) => ({
      ...slot,
      display_order: index + 1,
    }));

    setSlots(updatedSlots);

    try {
      await Promise.all(
        updatedSlots.map((slot: ClassSlot) =>
          slotApi.update(slot.id, { display_order: slot.display_order })
        )
      );
    } catch (error) {
      console.error('Failed to update slot order:', error);
    }
  };

  const handleUpdateSlot = async (slotId: string, data: Partial<ClassSlot>) => {
    updateSlot(slotId, data);

    try {
      await slotApi.update(slotId, data, currentUser?.id);
    } catch (error: unknown) {
      const err = error as { response?: { status?: number } };
      if (err?.response?.status !== 404) {
        console.error('Failed to update slot:', error);
      }
    }
  };

  const handleDeleteSlot = async (slotId: string) => {
    if (!currentUser) return;

    const previousSlots = [...slots];
    removeSlot(slotId);

    try {
      await slotApi.delete(slotId, currentUser.id);
    } catch (error) {
      console.error('Failed to delete slot:', error);
      setSlots(previousSlots);
      alert('Failed to delete slot. Please try again.');
    }
  };

  const handleSaveSlot = async (slotId: string) => {
    if (!currentUser) return;
    const slot = slots.find((s: ClassSlot) => s.id === slotId);
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

  const getNextAvailableSlotNumber = (): number | undefined => {
    const usedSlots = new Set(slots.map((s: ClassSlot) => s.slot_number));
    return Array.from({ length: MAX_SLOTS }, (_, idx) => idx + 1).find(
      (slotNumber) => !usedSlots.has(slotNumber)
    );
  };

  const handleAddSlot = async () => {
    if (!currentUser) return;

    const nextSlotNumber = getNextAvailableSlotNumber();

    if (!nextSlotNumber) {
      alert(
        `You already have ${MAX_SLOTS} slots configured. Delete one before adding another.`
      );
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

  const sortedSlots = [...slots].sort((a: ClassSlot, b: ClassSlot) => {
    const orderA = a.display_order ?? a.slot_number;
    const orderB = b.display_order ?? b.slot_number;
    return orderA - orderB;
  });

  const nextAvailableSlotNumber = getNextAvailableSlotNumber();

  return {
    currentUser,
    slots,
    sortedSlots,
    groupUsageCounts,
    nextAvailableSlotNumber,
    isAdding,
    sensors,
    handleDragEnd,
    handleUpdateSlot,
    handleDeleteSlot,
    handleSaveSlot,
    handleAddSlot,
  };
}
