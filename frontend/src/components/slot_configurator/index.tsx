import React from 'react';
import { Plus } from 'lucide-react';
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useSlotConfigurator } from './useSlotConfigurator';
import { SortableSlotItem, MAX_SLOTS } from './SortableSlotItem';
import { Button } from '../ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';

export const SlotConfiguratorView: React.FC = () => {
  const {
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
  } = useSlotConfigurator();

  if (!currentUser) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please select a user to configure class slots
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Class Slots Configuration</CardTitle>
            <CardDescription>
              Configure up to {MAX_SLOTS} class slots. Drag to reorder and add linked lesson group
              labels for schedule coupling.
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
            No slots configured. Click &quot;Add Slot&quot; to get started.
          </div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
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

        {nextAvailableSlotNumber !== undefined && (
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
