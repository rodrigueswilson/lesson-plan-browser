import { useState, useEffect, useRef } from 'react';
import { useStore } from '@lesson-browser';
import {
  planApi,
  createProgressStream,
  userApi,
  type ClassSlot,
  type ProgressPollData,
} from '@lesson-api';

export type ButtonState = 'idle' | 'processing' | 'success' | 'error';

export interface WeekStatus {
  plan_id?: string | null;
  done_slots: number[];
  missing_slots: number[];
  status: string | null;
  total_slots: number;
}

export interface RecentWeek {
  week_of: string;
  display: string;
  folder_name: string;
}

export interface ProcessResult {
  success?: boolean;
  processed_slots?: number;
  failed_slots?: number;
  output_file?: string;
  errors?: Array<{ slot?: number; subject?: string; error?: string } | string>;
}

const BATCH_PROGRESS_WATCHDOG_MS = 3 * 60 * 1000;

function isTerminalProgressStatus(status: unknown): boolean {
  const s = String(status ?? '').toLowerCase();
  return (
    s === 'completed' ||
    s === 'complete' ||
    s === 'done' ||
    s === 'failed' ||
    s === 'error'
  );
}

function isProgressSuccessStatus(status: unknown): boolean {
  const s = String(status ?? '').toLowerCase();
  return s === 'completed' || s === 'complete' || s === 'done';
}

function isProgressFailureStatus(status: unknown): boolean {
  const s = String(status ?? '').toLowerCase();
  return s === 'failed' || s === 'error';
}

export function useBatchProcessor() {
  const {
    currentUser,
    slots,
    isProcessing,
    setIsProcessing,
    progress,
    setProgress,
    selectedSlots,
    setSelectedSlots,
    toggleSlot,
    selectAllSlots,
    deselectAllSlots,
  } = useStore();

  const [weekOf, setWeekOf] = useState('');
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentWeeks, setRecentWeeks] = useState<RecentWeek[]>([]);
  const [availableWeeks, setAvailableWeeks] = useState<RecentWeek[]>([]);
  const [buttonState, setButtonState] = useState<ButtonState>('idle');
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [partial, setPartial] = useState(true);
  const [missingOnly, setMissingOnly] = useState(true);
  const [recallAiForSelected, setRecallAiForSelected] = useState(false);
  const [forceSlots, setForceSlots] = useState<Set<number>>(new Set());
  const [weekStatus, setWeekStatus] = useState<WeekStatus | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStageLabel, setProgressStageLabel] = useState('Queued');
  const [progressSlotCounts, setProgressSlotCounts] = useState({ completed: 0, total: 0 });
  const [progressLastUpdateAt, setProgressLastUpdateAt] = useState<string | null>(null);
  const [progressStalled, setProgressStalled] = useState(false);
  const appliedAutoDeselectRef = useRef<string | null>(null);

  useEffect(() => {
    if (slots.length > 0 && selectedSlots.size === 0) {
      selectAllSlots();
    }
  }, [slots.length, selectedSlots.size, selectAllSlots]);

  useEffect(() => {
    appliedAutoDeselectRef.current = null;
  }, [weekOf]);

  useEffect(() => {
    if (
      !weekOf ||
      !weekStatus?.plan_id ||
      !Array.isArray(weekStatus.done_slots) ||
      weekStatus.done_slots.length === 0 ||
      slots.length === 0
    ) {
      return;
    }
    if (appliedAutoDeselectRef.current === weekOf) return;
    appliedAutoDeselectRef.current = weekOf;
    const missingIds = slots
      .filter((s: ClassSlot) => !weekStatus.done_slots.includes(s.slot_number))
      .map((s: ClassSlot) => String(s.id));
    setSelectedSlots(new Set(missingIds));
  }, [weekOf, weekStatus?.plan_id, weekStatus?.done_slots, slots, setSelectedSlots]);

  const loadRecentWeeks = async () => {
    if (!currentUser) {
      console.log('[BatchProcessor] No current user, skipping recent weeks load');
      return;
    }
    console.log('[BatchProcessor] Loading recent weeks for user:', currentUser.id);
    try {
      const response = await userApi.getRecentWeeks(currentUser.id, 5);
      console.log('[BatchProcessor] Recent weeks response:', response.data);
      const raw = (response.data ?? []) as Array<{ week_of: string; display: string; folder_name?: unknown }>;
      const weeks: RecentWeek[] = raw.map((w) => ({
        week_of: w.week_of,
        display: w.display,
        folder_name: typeof w.folder_name === 'string' ? w.folder_name : '',
      }));
      setRecentWeeks(weeks);
      if (response.data.length === 0 && currentUser.base_path_override) {
        console.warn('[BatchProcessor] No recent weeks found in configured folder. Check if folders exist at:', currentUser.base_path_override);
      } else if (response.data.length === 0) {
        console.log('[BatchProcessor] No base_path_override configured. User needs to set lesson plan folder path in settings.');
      }
    } catch (err) {
      console.error('[BatchProcessor] Failed to load recent weeks:', err);
      setRecentWeeks([]);
    }
  };

  const loadAvailableWeeks = async () => {
    if (!currentUser) return;
    try {
      const response = await userApi.getAvailableWeeks(
        currentUser.id,
        currentUser.id
      );
      const raw = (response.data ?? []) as Array<{
        week_of: string;
        display: string;
        folder_name?: unknown;
      }>;
      const weeks: RecentWeek[] = raw.map((w) => ({
        week_of: w.week_of,
        display: w.display,
        folder_name: typeof w.folder_name === 'string' ? w.folder_name : '',
      }));
      setAvailableWeeks(weeks);
    } catch (err) {
      console.error('[BatchProcessor] Failed to load available weeks:', err);
      setAvailableWeeks([]);
    }
  };

  useEffect(() => {
    if (currentUser?.id) {
      loadRecentWeeks();
      loadAvailableWeeks();
    }
  }, [currentUser?.id]);

  useEffect(() => {
    if (buttonState === 'success' || buttonState === 'error') {
      const timer = setTimeout(() => setButtonState('idle'), 3000);
      return () => clearTimeout(timer);
    }
  }, [buttonState]);

  useEffect(() => {
    if (currentUser?.id && weekOf && weekOf.length >= 5) {
      void fetchWeekStatus();
    } else {
      setWeekStatus(null);
    }
  }, [currentUser?.id, weekOf]);

  const fetchWeekStatus = async (): Promise<WeekStatus | null> => {
    if (!currentUser?.id || !weekOf) return null;
    setIsLoadingStatus(true);
    try {
      const response = await planApi.getWeekStatus(currentUser.id, weekOf);
      const data = response.data;
      setWeekStatus((prev) => {
        if (!data?.plan_id) {
          return data ?? null;
        }
        const prevDone =
          prev?.plan_id === data.plan_id ? (prev?.done_slots ?? []) : [];
        const incDone = data.done_slots ?? [];
        const merged = [...new Set([...prevDone, ...incDone])].sort(
          (a, b) => a - b
        );
        const allNums = slots.map((s: ClassSlot) => s.slot_number);
        const missing = allNums.filter((n: number) => !merged.includes(n));
        return {
          ...data,
          done_slots: merged,
          missing_slots: missing,
          total_slots: slots.length,
        };
      });
      setForceSlots(new Set());
      return data ?? null;
    } catch (err) {
      console.error('[BatchProcessor] Failed to fetch week status:', err);
      setWeekStatus(null);
      return null;
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const refreshWeekStatusAfterSuccess = async (
    planId: string,
    processedSlotNumbers: number[]
  ) => {
    setWeekStatus((prev) => {
      const prevDone = prev?.done_slots ?? [];
      const merged = [...new Set([...prevDone, ...processedSlotNumbers])].sort(
        (a, b) => a - b
      );
      const allNums = slots.map((s: ClassSlot) => s.slot_number);
      const missing = allNums.filter((n: number) => !merged.includes(n));
      return {
        plan_id: planId,
        status: 'completed',
        done_slots: merged,
        missing_slots: missing,
        total_slots: slots.length,
      };
    });
    setForceSlots(new Set());
    void loadRecentWeeks();
    void loadAvailableWeeks();
    await fetchWeekStatus();
    await new Promise((r) => setTimeout(r, 400));
    await fetchWeekStatus();
    await new Promise((r) => setTimeout(r, 400));
    await fetchWeekStatus();
  };

  const toggleForceSlot = (slotNumber: number) => {
    setForceSlots((prev) => {
      const next = new Set(prev);
      if (next.has(slotNumber)) {
        next.delete(slotNumber);
      } else {
        next.add(slotNumber);
      }
      return next;
    });
  };

  const handleProcessClick = () => {
    if (!currentUser || !weekOf || selectedSlots.size === 0) return;
    setShowConfirmDialog(true);
  };

  const handleConfirmProcess = async () => {
    setShowConfirmDialog(false);
    if (!currentUser || !weekOf || selectedSlots.size === 0) return;

    const capturedSelectedIds = new Set(selectedSlots);
    const capturedSlotNumbers = slots
      .filter((s: ClassSlot) => capturedSelectedIds.has(String(s.id)))
      .map((s: ClassSlot) => s.slot_number);

    setButtonState('processing');
    setIsProcessing(true);
    setError(null);
    setResult(null);
    setProgress({ current: 0, total: selectedSlots.size, message: 'Starting...' });
    setProgressPercent(0);
    setProgressStageLabel('Queued');
    setProgressSlotCounts({ completed: 0, total: capturedSlotNumbers.length || selectedSlots.size });
    setProgressLastUpdateAt(null);
    setProgressStalled(false);

    try {
      const selectedSlotIds = Array.from(selectedSlots).map(String);
      const response = await planApi.process(
        currentUser.id,
        weekOf,
        'openai',
        selectedSlotIds,
        partial,
        missingOnly,
        recallAiForSelected ? capturedSlotNumbers : Array.from(forceSlots)
      );

      if (response.data.plan_id) {
        let progressCompleted = false;
        let progressHandle: { close: () => void } | null = null;
        let watchdogTimer: ReturnType<typeof setTimeout> | null = null;

        const clearWatchdog = () => {
          if (watchdogTimer !== null) {
            clearTimeout(watchdogTimer);
            watchdogTimer = null;
          }
        };

        const runWatchdogRecovery = () => {
          if (progressCompleted) return;
          setProgressStalled(true);
          setProgressStageLabel('Waiting for backend progress update');
          setProgress({
            current: progressSlotCounts.completed,
            total: progressSlotCounts.total || selectedSlots.size,
            message: 'Progress stream stalled. Waiting for backend completion signal...',
          });
          watchdogTimer = setTimeout(runWatchdogRecovery, BATCH_PROGRESS_WATCHDOG_MS);
        };

        watchdogTimer = setTimeout(runWatchdogRecovery, BATCH_PROGRESS_WATCHDOG_MS);

        try {
          progressHandle = createProgressStream(response.data.plan_id, (data: ProgressPollData) => {
            setProgressStalled(false);
            const slotTotal = data.total_slots > 0 ? data.total_slots : selectedSlots.size;
            const slotCompleted = Math.min(data.completed_slots ?? 0, slotTotal);
            const progressPct = Math.max(0, Math.min(100, data.progress_percent ?? data.progress ?? 0));
            setProgressPercent(progressPct);
            setProgressStageLabel(data.stage_label || data.stage || 'Processing');
            setProgressSlotCounts({ completed: slotCompleted, total: slotTotal });
            if (data.last_update_at) {
              setProgressLastUpdateAt(data.last_update_at);
            }
            setProgress({
              current: slotCompleted,
              total: slotTotal,
              message: data.message || 'Processing...',
            });

            if (!isTerminalProgressStatus(data.status)) {
              return;
            }

            if (progressCompleted) return;
            progressCompleted = true;
            clearWatchdog();
            progressHandle?.close();
            setIsProcessing(false);

            if (isProgressSuccessStatus(data.status)) {
              const finalResult: ProcessResult = {
                ...response.data,
                processed_slots: data.processed_slots ?? response.data.processed_slots ?? 0,
                failed_slots: data.failed_slots ?? response.data.failed_slots ?? 0,
                output_file: data.output_file ?? response.data.output_file,
                errors: data.errors ?? response.data.errors,
              };
              setResult(finalResult);
              setButtonState('success');
              setProgress({
                current: slotTotal,
                total: slotTotal,
                message: 'Completed successfully',
              });
              setProgressPercent(100);
              setProgressStageLabel('Completed');
              void refreshWeekStatusAfterSuccess(
                response.data.plan_id,
                capturedSlotNumbers
              );
            } else if (isProgressFailureStatus(data.status)) {
              const errorMessage = data.message || 'Processing failed';
              setError(errorMessage);
              setButtonState('error');
              const finalResult: ProcessResult = {
                ...response.data,
                processed_slots: data.processed_slots ?? 0,
                failed_slots: data.failed_slots ?? 0,
                errors: data.errors ?? [],
              };
              setResult(finalResult);
            }
          });
        } catch (streamErr) {
          clearWatchdog();
          throw streamErr;
        }
      } else {
        setIsProcessing(false);
        if (response.data.success) {
          setResult(response.data);
          setButtonState('success');
          if (response.data.plan_id) {
            void refreshWeekStatusAfterSuccess(
              response.data.plan_id,
              capturedSlotNumbers
            );
          }
        } else {
          setError('Processing failed');
          setButtonState('error');
        }
      }
    } catch (err: any) {
      setIsProcessing(false);
      setError(err.response?.data?.detail || err.message || 'Processing failed');
      setButtonState('error');
    }
  };

  const handleDownload = () => {
    if (!result?.output_file) return;
    const downloadUrl = `http://localhost:8000/api/render/${result.output_file.split('/').pop()}`;
    window.open(downloadUrl, '_blank');
  };

  const progressPercentage = progress.total > 0 ? (progress.current / progress.total) * 100 : 0;

  const sortedSlots = [...slots].sort((a, b) => {
    const orderA = a.display_order ?? a.slot_number;
    const orderB = b.display_order ?? b.slot_number;
    return orderA - orderB;
  });

  return {
    currentUser,
    slots,
    isProcessing,
    selectedSlots,
    weekOf,
    setWeekOf,
    result,
    error,
    recentWeeks,
    availableWeeks,
    buttonState,
    showConfirmDialog,
    setShowConfirmDialog,
    partial,
    setPartial,
    missingOnly,
    setMissingOnly,
    recallAiForSelected,
    setRecallAiForSelected,
    forceSlots,
    weekStatus,
    isLoadingStatus,
    progress,
    progressPercentage: progressPercent || progressPercentage,
    progressStageLabel,
    progressSlotCounts,
    progressLastUpdateAt,
    progressStalled,
    sortedSlots,
    toggleSlot,
    selectAllSlots,
    deselectAllSlots,
    toggleForceSlot,
    handleProcessClick,
    handleConfirmProcess,
    handleDownload,
  };
}
