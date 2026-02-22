import { FileText, CheckCircle2, Loader2, Play, CheckSquare, Square } from 'lucide-react';
import { Button } from '../ui/Button';
import type { WeekStatus } from './useBatchProcessor';

export interface SlotItem {
  id: number;
  slot_number: number;
  display_order?: number;
  subject: string;
  primary_teacher_name?: string;
  grade: string;
}

interface SlotSectionProps {
  sortedSlots: SlotItem[];
  selectedSlots: Set<number>;
  weekStatus: WeekStatus | null;
  forceSlots: Set<number>;
  isLoadingStatus: boolean;
  isProcessing: boolean;
  toggleSlot: (id: number) => void;
  selectAllSlots: () => void;
  deselectAllSlots: () => void;
  toggleForceSlot: (slotNumber: number) => void;
}

export function SlotSection({
  sortedSlots,
  selectedSlots,
  weekStatus,
  forceSlots,
  isLoadingStatus,
  isProcessing,
  toggleSlot,
  selectAllSlots,
  deselectAllSlots,
  toggleForceSlot,
}: SlotSectionProps) {
  return (
    <div className="pt-4 border-t">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium">Select Slots to Process:</h4>
          {isLoadingStatus && <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={selectAllSlots} disabled={isProcessing}>
            <CheckSquare className="w-4 h-4 mr-1" />
            Select All
          </Button>
          <Button variant="outline" size="sm" onClick={deselectAllSlots} disabled={isProcessing}>
            <Square className="w-4 h-4 mr-1" />
            Deselect All
          </Button>
        </div>
      </div>
      <div className="space-y-2">
        {sortedSlots.map((slot) => {
          const isSelected = selectedSlots.has(slot.id);
          return (
            <div
              key={slot.id}
              className={`flex items-center gap-3 text-sm p-2 rounded cursor-pointer transition-colors ${isSelected ? 'bg-primary/10 border border-primary/20' : 'bg-muted/50 hover:bg-muted'}`}
              onClick={() => !isProcessing && toggleSlot(slot.id)}
            >
              <input
                type="checkbox"
                id={`slot-checkbox-${slot.id}`}
                name={`slot-${slot.id}`}
                checked={isSelected}
                onChange={() => toggleSlot(slot.id)}
                disabled={isProcessing}
                className="w-4 h-4 cursor-pointer"
                onClick={(e) => e.stopPropagation()}
              />
              <FileText className="w-4 h-4 text-muted-foreground" />
              <div className="flex-1 flex justify-between items-center">
                <div>
                  <span className="font-medium">{slot.subject}</span>
                  {' - '}
                  <span className="text-muted-foreground">
                    {slot.primary_teacher_name || 'No teacher'}, Grade {slot.grade}
                  </span>
                </div>
                {weekStatus && weekStatus.done_slots.includes(slot.slot_number) && (
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-green-600 text-xs font-medium bg-green-50 px-2 py-0.5 rounded-full border border-green-100">
                      <CheckCircle2 className="w-3 h-3" />
                      Done
                    </div>
                    {isSelected && (
                      <div
                        className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] uppercase tracking-wider font-bold transition-all ${forceSlots.has(slot.slot_number) ? 'bg-orange-500 text-white border-orange-600 shadow-sm' : 'bg-white text-muted-foreground border-muted-foreground/20 hover:border-orange-400 hover:text-orange-600'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleForceSlot(slot.slot_number);
                        }}
                        title="Force AI transformation for this slot"
                      >
                        {forceSlots.has(slot.slot_number) ? (
                          <>
                            <Loader2 className="w-2.5 h-2.5 animate-spin" />
                            Recall AI
                          </>
                        ) : (
                          <>
                            <Play className="w-2.5 h-2.5" />
                            Skip AI
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
