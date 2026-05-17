import { create } from 'zustand';
import { User, ClassSlot, WeeklyPlan } from '@lesson-api';

function toSlotIdKey(id: string | number): string {
  return String(id);
}

export interface AppState {
  // Current user
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  
  // Users list
  users: User[];
  setUsers: (users: User[]) => void;
  
  // Class slots
  slots: ClassSlot[];
  setSlots: (slots: ClassSlot[]) => void;
  addSlot: (slot: ClassSlot) => void;
  updateSlot: (slotId: string, data: Partial<ClassSlot>) => void;
  removeSlot: (slotId: string) => void;
  
  // Weekly plans
  plans: WeeklyPlan[];
  setPlans: (plans: WeeklyPlan[]) => void;
  
  // Processing state
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  
  // Progress tracking
  progress: {
    current: number;
    total: number;
    message: string;
  };
  setProgress: (progress: { current: number; total: number; message: string }) => void;
  
  // Selected week
  selectedWeek: string | null;
  setSelectedWeek: (week: string | null) => void;
  
  // Selected slots for processing
  selectedSlots: Set<string>;
  setSelectedSlots: (slots: Set<string>) => void;
  toggleSlot: (slotId: string) => void;
  selectAllSlots: () => void;
  deselectAllSlots: () => void;
}

export const useStore = create<AppState>((set) => ({
  // Current user
  currentUser: null,
  setCurrentUser: (user) => set({ currentUser: user }),
  
  // Users
  users: [],
  setUsers: (users) => set({ users }),
  
  // Slots
  slots: [],
  setSlots: (slots) =>
    set((state) => {
      if (slots.length === 0) {
        return { slots, selectedSlots: new Set<string>() };
      }
      const validIds = new Set(slots.map((s) => toSlotIdKey(s.id)));
      const pruned = new Set(
        [...state.selectedSlots].map(toSlotIdKey).filter((id) => validIds.has(id))
      );
      return { slots, selectedSlots: pruned };
    }),
  addSlot: (slot) => set((state) => ({ slots: [...state.slots, slot] })),
  updateSlot: (slotId, data) =>
    set((state) => ({
      slots: state.slots.map((slot) =>
        slot.id === slotId ? { ...slot, ...data } : slot
      ),
    })),
  removeSlot: (slotId) =>
    set((state) => {
      const key = toSlotIdKey(slotId);
      const newSelected = new Set(
        [...state.selectedSlots].map(toSlotIdKey)
      );
      newSelected.delete(key);
      return {
        slots: state.slots.filter((slot) => toSlotIdKey(slot.id) !== key),
        selectedSlots: newSelected,
      };
    }),
  
  // Plans
  plans: [],
  setPlans: (plans) => set({ plans }),
  
  // Processing
  isProcessing: false,
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  
  // Progress
  progress: { current: 0, total: 0, message: '' },
  setProgress: (progress) => set({ progress }),
  
  // Selected week
  selectedWeek: null,
  setSelectedWeek: (week) => set({ selectedWeek: week }),
  
  // Selected slots
  selectedSlots: new Set<string>(),
  setSelectedSlots: (slots) =>
    set({ selectedSlots: new Set([...slots].map(toSlotIdKey)) }),
  toggleSlot: (slotId) =>
    set((state) => {
      const key = toSlotIdKey(slotId);
      const newSelected = new Set(
        [...state.selectedSlots].map(toSlotIdKey)
      );
      if (newSelected.has(key)) {
        newSelected.delete(key);
      } else {
        newSelected.add(key);
      }
      return { selectedSlots: newSelected };
    }),
  selectAllSlots: () =>
    set((state) => ({
      selectedSlots: new Set(state.slots.map((s) => toSlotIdKey(s.id))),
    })),
  deselectAllSlots: () => set({ selectedSlots: new Set<string>() }),
}));
