import { useState, useEffect, useRef } from 'react';
import { Grid, CalendarDays, FileText, Clock, PlayCircle, ArrowLeft } from 'lucide-react';
import { WeekView } from './WeekView';
import { DayView } from './DayView';
import { LessonDetailView } from './LessonDetailView';
import { TopNavigationBar } from './TopNavigationBar';
import { planApi, WeeklyPlan, ScheduleEntry, scheduleApi, lessonApi, userApi, ClassSlot, normalizeWeekOfForMatch } from '@lesson-api';
import { useStore } from '../store/useStore';
import { Button } from '@lesson-ui/Button';
import { Select } from '@lesson-ui/Select';
import { Label } from '@lesson-ui/Label';
import { dedupeScheduleEntries, isNonClassPeriod, normalizeSubject } from '../utils/scheduleEntries';
import { findPlanSlotForEntry } from '../utils/planMatching';

type ViewMode = 'week' | 'day' | 'lesson';

const sortLessons = (entries: ScheduleEntry[]) => {
  return [...entries].sort((a, b) => {
    if (a.slot_number !== b.slot_number) {
      return a.slot_number - b.slot_number;
    }

    const startA = a.start_time || '';
    const startB = b.start_time || '';
    if (startA !== startB) {
      return startA.localeCompare(startB);
    }

    const endA = a.end_time || '';
    const endB = b.end_time || '';
    if (endA !== endB) {
      return endA.localeCompare(endB);
    }

    return (a.subject || '').localeCompare(b.subject || '');
  });
};

/** Get ISO week number (1-53) for a given date. */
function getISOWeekNumber(year: number, month: number, day: number): number {
  const d = new Date(year, month - 1, day);
  d.setDate(d.getDate() + 4 - (d.getDay() || 7));
  const startOfYear = new Date(d.getFullYear(), 0, 1);
  return Math.ceil((((d.getTime() - startOfYear.getTime()) / 86400000) + startOfYear.getDay() + 1) / 7);
}

/** Format week_of (e.g. "09-29-10-03") as "W12 03/16-03/20" for display when not provided by API. */
function formatWeekOfForDisplay(weekOf: string): string {
  if (!weekOf) return 'Unknown Week';
  const parts = weekOf.replace(/^week of\s+/i, '').trim().split(/[-/]/);
  if (parts.length >= 4) {
    const m1 = parseInt(parts[0], 10);
    const d1 = parseInt(parts[1], 10);
    const m2 = parseInt(parts[2], 10);
    const d2 = parseInt(parts[3], 10);
    const now = new Date();
    let year = now.getFullYear();
    if (now.getMonth() + 1 === 12 && m1 <= 2) year += 1;
    else if (now.getMonth() + 1 === 1 && m1 === 12) year -= 1;
    const w = getISOWeekNumber(year, m1, d1);
    const pad = (n: number) => String(n).padStart(2, '0');
    const start = `${pad(m1)}/${pad(d1)}`;
    const end = `${pad(m2)}/${pad(d2)}`;
    return `W${String(w).padStart(2, '0')} ${start}-${end}`;
  }
  return weekOf;
}

type WeekOption = { week_of: string; display: string; folder_name?: string };

function parseWeekOfStart(weekOf: string): { month: number; day: number } | null {
  const parts = weekOf.replace(/^week of\s+/i, '').trim().split(/[-/]/);
  if (parts.length >= 4) {
    const month = parseInt(parts[0], 10);
    const day = parseInt(parts[1], 10);
    if (!Number.isNaN(month) && !Number.isNaN(day)) return { month, day };
  }
  return null;
}

function getWeekCalendarSortKey(
  weekOf: string,
  folderName: string | undefined,
  plans: WeeklyPlan[]
): number {
  const parsed = parseWeekOfStart(weekOf);
  const month = parsed?.month ?? 1;
  const day = parsed?.day ?? 1;

  let year: number;
  const folderMatch = folderName?.match(/^(\d{2})\s*W\s*\d/i);
  if (folderMatch) {
    year = 2000 + parseInt(folderMatch[1], 10);
  } else {
    const canonical = normalizeWeekOfForMatch(weekOf);
    const plansForWeek = plans.filter(
      (p) => p.week_of && normalizeWeekOfForMatch(p.week_of) === canonical
    );
    const latestGenerated = plansForWeek
      .map((p) => (p.generated_at ? new Date(p.generated_at).getTime() : 0))
      .reduce((a, b) => Math.max(a, b), 0);
    if (latestGenerated > 0) {
      year = new Date(latestGenerated).getFullYear();
    } else {
      const now = new Date();
      const currMonth = now.getMonth() + 1;
      if (now.getMonth() + 1 === 12 && month <= 2) year = now.getFullYear() + 1;
      else if (currMonth === 1 && month === 12) year = now.getFullYear() - 1;
      else year = now.getFullYear();
    }
  }
  return year * 10000 + month * 100 + day;
}

/**
 * Build available weeks, then sort by calendar (year + week start) newest first.
 * Year from folder_name (YY W##), or from plan's generated_at, or inferred.
 * Selector shows first = most recent calendar week (e.g. 26 W12), last = oldest (e.g. 25 W36).
 */
function buildAvailableWeeksInApiOrder(
  weeks: Array<{ week_of: string; display: string; folder_name?: string }>,
  plans: WeeklyPlan[]
): Array<{ week_of: string; display: string }> {
  const seen = new Set<string>();
  const result: WeekOption[] = [];

  for (const w of weeks) {
    if (w.week_of && !seen.has(w.week_of)) {
      seen.add(w.week_of);
      result.push({ week_of: w.week_of, display: w.display, folder_name: w.folder_name });
    }
  }

  const planOnlyLatest = new Map<string, number>();
  for (const p of plans) {
    if (!p.week_of) continue;
    const canonical = normalizeWeekOfForMatch(p.week_of);
    if (seen.has(canonical)) continue;
    const at = p.generated_at ? new Date(p.generated_at).getTime() : 0;
    planOnlyLatest.set(canonical, Math.max(planOnlyLatest.get(canonical) ?? 0, at));
  }
  const planOnly = Array.from(planOnlyLatest.entries())
    .map(([week_of, latestAt]) => ({ week_of, latestAt }))
    .sort((a, b) => b.latestAt - a.latestAt);
  for (const { week_of } of planOnly) {
    seen.add(week_of);
    result.push({ week_of, display: formatWeekOfForDisplay(week_of) });
  }

  result.sort(
    (a, b) =>
      getWeekCalendarSortKey(b.week_of, b.folder_name, plans) -
      getWeekCalendarSortKey(a.week_of, a.folder_name, plans)
  );

  return result.map(({ week_of, display }) => ({ week_of, display }));
}


interface LessonPlanBrowserProps {
  onEnterLessonMode?: (scheduleEntry: ScheduleEntry, day?: string, slot?: number, planId?: string, previousViewMode?: 'week' | 'day' | 'lesson', weekOf?: string) => void;
  onExitLessonMode?: () => void; // Callback to exit lesson mode
  showLessonModeButton?: boolean; // Whether to highlight the Lesson Mode button (when in lesson mode)
  onViewPlan?: (scheduleEntry: ScheduleEntry) => void;
  initialLesson?: {
    scheduleEntry: ScheduleEntry;
    day: string;
    slot: number;
    planId?: string;
  } | null;
  initialDay?: string; // Day to show when opening browser (e.g., when exiting lesson mode)
}

type LessonSlotInfo = {
  planSlotIndex?: number;
  planSlotData?: any;
};

// @ts-expect-error - onViewPlan is part of the public API but not used in this component
export function LessonPlanBrowser({ onEnterLessonMode, onExitLessonMode, showLessonModeButton = false, onViewPlan, initialLesson, initialDay }: LessonPlanBrowserProps = {}) {
  const { currentUser, slots } = useStore();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [plans, setPlans] = useState<WeeklyPlan[]>([]);
  const [availableWeeks, setAvailableWeeks] = useState<Array<{ week_of: string; display: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // View state - initialize to 'lesson' if initialLesson is provided to prevent flash
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    // If initialLesson is provided, start with 'lesson' view to prevent flash
    return initialLesson ? 'lesson' : 'week';
  });
  const [selectedWeek, setSelectedWeek] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [selectedLesson, setSelectedLesson] = useState<{
    scheduleEntry: ScheduleEntry;
    day: string;
    slot: number;
    planSlotIndex?: number;
    planSlotData?: any;
    weekOf?: string; // Store the weekOf from when the lesson was clicked
  } | null>(null);
  const [currentDayLessons, setCurrentDayLessons] = useState<ScheduleEntry[]>([]);
  const [currentDayLessonSlots, setCurrentDayLessonSlots] = useState<Record<string, LessonSlotInfo>>({});
  const [cachedLessonPlanData, setCachedLessonPlanData] = useState<any>(null);
  const [cachedLessonPlanWeek, setCachedLessonPlanWeek] = useState<string | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [currentLesson, setCurrentLesson] = useState<ScheduleEntry | null>(null);

  // Use a ref to prevent race conditions with state updates
  const isNavigatingRef = useRef(false);
  const hasInitializedLesson = useRef(false);
  const currentLessonIntervalRef = useRef<number | null>(null);

  // Cache for plans to prevent redundant API calls
  const plansCacheRef = useRef<{
    data: WeeklyPlan[];
    timestamp: number;
    userId: string | null;
  }>({ data: [], timestamp: 0, userId: null });
  const fetchPlansInProgressRef = useRef(false);
  const CACHE_DURATION_MS = 30000; // 30 seconds cache

  // Auto-open initial lesson if provided
  useEffect(() => {
    // Reset initialization flag when initialLesson changes
    if (initialLesson) {
      hasInitializedLesson.current = false;
    }
  }, [initialLesson]);

  // Handle initialDay prop - open day view when exiting lesson mode
  // Use a ref to track if we've already processed this initialDay to prevent re-triggering
  const processedInitialDayRef = useRef<string | null>(null);

  useEffect(() => {
    if (initialDay && !loading && plans.length > 0) {
      // Only process if this is a new initialDay value
      if (processedInitialDayRef.current !== initialDay) {
        console.log('[LessonPlanBrowser] Opening day view for initialDay:', initialDay);
        // Normalize day to lowercase to match the expected format (e.g., "monday", "tuesday")
        const normalizedDay = initialDay.toLowerCase();
        console.log('[LessonPlanBrowser] Normalized day:', normalizedDay);
        setSelectedDay(normalizedDay);
        setViewMode('day');
        processedInitialDayRef.current = initialDay;
        console.log('[LessonPlanBrowser] Set viewMode to "day" and selectedDay to:', normalizedDay);
      }
    } else if (!initialDay) {
      // Reset the ref when initialDay is cleared
      processedInitialDayRef.current = null;
    }
  }, [initialDay, loading, plans.length]);

  useEffect(() => {
    if (initialLesson && !hasInitializedLesson.current && !loading && currentUser && plans.length > 0) {
      hasInitializedLesson.current = true;
      // Ensure view mode is set to 'lesson' before opening
      setViewMode('lesson');
      console.log('[LessonPlanBrowser] Auto-opening initial lesson:', initialLesson);

      // Find the plan for this lesson
      // First try to use the planId if provided (from lesson mode)
      let matchingPlan: WeeklyPlan | undefined;

      if (initialLesson.planId) {
        matchingPlan = plans.find(p => p.id === initialLesson.planId);
        console.log('[LessonPlanBrowser] Found plan by ID:', initialLesson.planId, 'plan:', matchingPlan?.id);
      }

      // If not found by ID, try to find by week
      if (!matchingPlan) {
        const scheduleWeek = initialLesson.scheduleEntry.week_of;
        if (scheduleWeek) {
          matchingPlan = plans.find(p => p.week_of === scheduleWeek);
          console.log('[LessonPlanBrowser] Found plan by week:', scheduleWeek, 'plan:', matchingPlan?.id);
        }
      }

      // Fallback to first plan
      if (!matchingPlan && plans.length > 0) {
        matchingPlan = plans[0];
        console.log('[LessonPlanBrowser] Using first plan as fallback:', matchingPlan.id);
      }

      const openLesson = async () => {
        // Check if we already have cached data for this week
        if (matchingPlan && matchingPlan.week_of === cachedLessonPlanWeek && cachedLessonPlanData) {
          console.log('[LessonPlanBrowser] Using cached plan data');
          // Use cached data - no API call needed
          const dayData = cachedLessonPlanData.days?.[initialLesson.day];
          let planSlotIndex: number | undefined;
          let planSlotData: any;

          if (dayData) {
            const slotInfo = findPlanSlotForEntry(dayData, initialLesson.scheduleEntry);
            if (slotInfo) {
              planSlotIndex = slotInfo.planSlotIndex;
              planSlotData = slotInfo.planSlotData;
            } else if (dayData.slots && Array.isArray(dayData.slots)) {
              const slotByNumber = dayData.slots.find((s: any) => s.slot_number === initialLesson.slot);
              if (slotByNumber) {
                planSlotData = slotByNumber;
                planSlotIndex = dayData.slots.indexOf(slotByNumber);
              }
            }
          }

          // Use handleLessonClick with cached data - it won't reload if data is cached
          await handleLessonClick(
            initialLesson.scheduleEntry,
            initialLesson.day,
            initialLesson.slot,
            planSlotIndex,
            planSlotData
          );
          return;
        }

        // Only load if we don't have cached data
        if (matchingPlan) {
          try {
            console.log('[LessonPlanBrowser] Loading plan detail for:', matchingPlan.id);
            const planDetailResponse = await lessonApi.getPlanDetail(matchingPlan.id, currentUser.id);

            if (planDetailResponse.data?.lesson_json) {
              const lessonJson = typeof planDetailResponse.data.lesson_json === 'string'
                ? JSON.parse(planDetailResponse.data.lesson_json)
                : planDetailResponse.data.lesson_json;

              // Enrich and cache the plan data
              const enrichedPlanData = enrichPlanDataWithSlots(lessonJson, slots);
              setCachedLessonPlanData(enrichedPlanData);
              setCachedLessonPlanWeek(matchingPlan.week_of);

              // Find the slot data
              const dayData = enrichedPlanData.days?.[initialLesson.day];
              let planSlotIndex: number | undefined;
              let planSlotData: any;

              if (dayData) {
                const slotInfo = findPlanSlotForEntry(dayData, initialLesson.scheduleEntry);
                if (slotInfo) {
                  planSlotIndex = slotInfo.planSlotIndex;
                  planSlotData = slotInfo.planSlotData;
                } else if (dayData.slots && Array.isArray(dayData.slots)) {
                  const slotByNumber = dayData.slots.find((s: any) => s.slot_number === initialLesson.slot);
                  if (slotByNumber) {
                    planSlotData = slotByNumber;
                    planSlotIndex = dayData.slots.indexOf(slotByNumber);
                  }
                }
              }

              // Now use handleLessonClick with the loaded data
              // handleLessonClick will check cache first, so this should be fast
              await handleLessonClick(
                initialLesson.scheduleEntry,
                initialLesson.day,
                initialLesson.slot,
                planSlotIndex,
                planSlotData
              );
              return;
            }
          } catch (err) {
            console.error('[LessonPlanBrowser] Error loading plan detail:', err);
          }
        }

        // Fallback: use handleLessonClick - it will handle loading if needed
        await handleLessonClick(
          initialLesson.scheduleEntry,
          initialLesson.day,
          initialLesson.slot
        );
      };

      if (matchingPlan && matchingPlan.week_of) {
        console.log('[LessonPlanBrowser] Setting selected week to:', matchingPlan.week_of);
        setSelectedWeek(matchingPlan.week_of);
        // Small delay to ensure state is updated, then open lesson
        setTimeout(() => {
          console.log('[LessonPlanBrowser] Opening lesson after week set');
          openLesson();
        }, 300);
      } else {
        // Try to find any plan that might match
        const anyPlan = plans.find(p => p.week_of);
        if (anyPlan && anyPlan.week_of) {
          console.log('[LessonPlanBrowser] Using fallback plan, week:', anyPlan.week_of);
          setSelectedWeek(anyPlan.week_of);
          setTimeout(() => {
            openLesson();
          }, 300);
        } else {
          console.warn('[LessonPlanBrowser] No plan found, opening lesson without plan data');
          // Just open the lesson directly
          openLesson();
        }
      }
    }
  }, [initialLesson, loading, currentUser, plans]);

  const fetchPlans = async (isRefresh = false) => {
    if (!currentUser) {
      setPlans([]);
      setAvailableWeeks([]);
      setLoading(false);
      return;
    }

    // Check cache first (unless it's a refresh)
    const now = Date.now();
    const cache = plansCacheRef.current;
    let cachedPlans: WeeklyPlan[] | null = null;
    let cachedWeeks: Array<{ week_of: string; display: string }> = [];
    let cacheValid = false;

    if (
      !isRefresh &&
      cache.userId === currentUser.id &&
      cache.data.length > 0 &&
      now - cache.timestamp < CACHE_DURATION_MS
    ) {
      cacheValid = true;
      cachedPlans = cache.data;
      console.log('[LessonPlanBrowser] Using cached plans');
      setPlans(cachedPlans);

      // Still fetch weeks as they might change
      try {
        const weeksResponse = await userApi
          .getRecentWeeks(currentUser.id, 25, currentUser.id)
          .catch(() => ({ data: [] }));
        cachedWeeks = weeksResponse.data || [];
        const cachedAvailableWeeks = buildAvailableWeeksInApiOrder(
          cachedWeeks,
          cachedPlans || []
        );
        setAvailableWeeks(cachedAvailableWeeks);
        if (!selectedWeek && cachedAvailableWeeks.length > 0) {
          setSelectedWeek(cachedAvailableWeeks[0]?.week_of ?? null);
        }
      } catch (error) {
        console.error('Failed to fetch weeks:', error);
      }

      const desiredWeek =
        selectedWeek ||
        cachedAvailableWeeks[0]?.week_of ||
        cachedPlans[0]?.week_of ||
        null;
      const cacheHasDesiredWeek = desiredWeek
        ? cachedPlans.some((p) => p.week_of === desiredWeek)
        : false;

      if (cacheHasDesiredWeek) {
        setLoading(false);
        return;
      }

      console.warn(
        '[LessonPlanBrowser] Cached plans missing desired week, fetching fresh data',
        {
          desiredWeek,
          cachedWeeks: cachedPlans.map((p) => p.week_of),
        }
      );
      // Fall through to fresh fetch
    }

    // Prevent concurrent calls
    if (fetchPlansInProgressRef.current) {
      console.log('[LessonPlanBrowser] Fetch already in progress, skipping');
      return;
    }

    fetchPlansInProgressRef.current = true;

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      // Fetch both plans and available weeks in parallel
      const [plansResponse, weeksResponse] = await Promise.all([
        planApi.list(currentUser.id, 100, currentUser.id),
        userApi.getRecentWeeks(currentUser.id, 25, currentUser.id).catch(() => ({ data: [] }))
      ]);

      console.log('*** DEBUG: EXECUTING LESSON PLAN BROWSER FILTER LOGIC ***');
      console.log('*** DEBUG: Current User ID:', currentUser.id);

      const rawPlans = plansResponse.data || [];
      // Robustly filter plans by current user ID to prevent data leakage from backend/local DB
      const plans = rawPlans.filter(p => p.user_id === currentUser.id);

      if (rawPlans.length !== plans.length) {
        console.warn(`[LessonPlanBrowser] Filtered out ${rawPlans.length - plans.length} plans belonging to other users`);
      }

      const weeks = weeksResponse.data || [];

      console.log('[LessonPlanBrowser] fetchPlans result:', {
        planCount: plans.length,
        weekCount: weeks.length,
        planWeekOfValues: plans.map(p => p.week_of),
        weekWeekOfValues: weeks.map(w => w.week_of),
        currentSelectedWeek: selectedWeek
      });

      // Update cache
      plansCacheRef.current = {
        data: plans,
        timestamp: Date.now(),
        userId: currentUser.id
      };

      setPlans(plans);

      const availableWeeksList = buildAvailableWeeksInApiOrder(weeks, plans);
      setAvailableWeeks(availableWeeksList);

      const weekValues = availableWeeksList.map((w) => w.week_of);
      if (!selectedWeek && weekValues.length > 0) {
        const autoSelectedWeek = weekValues[0];
        console.log('[LessonPlanBrowser] Auto-selecting week (most recent):', {
          availableWeeks: weekValues,
          selected: autoSelectedWeek
        });
        setSelectedWeek(autoSelectedWeek);
      } else if (selectedWeek && !weekValues.includes(selectedWeek) && weekValues.length > 0) {
        console.log('[LessonPlanBrowser] Selected week not available, switching to:', weekValues[0]);
        setSelectedWeek(weekValues[0]);
      } else {
        console.log('[LessonPlanBrowser] Keeping existing selectedWeek:', selectedWeek);
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      // If error is rate limit, use cached data if available
      if (error instanceof Error && error.message.includes('429')) {
        if (cache.userId === currentUser.id && cache.data.length > 0) {
          console.log('[LessonPlanBrowser] Rate limited, using cached plans');
          setPlans(cache.data);
        }
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      fetchPlansInProgressRef.current = false;
    }
  };

  useEffect(() => {
    // Clear cache when user changes
    if (plansCacheRef.current.userId !== currentUser?.id) {
      plansCacheRef.current = { data: [], timestamp: 0, userId: null };
    }
    fetchPlans();
  }, [currentUser]);

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Format time as HH:MM:SS
  const formatTime = (date: Date): string => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  // Format date as MM/DD/YY
  const formatDate = (date: Date): string => {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${month}/${day}/${year}`;
  };

  // Get day abbreviation (MON, TUE, WED, etc.)
  const getDayAbbreviation = (date: Date): string => {
    const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
    return days[date.getDay()];
  };

  // Fetch the current lesson periodically for highlighting / Today jump
  useEffect(() => {
    if (!currentUser) {
      setCurrentLesson(null);
      if (currentLessonIntervalRef.current) {
        window.clearInterval(currentLessonIntervalRef.current);
        currentLessonIntervalRef.current = null;
      }
      return;
    }

    let cancelled = false;

    const fetchCurrentLesson = async () => {
      try {
        const response = await scheduleApi.getCurrentLesson(currentUser.id);
        if (!cancelled) {
          setCurrentLesson(response.data);
        }
      } catch (error) {
        console.error('[LessonPlanBrowser] Failed to fetch current lesson:', error);
        if (!cancelled) {
          setCurrentLesson(null);
        }
      }
    };

    fetchCurrentLesson();
    const interval = window.setInterval(fetchCurrentLesson, 60000);
    currentLessonIntervalRef.current = interval;

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      currentLessonIntervalRef.current = null;
    };
  }, [currentUser]);

  const handleTodayClick = () => {
    // Prefer the backend-reported current lesson because it aligns with schedule entries
    if (currentLesson) {
      setSelectedWeek((prevWeek) => currentLesson.week_of || prevWeek);
      setSelectedDay(currentLesson.day_of_week);
      setViewMode('day');
      return;
    }

    const today = new Date();
    const weekdayIndex = today.getDay(); // 0 = Sunday, 1 = Monday
    const weekdayMap: Record<number, typeof selectedDay> = {
      0: null,
      1: 'monday',
      2: 'tuesday',
      3: 'wednesday',
      4: 'thursday',
      5: 'friday',
      6: null,
    };
    const inferredDay = weekdayMap[weekdayIndex];
    if (inferredDay) {
      setSelectedDay(inferredDay);
      setViewMode('day');
    } else {
      // Weekend: just show week view
      setViewMode('week');
    }
  };

  const handleWeekClick = () => {
    setViewMode('week');
    // Clear cached data when switching weeks to avoid stale data
    setCachedLessonPlanData(null);
    setCachedLessonPlanWeek(null);
    setSelectedLesson(null);
    // Don't clear selectedDay/selectedLesson - preserve context
  };

  const handleDayClick = (day: string) => {
    setViewMode('day');
    setSelectedDay(day);
    // Don't clear selectedLesson - keep it for navigation
  };

  const handleWeekDayClick = (day: string) => {
    handleDayClick(day);
  };

  const enrichPlanDataWithSlots = (planData: any, userSlots: ClassSlot[]) => {
    if (!planData || planData.__slots_enriched || !userSlots?.length) {
      return planData;
    }

    const slotByNumber = new Map<number, ClassSlot>();
    userSlots.forEach((slot) => {
      if (typeof slot.slot_number === 'number') {
        slotByNumber.set(slot.slot_number, slot);
      }
    });

    Object.values(planData.days || {}).forEach((dayData: any) => {
      if (!dayData?.slots) return;
      dayData.slots.forEach((slot: any) => {
        const canonical = slotByNumber.get(slot?.slot_number);
        if (!canonical) {
          return;
        }

        if (!slot.grade && canonical.grade) {
          slot.grade = canonical.grade;
        }
        if (!slot.homeroom && canonical.homeroom) {
          slot.homeroom = canonical.homeroom;
        }
      });
    });

    Object.defineProperty(planData, '__slots_enriched', {
      value: true,
      enumerable: false,
      configurable: true,
    });

    return planData;
  };

  const buildLessonSlotMap = (dayData: any, lessons: ScheduleEntry[]) => {
    if (!dayData?.slots || !Array.isArray(dayData.slots)) {
      return {};
    }

    return lessons.reduce<Record<string, LessonSlotInfo>>((acc, lesson) => {
      const match = findPlanSlotForEntry(dayData, lesson);
      if (match) {
        acc[lesson.id] = match;
      }
      return acc;
    }, {});
  };

  const getLessonPlanSlot = (lesson: ScheduleEntry, day: string): LessonSlotInfo | null => {
    const existing = currentDayLessonSlots[lesson.id];
    if (existing) {
      return existing;
    }

    // CRITICAL: Use week from selectedLesson if available, otherwise fall back to selectedWeek
    // This ensures we use the correct week even when navigating between lessons
    const weekToUse = selectedLesson?.weekOf || selectedLesson?.scheduleEntry?.week_of || selectedWeek;

    if (cachedLessonPlanData && cachedLessonPlanWeek === weekToUse) {
      const dayData = cachedLessonPlanData.days?.[day];
      const match = findPlanSlotForEntry(dayData, lesson);
      if (match) {
        setCurrentDayLessonSlots((prev) => ({
          ...prev,
          [lesson.id]: match,
        }));
        return match;
      }
    }

    return null;
  };

  const handleLessonClick = async (
    scheduleEntry: ScheduleEntry,
    day: string,
    slot: number,
    planSlotIndex?: number,
    planSlotData?: any,
    weekOfFromView?: string // weekOf from the view (WeekView/DayView) that triggered the click
  ) => {
    // Prevent opening lesson plans for non-class periods
    const subject = scheduleEntry.subject || '';
    const isNonClass = isNonClassPeriod(subject);
    console.log('[handleLessonClick] Entry check:', {
      subject: subject,
      subjectType: typeof subject,
      isNonClassPeriod: isNonClass,
      entryId: scheduleEntry.id,
      day: day,
      slot: slot,
      entryWeekOf: scheduleEntry.week_of,
      selectedWeek: selectedWeek
    });

    if (isNonClass) {
      console.log('[handleLessonClick] Ignoring click on non-class period:', subject);
      return;
    }

    // CRITICAL FIX: Determine the correct weekOf for this lesson
    // Priority: weekOfFromView (from WeekView/DayView) > scheduleEntry.week_of > selectedWeek
    // weekOfFromView is the most reliable because it comes directly from the view displaying the lesson
    const lessonWeekOf = weekOfFromView || scheduleEntry.week_of || selectedWeek;

    console.log('[handleLessonClick] Week resolution:', {
      weekOfFromView: weekOfFromView,
      scheduleEntry_week_of: scheduleEntry.week_of,
      selectedWeek: selectedWeek,
      using_weekOf: lessonWeekOf,
      day: day,
      priority: weekOfFromView ? 'weekOfFromView (highest)' : scheduleEntry.week_of ? 'scheduleEntry.week_of' : 'selectedWeek (fallback)',
    });

    // Update selectedWeek if scheduleEntry has a different week_of
    if (scheduleEntry.week_of && scheduleEntry.week_of !== selectedWeek) {
      console.log('[handleLessonClick] Updating selectedWeek from', selectedWeek, 'to', scheduleEntry.week_of);
      setSelectedWeek(scheduleEntry.week_of);
      // Clear cached data since we're switching weeks
      setCachedLessonPlanData(null);
      setCachedLessonPlanWeek(null);
    }

    // Also update selectedWeek if weekOfFromView is different (most reliable source)
    if (weekOfFromView && weekOfFromView !== selectedWeek) {
      console.log('[handleLessonClick] Updating selectedWeek from', selectedWeek, 'to weekOfFromView:', weekOfFromView);
      setSelectedWeek(weekOfFromView);
      // Clear cached data since we're switching weeks
      setCachedLessonPlanData(null);
      setCachedLessonPlanWeek(null);
    }

    setViewMode('lesson');
    // CRITICAL: Use the plan slot number (from plan matching) to find content
    // The schedule entry's slot_number might not match the plan slot number
    // The plan slot number is the authoritative source for which content to display
    // Priority: planSlotData.slot_number > slot (from plan matching) > scheduleEntry.slot_number
    const displaySlot = planSlotData?.slot_number ?? slot ?? scheduleEntry.slot_number;
    console.log('[handleLessonClick] Slot resolution:', {
      scheduleEntry_slot: scheduleEntry.slot_number,
      param_slot: slot,
      planSlotData_slot: planSlotData?.slot_number,
      planSlotIndex,
      using_display_slot: displaySlot,
      lessonWeekOf: lessonWeekOf,
      note: 'Using plan slot number (from plan matching) for content display',
    });
    const lessonToStore = {
      scheduleEntry,
      day,
      slot: displaySlot,
      planSlotIndex,
      planSlotData,
      weekOf: lessonWeekOf || undefined, // Store the weekOf for this lesson
    };

    console.log('[handleLessonClick] Storing lesson in selectedLesson:', {
      subject: scheduleEntry.subject,
      day: day,
      slot: displaySlot,
      weekOf: lessonWeekOf,
      note: 'This weekOf will be used by LessonDetailView'
    });

    setSelectedLesson(lessonToStore);

    // Fetch all lessons for this day to enable navigation
    try {
      const response = await scheduleApi.getSchedule(currentUser!.id, day);
      const activeLessons = response.filter((e) => e.is_active && !isNonClassPeriod(e.subject));
      const dedupedLessons = dedupeScheduleEntries(activeLessons);
      const sortedLessons = sortLessons(dedupedLessons);
      setCurrentDayLessons(sortedLessons);
      const initialSlotMap: Record<string, LessonSlotInfo> = {};

      if (planSlotIndex !== undefined || planSlotData) {
        initialSlotMap[scheduleEntry.id] = {
          planSlotIndex,
          planSlotData,
        };
      }

      const canonicalEntry =
        sortedLessons.find((entry) => entry.id === scheduleEntry.id) ??
        sortedLessons.find(
          (entry) =>
            entry.slot_number === scheduleEntry.slot_number &&
            entry.start_time === scheduleEntry.start_time &&
            entry.end_time === scheduleEntry.end_time &&
            normalizeSubject(entry.subject) === normalizeSubject(scheduleEntry.subject) &&
            (entry.grade || '') === (scheduleEntry.grade || '') &&
            (entry.homeroom || '') === (scheduleEntry.homeroom || '')
        );

      if (canonicalEntry && canonicalEntry.id !== scheduleEntry.id) {
        if (initialSlotMap[scheduleEntry.id]) {
          initialSlotMap[canonicalEntry.id] = initialSlotMap[scheduleEntry.id];
          delete initialSlotMap[scheduleEntry.id];
        }

        setSelectedLesson((prev) =>
          prev
            ? {
              ...prev,
              scheduleEntry: canonicalEntry,
            }
            : prev
        );
      }

      setCurrentDayLessonSlots(initialSlotMap);

      if (!selectedWeek) {
        setCachedLessonPlanData(null);
        setCachedLessonPlanWeek(null);
        return;
      }

      // Check cache first to avoid duplicate API calls
      // CRITICAL: Use lessonWeekOf (the correct week for this lesson) not selectedWeek (which might be stale)
      let planData =
        cachedLessonPlanWeek === lessonWeekOf ? cachedLessonPlanData : null;

      console.log('[handleLessonClick] Cache check:', {
        cachedLessonPlanWeek: cachedLessonPlanWeek,
        selectedWeek: selectedWeek,
        lessonWeekOf: lessonWeekOf,
        usingCachedData: planData !== null,
        note: 'Using lessonWeekOf for cache check, not selectedWeek'
      });

      planData = enrichPlanDataWithSlots(planData, slots);

      // Skip API call if we already have planSlotData (caller already loaded it)
      // or if we have cached data
      if (!planData && !planSlotData) {
        let availablePlans = plans;

        // CRITICAL: Use lessonWeekOf (the correct week for this lesson) not selectedWeek
        const canonicalLessonWeek = normalizeWeekOfForMatch(lessonWeekOf);
        const planMatchesWeek = (p: WeeklyPlan) => p.week_of === lessonWeekOf || (!!canonicalLessonWeek && normalizeWeekOfForMatch(p.week_of) === canonicalLessonWeek);
        if (!availablePlans.some(planMatchesWeek)) {
          console.log('[handleLessonClick] Plan not in availablePlans, checking cache/refetching:', {
            lessonWeekOf: lessonWeekOf,
            availableWeekOfValues: availablePlans.map(p => p.week_of)
          });
          // Check cache first before making API call
          const cache = plansCacheRef.current;
          if (cache.userId === currentUser!.id && cache.data.length > 0) {
            availablePlans = cache.data;
            setPlans(availablePlans);
          } else {
            const plansResponse = await planApi.list(currentUser!.id, 100, currentUser!.id);
            availablePlans = plansResponse.data || [];
            // Update cache
            plansCacheRef.current = {
              data: availablePlans,
              timestamp: Date.now(),
              userId: currentUser!.id
            };
            setPlans(availablePlans);
          }
        }

        // CRITICAL: Use lessonWeekOf (the correct week for this lesson) not selectedWeek; canonical match so 3/2-03/06 matches 03/02-03/06
        const completedPlans = availablePlans
          .filter((p) => planMatchesWeek(p) && p.status === 'completed')
          .sort(
            (a, b) =>
              new Date(b.generated_at ?? 0).getTime() - new Date(a.generated_at ?? 0).getTime()
          );

        const fallbackPlans = availablePlans
          .filter(planMatchesWeek)
          .sort(
            (a, b) =>
              new Date(b.generated_at ?? 0).getTime() - new Date(a.generated_at ?? 0).getTime()
          );

        const plan = completedPlans[0] ?? fallbackPlans[0];

        console.log('[handleLessonClick] Plan selection:', {
          lessonWeekOf: lessonWeekOf,
          selectedWeek: selectedWeek,
          completedPlansCount: completedPlans.length,
          fallbackPlansCount: fallbackPlans.length,
          selectedPlanId: plan?.id,
          selectedPlanWeekOf: plan?.week_of,
          note: 'Using lessonWeekOf to find plan, not selectedWeek'
        });

        if (!plan) {
          console.error('[handleLessonClick] No plan found for selected week. Aborting lesson click.', {
            desiredWeek: lessonWeekOf,
            availableWeekOfValues: availablePlans.map((p) => p.week_of),
          });
          alert(
            `No lesson plan was found for week ${lessonWeekOf}. Please generate the lesson plan for this week before selecting a lesson.`
          );
          setIsNavigating(false);
          isNavigatingRef.current = false;
          setLoading(false);
          return;
        }

        if (plan) {
          const planDetailResponse = await lessonApi.getPlanDetail(plan.id, currentUser!.id);
          if (planDetailResponse.data?.lesson_json) {
            const enrichedPlanData = enrichPlanDataWithSlots(
              planDetailResponse.data.lesson_json,
              slots
            );
            // CRITICAL: Cache with lessonWeekOf, not selectedWeek
            setCachedLessonPlanData(enrichedPlanData);
            setCachedLessonPlanWeek(lessonWeekOf);
            console.log('[handleLessonClick] Caching plan data for week:', lessonWeekOf);
            planData = enrichedPlanData;
          } else {
            setCachedLessonPlanData(null);
            setCachedLessonPlanWeek(null);
          }
        } else {
          setCachedLessonPlanData(null);
          setCachedLessonPlanWeek(null);
        }
      } else if (planData) {
        // We have cached data, no need to reload
        console.log('[handleLessonClick] Using cached plan data for week:', lessonWeekOf);
      } else if (planSlotData) {
        // Caller already provided slot data, skip reload to avoid rate limiting
        console.log('[handleLessonClick] Using provided planSlotData, skipping API call');
      }

      if (planData) {
        const dayData = planData.days?.[day];
        if (dayData) {
          const lessonSlotMap = buildLessonSlotMap(dayData, sortedLessons);
          if (Object.keys(lessonSlotMap).length > 0) {
            setCurrentDayLessonSlots((prev) => ({
              ...prev,
              ...lessonSlotMap,
            }));

            setSelectedLesson((prev) => {
              if (!prev) return prev;
              const info = lessonSlotMap[prev.scheduleEntry.id];
              if (!info) return prev;
              return {
                ...prev,
                slot: info.planSlotData?.slot_number ?? prev.slot,
                planSlotIndex: info.planSlotIndex ?? prev.planSlotIndex,
                planSlotData: info.planSlotData ?? prev.planSlotData,
              };
            });
          }
        }
      }
    } catch (error) {
      console.warn('Failed to fetch day lessons for navigation:', error);
      setCurrentDayLessons([]);
      setCachedLessonPlanData(null);
      setCachedLessonPlanWeek(null);
    }

    // Ensure day is set when clicking lesson from week view
    if (!selectedDay) {
      setSelectedDay(day);
    }
  };

  const handleBack = () => {
    if (viewMode === 'lesson') {
      if (selectedDay) {
        setViewMode('day');
        // Keep selectedLesson for quick navigation back
      } else {
        setViewMode('week');
        setSelectedLesson(null);
      }
    } else if (viewMode === 'day') {
      setViewMode('week');
      // Don't clear selectedDay or selectedLesson - preserve context
    }
  };

  const handlePreviousLesson = async () => {
    if (!selectedLesson || currentDayLessons.length === 0 || isNavigating) return;

    setIsNavigating(true);

    const currentIndex = currentDayLessons.findIndex(
      lesson => lesson.id === selectedLesson.scheduleEntry.id
    );

    if (currentIndex > 0) {
      const prevLesson = currentDayLessons[currentIndex - 1];
      const planSlotInfo = getLessonPlanSlot(prevLesson, selectedLesson.day);

      if (planSlotInfo) {
        setSelectedLesson({
          scheduleEntry: prevLesson,
          day: selectedLesson.day,
          slot: planSlotInfo.planSlotData?.slot_number ?? prevLesson.slot_number,
          planSlotIndex: planSlotInfo.planSlotIndex,
          planSlotData: planSlotInfo.planSlotData,
        });
        setIsNavigating(false);
        return;
      }

      try {
        await handleLessonClick(prevLesson, selectedLesson.day, prevLesson.slot_number);
      } finally {
        setIsNavigating(false);
      }
    } else {
      setIsNavigating(false);
    }
  };

  const handleNextLesson = async () => {
    console.log(`[handleNextLesson] Called. isNavigatingRef: ${isNavigatingRef.current}`);

    // Use ref for synchronous check
    if (!selectedLesson || currentDayLessons.length === 0 || isNavigatingRef.current) {
      console.log(`[handleNextLesson] Blocked - isNavigatingRef: ${isNavigatingRef.current}, selectedLesson: ${!!selectedLesson}, currentDayLessons: ${currentDayLessons.length}`);
      return;
    }

    console.log(`[handleNextLesson] Starting navigation...`);
    isNavigatingRef.current = true;
    setIsNavigating(true);

    const currentIndex = currentDayLessons.findIndex(
      lesson => lesson.id === selectedLesson.scheduleEntry.id
    );

    if (currentIndex < currentDayLessons.length - 1) {
      const nextLesson = currentDayLessons[currentIndex + 1];

      console.log(`[handleNextLesson] Moving to next lesson. Current index: ${currentIndex}, day: ${selectedLesson.day}`);
      console.log(`[handleNextLesson] Has cached data: ${!!cachedLessonPlanData}`);
      console.log(`[handleNextLesson] Has planSlotData: ${!!selectedLesson.planSlotData}`);
      const planSlotInfo = getLessonPlanSlot(nextLesson, selectedLesson.day);

      if (planSlotInfo) {
        setSelectedLesson({
          scheduleEntry: nextLesson,
          day: selectedLesson.day,
          slot: planSlotInfo.planSlotData?.slot_number ?? nextLesson.slot_number,
          planSlotIndex: planSlotInfo.planSlotIndex,
          planSlotData: planSlotInfo.planSlotData,
        });
        isNavigatingRef.current = false;
        setIsNavigating(false);
        return;
      }

      console.log(`[handleNextLesson] No cached data available, calling handleLessonClick`);
      try {
        await handleLessonClick(nextLesson, selectedLesson.day, nextLesson.slot_number);
      } finally {
        isNavigatingRef.current = false;
        setIsNavigating(false);
      }
    } else {
      isNavigatingRef.current = false;
      setIsNavigating(false);
    }
  };

  const handleDaySwitch = (day: string) => {
    setSelectedDay(day);
    // Don't clear selectedLesson - keep it for navigation
    // Stay in day view
  };

  // Helper function to find a lesson for Lesson Mode
  const findLessonForLessonMode = async (): Promise<{
    scheduleEntry: ScheduleEntry;
    day: string;
    slot: number;
    planId?: string;
  } | null> => {
    if (!currentUser) return null;

    // Priority 1: Use selectedLesson if available
    if (selectedLesson) {
      const matchingPlan = plans.find(p => p.week_of === selectedLesson!.scheduleEntry.week_of);
      return {
        scheduleEntry: selectedLesson.scheduleEntry,
        day: selectedLesson.day,
        slot: selectedLesson.slot,
        planId: matchingPlan?.id,
      };
    }

    // Priority 2: Use currentLesson
    if (currentLesson) {
      const matchingPlan = plans.find(p => p.week_of === currentLesson!.week_of);
      return {
        scheduleEntry: currentLesson,
        day: currentLesson.day_of_week || 'monday',
        slot: currentLesson.slot_number || 1,
        planId: matchingPlan?.id,
      };
    }

    // Priority 3: Find next lesson from schedule
    try {
      const allScheduleEntries = await scheduleApi.getSchedule(currentUser.id);
      if (!allScheduleEntries || allScheduleEntries.length === 0) {
        return null;
      }

      const classLessons = allScheduleEntries.filter(entry =>
        entry.subject && !isNonClassPeriod(entry.subject)
      );

      if (classLessons.length === 0) {
        return null;
      }

      // Get current date and time
      const now = new Date();
      const currentDayOfWeek = now.getDay();
      const currentTime = now.getHours() * 60 + now.getMinutes();
      const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      const currentDayName = dayNames[currentDayOfWeek];

      // Find next lesson
      let nextLesson: ScheduleEntry | null = null;
      const parseTime = (timeStr: string | null | undefined): number => {
        if (!timeStr) return 0;
        const parts = timeStr.split(':');
        if (parts.length < 2) return 0;
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
      };

      // Check today's lessons
      if (currentDayOfWeek >= 1 && currentDayOfWeek <= 5) {
        const todayLessons = classLessons.filter(entry =>
          entry.day_of_week?.toLowerCase() === currentDayName
        );

        for (const lesson of todayLessons) {
          const startTime = parseTime(lesson.start_time);
          if (startTime > currentTime) {
            if (!nextLesson || parseTime(lesson.start_time) < parseTime(nextLesson.start_time)) {
              nextLesson = lesson;
            }
          }
        }
      }

      // If no lesson found today, find first lesson of the week
      if (!nextLesson && classLessons.length > 0) {
        const weekDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
        for (const dayName of weekDays) {
          const dayLessons = classLessons.filter(entry =>
            entry.day_of_week?.toLowerCase() === dayName
          );
          if (dayLessons.length > 0) {
            dayLessons.sort((a, b) => {
              if (a.slot_number !== b.slot_number) {
                return a.slot_number - b.slot_number;
              }
              const timeA = parseTime(a.start_time);
              const timeB = parseTime(b.start_time);
              return timeA - timeB;
            });
            nextLesson = dayLessons[0];
            break;
          }
        }
      }

      if (!nextLesson) {
        return null;
      }

      const matchingPlan = plans.find(p => p.week_of === nextLesson!.week_of);
      return {
        scheduleEntry: nextLesson,
        day: nextLesson.day_of_week || 'monday',
        slot: nextLesson.slot_number || 1,
        planId: matchingPlan?.id,
      };
    } catch (error) {
      console.error('[LessonPlanBrowser] Failed to find lesson for Lesson Mode:', error);
      return null;
    }
  };

  // Handle Lesson button click - find and open current/next lesson
  const handleLessonButtonClick = async () => {
    if (!currentUser) return;

    try {
      // First, try to use currentLesson if available
      if (currentLesson) {
        console.log('[LessonPlanBrowser] Using current lesson:', currentLesson);
        try {
          await handleLessonClick(
            currentLesson,
            currentLesson.day_of_week || 'monday',
            currentLesson.slot_number || 1
          );
          return;
        } catch (error: any) {
          // If current lesson fails (e.g., no phase_plan), try to find next lesson
          console.warn('[LessonPlanBrowser] Current lesson failed, finding next lesson:', error);
          // Continue to find next lesson below
        }
      }

      // If no current lesson, fetch schedule and find next lesson
      console.log('[LessonPlanBrowser] No current lesson, finding next lesson...');
      const allScheduleEntries = await scheduleApi.getSchedule(currentUser.id);

      if (!allScheduleEntries || allScheduleEntries.length === 0) {
        console.log('[LessonPlanBrowser] No schedule entries found, using fallback');
        // Fallback: find previous Monday's first lesson
        await findFallbackLesson();
        return;
      }

      // Filter out non-class periods
      const classLessons = allScheduleEntries.filter(entry =>
        entry.subject && !isNonClassPeriod(entry.subject)
      );

      if (classLessons.length === 0) {
        console.log('[LessonPlanBrowser] No class lessons found, using fallback');
        await findFallbackLesson();
        return;
      }

      // Get current date and time
      const now = new Date();
      const currentDayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
      const currentTime = now.getHours() * 60 + now.getMinutes(); // minutes since midnight

      // Map day names
      const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      const currentDayName = dayNames[currentDayOfWeek];

      // Helper to parse time string (e.g., "09:00") to minutes
      const parseTime = (timeStr: string | null | undefined): number => {
        if (!timeStr) return 0;
        const parts = timeStr.split(':');
        if (parts.length < 2) return 0;
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
      };

      // Find next lesson
      let nextLesson: ScheduleEntry | null = null;

      // First, check if there's a lesson today after current time
      if (currentDayOfWeek >= 1 && currentDayOfWeek <= 5) { // Monday-Friday
        const todayLessons = classLessons.filter(entry =>
          entry.day_of_week?.toLowerCase() === currentDayName
        );

        for (const lesson of todayLessons) {
          const startTime = parseTime(lesson.start_time);
          if (startTime > currentTime) {
            if (!nextLesson || parseTime(lesson.start_time) < parseTime(nextLesson.start_time)) {
              nextLesson = lesson;
            }
          }
        }
      }

      // If no lesson found today, find next lesson in the week
      if (!nextLesson) {
        const weekDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
        let startDayIndex = currentDayOfWeek >= 1 && currentDayOfWeek <= 5
          ? currentDayOfWeek - 1
          : 0; // Start from Monday if weekend

        // Search from today (or Monday if weekend) through Friday
        for (let i = 0; i < 5; i++) {
          const dayIndex = (startDayIndex + i) % 5;
          const dayName = weekDays[dayIndex];
          const dayLessons = classLessons.filter(entry =>
            entry.day_of_week?.toLowerCase() === dayName
          );

          if (dayLessons.length > 0) {
            // Sort by slot_number and start_time
            dayLessons.sort((a, b) => {
              if (a.slot_number !== b.slot_number) {
                return a.slot_number - b.slot_number;
              }
              const timeA = parseTime(a.start_time);
              const timeB = parseTime(b.start_time);
              return timeA - timeB;
            });

            // If it's today and we're looking at today, skip lessons that already passed
            if (dayIndex === startDayIndex && currentDayOfWeek >= 1 && currentDayOfWeek <= 5) {
              const futureLessons = dayLessons.filter(lesson =>
                parseTime(lesson.start_time) > currentTime
              );
              if (futureLessons.length > 0) {
                nextLesson = futureLessons[0];
                break;
              }
            } else {
              // For future days or if it's weekend, take the first lesson
              nextLesson = dayLessons[0];
              break;
            }
          }
        }
      }

      // If still no lesson found, use fallback
      if (!nextLesson) {
        console.log('[LessonPlanBrowser] No next lesson found, using fallback');
        await findFallbackLesson();
        return;
      }

      console.log('[LessonPlanBrowser] Found next lesson:', nextLesson);

      // Try to open the lesson, but handle errors gracefully
      try {
        await handleLessonClick(
          nextLesson,
          nextLesson.day_of_week || 'monday',
          nextLesson.slot_number || 1
        );
      } catch (error: any) {
        // If this lesson fails (e.g., no phase_plan), try to find another lesson
        console.warn('[LessonPlanBrowser] Lesson failed to open, trying next available:', error);

        // Remove this lesson from consideration and try again
        const remainingLessons = classLessons.filter(l => l.id !== nextLesson.id);
        if (remainingLessons.length > 0) {
          // Try the next lesson in the list
          const sortedRemaining = remainingLessons.sort((a, b) => {
            const dayOrder = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
            const dayA = dayOrder.indexOf(a.day_of_week?.toLowerCase() || '');
            const dayB = dayOrder.indexOf(b.day_of_week?.toLowerCase() || '');
            if (dayA !== dayB) return dayA - dayB;
            return (a.slot_number || 0) - (b.slot_number || 0);
          });

          try {
            const alternativeLesson = sortedRemaining[0];
            console.log('[LessonPlanBrowser] Trying alternative lesson:', alternativeLesson);
            await handleLessonClick(
              alternativeLesson,
              alternativeLesson.day_of_week || 'monday',
              alternativeLesson.slot_number || 1
            );
          } catch (altError) {
            console.error('[LessonPlanBrowser] Alternative lesson also failed:', altError);
            // Fallback to Monday's first lesson
            await findFallbackLesson();
          }
        } else {
          // No more lessons to try, use fallback
          await findFallbackLesson();
        }
      }
    } catch (error) {
      console.error('[LessonPlanBrowser] Error finding lesson:', error);
      // Fallback on error
      await findFallbackLesson();
    }
  };

  // Fallback: find previous week's first lesson from lesson plan database
  const findFallbackLesson = async () => {
    if (!currentUser) return;

    try {
      // Get current week
      const now = new Date();
      const currentWeekOf = getWeekOfDate(now);

      console.log('[LessonPlanBrowser] Finding fallback lesson from previous week in lesson plan database');

      // Get all available plans from the database
      let availablePlans = plans;
      if (availablePlans.length === 0) {
        // Fetch plans if not already loaded
        const plansResponse = await planApi.list(currentUser.id, 100, currentUser.id);
        availablePlans = plansResponse.data || [];
        setPlans(availablePlans);
      }

      if (availablePlans.length === 0) {
        console.log('[LessonPlanBrowser] No lesson plans found in database');
        return;
      }

      // Find the most recent previous week (before current week)
      // Sort plans by week_of date (most recent first)
      const sortedPlans = availablePlans
        .filter(p => p.week_of && p.week_of < currentWeekOf)
        .sort((a, b) => {
          // Compare dates (YYYY-MM-DD format sorts correctly as strings)
          return b.week_of!.localeCompare(a.week_of!);
        });

      if (sortedPlans.length === 0) {
        console.log('[LessonPlanBrowser] No previous week plans found, trying any available plan');
        // If no previous week, use the most recent plan available
        const allSortedPlans = availablePlans
          .filter(p => p.week_of)
          .sort((a, b) => b.week_of!.localeCompare(a.week_of!));

        if (allSortedPlans.length === 0) {
          console.log('[LessonPlanBrowser] No plans available at all');
          return;
        }
        sortedPlans.push(allSortedPlans[0]);
      }

      const previousWeekPlan = sortedPlans[0];
      const previousWeekOf = previousWeekPlan.week_of!;

      console.log('[LessonPlanBrowser] Found previous week plan:', {
        week: previousWeekOf,
        planId: previousWeekPlan.id
      });

      // Fetch schedule entries for that week
      const allScheduleEntries = await scheduleApi.getSchedule(currentUser.id);
      if (!allScheduleEntries || allScheduleEntries.length === 0) {
        console.log('[LessonPlanBrowser] No schedule entries found');
        return;
      }

      // Load the lesson plan detail to check which lessons have phase_plans
      let planDetailResponse = await lessonApi.getPlanDetail(previousWeekPlan.id, currentUser.id);
      let planData = planDetailResponse.data?.lesson_json;

      if (!planData) {
        console.log('[LessonPlanBrowser] Could not load plan detail for previous week');
        return;
      }

      // Filter lessons from the previous week that have lesson plans
      const previousWeekLessons = allScheduleEntries.filter(entry =>
        entry.week_of === previousWeekOf &&
        entry.subject &&
        !isNonClassPeriod(entry.subject)
      );

      if (previousWeekLessons.length === 0) {
        console.log('[LessonPlanBrowser] No lessons found for previous week:', previousWeekOf);
        return;
      }

      // Helper to check if a lesson has a phase_plan (using the provided plan data)
      const hasPhasePlan = (entry: ScheduleEntry, day: string, slot: number, planDataToCheck: any): boolean => {
        try {
          const dayKey = day.toLowerCase();
          const dayData = planDataToCheck.days?.[dayKey];

          if (!dayData) {
            console.log('[LessonPlanBrowser] No day data for:', dayKey, 'Available days:', Object.keys(planDataToCheck.days || {}));
            return false;
          }

          if (!dayData.slots || !Array.isArray(dayData.slots)) {
            console.log('[LessonPlanBrowser] No slots array for day:', dayKey);
            return false;
          }

          const slotData = dayData.slots.find((s: any) => s.slot_number === slot);
          if (!slotData) {
            console.log('[LessonPlanBrowser] No slot data for:', { day: dayKey, slot, availableSlots: dayData.slots.map((s: any) => s.slot_number) });
            return false;
          }

          // Check for phase_plan in the nested structure
          const tailoredInstruction = slotData.tailored_instruction;
          if (!tailoredInstruction) {
            console.log('[LessonPlanBrowser] No tailored_instruction for:', { day: dayKey, slot });
            return false;
          }

          const coTeachingModel = tailoredInstruction.co_teaching_model;
          if (!coTeachingModel) {
            console.log('[LessonPlanBrowser] No co_teaching_model for:', { day: dayKey, slot });
            return false;
          }

          const phasePlan = coTeachingModel.phase_plan;
          const hasPlan = Array.isArray(phasePlan) && phasePlan.length > 0;

          console.log('[LessonPlanBrowser] Phase plan check result:', {
            day: dayKey,
            slot,
            hasPlan,
            phasePlanType: typeof phasePlan,
            phasePlanLength: Array.isArray(phasePlan) ? phasePlan.length : 'not array',
            phasePlanValue: phasePlan
          });

          return hasPlan;
        } catch (error) {
          console.error('[LessonPlanBrowser] Error checking phase_plan:', error, { day, slot });
          return false;
        }
      };

      // Find Monday's first lesson (slot 1, or earliest available) that has a phase_plan
      const mondayLessons = previousWeekLessons.filter(entry =>
        entry.day_of_week?.toLowerCase() === 'monday'
      );

      // Sort lessons by day and slot
      const sortedLessons = mondayLessons.length > 0
        ? mondayLessons.sort((a, b) => a.slot_number - b.slot_number)
        : previousWeekLessons.sort((a, b) => {
          // Sort by day, then by slot
          const dayOrder = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
          const dayA = dayOrder.indexOf(a.day_of_week?.toLowerCase() || '');
          const dayB = dayOrder.indexOf(b.day_of_week?.toLowerCase() || '');
          if (dayA !== dayB) return dayA - dayB;
          return a.slot_number - b.slot_number;
        });

      // Find the first lesson that has a phase_plan
      // Try all lessons in order until we find one with phase_plan
      let fallbackLesson: ScheduleEntry | null = null;
      let finalPlanData = planData;
      let finalWeekOf = previousWeekOf;
      let finalPlan = previousWeekPlan;

      for (const lesson of sortedLessons) {
        const day = lesson.day_of_week?.toLowerCase() || 'monday';
        const slot = lesson.slot_number || 1;

        if (hasPhasePlan(lesson, day, slot, planData)) {
          console.log('[LessonPlanBrowser] Found lesson with phase_plan:', { day, slot });
          fallbackLesson = lesson;
          break;
        }
      }

      // If no lesson with phase_plan found in first previous week, try earlier weeks
      if (!fallbackLesson) {
        console.log('[LessonPlanBrowser] No lessons with phase_plan found in first previous week, trying earlier weeks...');

        // Try all previous weeks until we find one with a lesson that has phase_plan
        for (let i = 1; i < sortedPlans.length && i < 5; i++) { // Limit to 5 weeks back
          const earlierWeekPlan = sortedPlans[i];
          const earlierWeekOf = earlierWeekPlan.week_of!;

          console.log('[LessonPlanBrowser] Trying earlier week:', earlierWeekOf);

          // Load plan detail for earlier week
          const earlierPlanDetailResponse = await lessonApi.getPlanDetail(earlierWeekPlan.id, currentUser.id);
          const earlierPlanData = earlierPlanDetailResponse.data?.lesson_json;

          if (!earlierPlanData) {
            continue;
          }

          // Find lessons from earlier week
          const earlierWeekLessons = allScheduleEntries.filter(entry =>
            entry.week_of === earlierWeekOf &&
            entry.subject &&
            !isNonClassPeriod(entry.subject)
          );

          if (earlierWeekLessons.length === 0) {
            continue;
          }

          // Sort and find first with phase_plan
          const sortedEarlierLessons = earlierWeekLessons.sort((a, b) => {
            const dayOrder = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
            const dayA = dayOrder.indexOf(a.day_of_week?.toLowerCase() || '');
            const dayB = dayOrder.indexOf(b.day_of_week?.toLowerCase() || '');
            if (dayA !== dayB) return dayA - dayB;
            return a.slot_number - b.slot_number;
          });

          for (const lesson of sortedEarlierLessons) {
            const day = lesson.day_of_week?.toLowerCase() || 'monday';
            const slot = lesson.slot_number || 1;

            if (hasPhasePlan(lesson, day, slot, earlierPlanData)) {
              console.log('[LessonPlanBrowser] Found lesson with phase_plan in earlier week:', {
                week: earlierWeekOf,
                day,
                slot
              });
              fallbackLesson = lesson;
              finalPlanData = earlierPlanData;
              finalWeekOf = earlierWeekOf;
              finalPlan = earlierWeekPlan;
              break;
            }
          }

          if (fallbackLesson) {
            break; // Found a lesson, stop searching
          }
        }

        // If still no lesson found, use first available as last resort
        if (!fallbackLesson) {
          console.log('[LessonPlanBrowser] No lessons with phase_plan found in any previous week, using first available lesson');
          fallbackLesson = sortedLessons[0];
        }
      }

      if (!fallbackLesson) {
        console.log('[LessonPlanBrowser] No fallback lesson found');
        return;
      }

      console.log('[LessonPlanBrowser] Using fallback lesson from previous week:', {
        lesson: fallbackLesson,
        week: finalWeekOf,
        day: fallbackLesson.day_of_week,
        slot: fallbackLesson.slot_number,
        planId: finalPlan.id,
        hasPhasePlan: hasPhasePlan(fallbackLesson, fallbackLesson.day_of_week || 'monday', fallbackLesson.slot_number || 1, finalPlanData)
      });

      // Set the week to the week we found the lesson in
      if (finalWeekOf !== selectedWeek) {
        setSelectedWeek(finalWeekOf);
        // Wait a bit for state to update
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Cache the plan data to avoid reloading
      setCachedLessonPlanData(finalPlanData);
      setCachedLessonPlanWeek(finalWeekOf);

      // Open the lesson - handleLessonClick will use cached data
      await handleLessonClick(
        fallbackLesson,
        fallbackLesson.day_of_week || 'monday',
        fallbackLesson.slot_number || 1
      );
    } catch (error) {
      console.error('[LessonPlanBrowser] Error in fallback:', error);
    }
  };

  // Helper function to get week_of date string (YYYY-MM-DD format for Monday of the week)
  const getWeekOfDate = (date: Date): string => {
    // Create a copy to avoid mutating the original date
    const dateCopy = new Date(date);
    // Get Monday of the week
    const day = dateCopy.getDay();
    const diff = dateCopy.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
    const monday = new Date(dateCopy);
    monday.setDate(diff);

    // Format as YYYY-MM-DD
    const year = monday.getFullYear();
    const month = String(monday.getMonth() + 1).padStart(2, '0');
    const dayOfMonth = String(monday.getDate()).padStart(2, '0');

    return `${year}-${month}-${dayOfMonth}`;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading lesson plans...</div>
        </div>
      </div>
    );
  }

  if (!selectedWeek) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">No weeks available</div>
          <div className="text-sm text-muted-foreground">Generate a lesson plan to get started</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col bg-background">
      {/* Top Bar */}
      <TopNavigationBar
        currentTime={currentTime}
        formatTime={formatTime}
        formatDate={formatDate}
        getDayAbbreviation={getDayAbbreviation}
        viewMode={viewMode}
        onWeekClick={handleWeekClick}
        onDayClick={() => {
          if (!selectedDay) {
            setSelectedDay('monday');
          }
          setViewMode('day');
        }}
        onLessonClick={async () => {
          // If there's already a selected lesson, just switch to lesson view
          if (selectedLesson) {
            setViewMode('lesson');
          } else {
            // Otherwise, find and open current/next lesson
            await handleLessonButtonClick();
          }
        }}
        onEnterLessonMode={onEnterLessonMode ? (scheduleEntry, day, slot, planId, previousViewMode, weekOf) => {
          // Pass current view mode and weekOf when entering from TopNavigationBar
          onEnterLessonMode(scheduleEntry, day, slot, planId, viewMode, weekOf || selectedWeek || undefined);
        } : undefined}
        onExitLessonMode={onExitLessonMode}
        showLessonModeButton={showLessonModeButton}
        selectedWeek={selectedWeek}
        availableWeeks={availableWeeks}
        onWeekChange={(week) => {
          setSelectedWeek(week);
          // Only reset if switching to a different week
          if (week !== selectedWeek) {
            setSelectedDay(null);
            setSelectedLesson(null);
            setCachedLessonPlanData(null); // Clear cached data for new week
            setCachedLessonPlanWeek(null);
            setViewMode('week');
          }
        }}
        onRefreshPlans={() => fetchPlans(true)}
        refreshing={refreshing}
        onTodayClick={handleTodayClick}
        findLessonForLessonMode={findLessonForLessonMode}
      />

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden min-h-0">
        {viewMode === 'week' && !initialLesson && (
          <div className="h-full w-full overflow-hidden">
            <WeekView
              weekOf={selectedWeek!}
              onLessonClick={handleLessonClick}
              onDayClick={handleWeekDayClick}
              currentLessonId={currentLesson?.id}
            />
          </div>
        )}

        {viewMode === 'day' && selectedDay && (
          <div className="h-full w-full overflow-hidden">
            <DayView
              weekOf={selectedWeek!}
              day={selectedDay}
              onLessonClick={handleLessonClick}
              onDaySwitch={handleDaySwitch}
            />
          </div>
        )}

        {viewMode === 'lesson' && selectedLesson && (
          <div className="h-full overflow-y-auto p-6">
            {(() => {
              const currentIndex = currentDayLessons.findIndex(
                lesson => lesson.id === selectedLesson.scheduleEntry.id
              );
              const canGoPrevious = currentIndex > 0;
              const canGoNext = currentIndex < currentDayLessons.length - 1;

              // Use the weekOf stored in selectedLesson (from when lesson was clicked)
              // This ensures we use the correct week even if selectedWeek hasn't updated yet
              // Fallback to selectedWeek if weekOf wasn't stored
              const weekOfForLesson = selectedLesson.weekOf || selectedLesson.scheduleEntry.week_of || selectedWeek;

              console.log('[LessonPlanBrowser] Rendering LessonDetailView with weekOf:', {
                selectedLesson_weekOf: selectedLesson.weekOf,
                scheduleEntry_week_of: selectedLesson.scheduleEntry.week_of,
                selectedWeek: selectedWeek,
                final_weekOfForLesson: weekOfForLesson,
                subject: selectedLesson.scheduleEntry.subject,
                day: selectedLesson.day,
                slot: selectedLesson.slot,
                priority: selectedLesson.weekOf ? 'selectedLesson.weekOf' : selectedLesson.scheduleEntry.week_of ? 'scheduleEntry.week_of' : 'selectedWeek (fallback)'
              });

              return (
                <LessonDetailView
                  scheduleEntry={selectedLesson.scheduleEntry}
                  day={selectedLesson.day}
                  slot={selectedLesson.slot}
                  planSlotIndex={selectedLesson.planSlotIndex}
                  initialSlotData={selectedLesson.planSlotData}
                  weekOf={weekOfForLesson || ''}
                  onBack={handleBack}
                  onEnterLessonMode={onEnterLessonMode ? (scheduleEntry, day, slot, planId, previousViewMode, weekOf) => {
                    // Pass 'lesson' view mode and weekOf when entering from LessonDetailView
                    // Use selectedWeek as fallback if weekOf is not provided
                    onEnterLessonMode(scheduleEntry, day, slot, planId, 'lesson', weekOf || selectedWeek || undefined);
                  } : undefined}
                  onPreviousLesson={handlePreviousLesson}
                  onNextLesson={handleNextLesson}
                  canGoPrevious={canGoPrevious}
                  canGoNext={canGoNext}
                />
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
