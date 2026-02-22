import { useState, useEffect } from 'react';
import { useStore } from '@lesson-browser';
import { planApi, createProgressStream, userApi } from '@lesson-api';

export type ButtonState = 'idle' | 'processing' | 'success' | 'error';

export interface WeekStatus {
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
  errors?: Array<{ slot: number; subject: string; error: string }>;
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
    toggleSlot,
    selectAllSlots,
    deselectAllSlots,
  } = useStore();

  const [weekOf, setWeekOf] = useState('');
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentWeeks, setRecentWeeks] = useState<RecentWeek[]>([]);
  const [buttonState, setButtonState] = useState<ButtonState>('idle');
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [partial, setPartial] = useState(true);
  const [missingOnly, setMissingOnly] = useState(false);
  const [forceSlots, setForceSlots] = useState<Set<number>>(new Set());
  const [weekStatus, setWeekStatus] = useState<WeekStatus | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);

  useEffect(() => {
    if (slots.length > 0 && selectedSlots.size === 0) {
      selectAllSlots();
    }
  }, [slots.length, selectedSlots.size, selectAllSlots]);

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

  useEffect(() => {
    if (currentUser?.id) {
      loadRecentWeeks();
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
      fetchWeekStatus();
    } else {
      setWeekStatus(null);
    }
  }, [currentUser?.id, weekOf]);

  const fetchWeekStatus = async () => {
    if (!currentUser?.id || !weekOf) return;
    setIsLoadingStatus(true);
    try {
      const response = await planApi.getWeekStatus(currentUser.id, weekOf);
      setWeekStatus(response.data);
      setForceSlots(new Set());
    } catch (err) {
      console.error('[BatchProcessor] Failed to fetch week status:', err);
      setWeekStatus(null);
    } finally {
      setIsLoadingStatus(false);
    }
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

    setButtonState('processing');
    setIsProcessing(true);
    setError(null);
    setResult(null);
    setProgress({ current: 0, total: selectedSlots.size, message: 'Starting...' });

    try {
      const selectedSlotIds = Array.from(selectedSlots).map(String);
      const response = await planApi.process(
        currentUser.id,
        weekOf,
        'openai',
        selectedSlotIds,
        partial,
        missingOnly,
        Array.from(forceSlots)
      );

      if (response.data.plan_id) {
        const eventSource = createProgressStream(response.data.plan_id, (data) => {
          setProgress({
            current: data.current || 0,
            total: data.total || selectedSlots.size,
            message: data.message || 'Processing...',
          });

          if (data.status === 'completed' || data.status === 'complete' || data.status === 'failed' || data.status === 'error') {
            eventSource.close();
            setIsProcessing(false);

            if (data.status === 'completed' || data.status === 'complete') {
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
                current: data.total || selectedSlots.size,
                total: data.total || selectedSlots.size,
                message: 'Completed successfully',
              });
              fetchWeekStatus();
            } else {
              const errorMessage = data.message || data.error || 'Processing failed';
              setError(errorMessage);
              setButtonState('error');
              const finalResult: ProcessResult = {
                ...response.data,
                processed_slots: data.processed_slots ?? 0,
                failed_slots: data.failed_slots ?? 0,
                errors: data.errors ?? (data.errors && Array.isArray(data.errors) ? data.errors : []),
              };
              setResult(finalResult);
            }
          }
        });
      } else {
        setIsProcessing(false);
        if (response.data.success) {
          setResult(response.data);
          setButtonState('success');
          fetchWeekStatus();
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
    buttonState,
    showConfirmDialog,
    setShowConfirmDialog,
    partial,
    setPartial,
    missingOnly,
    setMissingOnly,
    forceSlots,
    weekStatus,
    isLoadingStatus,
    progress,
    progressPercentage,
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
