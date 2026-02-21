import { Card } from '@lesson-ui/Card';
import { scheduleApi, ScheduleEntry, planApi, lessonApi } from '@lesson-api';
import { useStore } from '../store/useStore';
import { useState, useEffect } from 'react';
import { getSubjectColors, meetingPeriodColors } from '../utils/scheduleColors';
import { dedupeScheduleEntries, formatEntryDisplay, isMeetingPeriod, isNonClassPeriod } from '../utils/scheduleEntries';
import { buildSlotDataMap } from '../utils/planMatching';

const MEETING_CLASSES = `${meetingPeriodColors.bg} ${meetingPeriodColors.border} ${meetingPeriodColors.text}`;

interface WeekViewProps {
  weekOf: string;
  onLessonClick: (
    scheduleEntry: ScheduleEntry,
    day: string,
    slot: number,
    planSlotIndex?: number,
    planSlotData?: any,
    weekOf?: string
  ) => void | Promise<void>;
  onDayClick?: (day: string) => void;
  currentLessonId?: string | null;
}

interface LessonData {
  widaObjective?: string;
  grade?: string;
  planSlotNumber?: number;
  planSlotIndex?: number;
  planSlot?: any;
}

// Helper function to normalize time format (ensures consistent matching)
const normalizeTime = (time: string | null | undefined): string => {
  if (!time) return '';
  // Ensure HH:MM format (pad single digits)
  const parts = time.split(':');
  if (parts.length === 2) {
    const hours = parts[0].padStart(2, '0');
    const minutes = parts[1].padStart(2, '0');
    return `${hours}:${minutes}`;
  }
  return time;
};

// Helper function to create consistent time slot key
const createTimeSlotKey = (start: string, end: string): string => {
  return `${normalizeTime(start)}-${normalizeTime(end)}`;
};

export function WeekView({ weekOf, onLessonClick, onDayClick, currentLessonId }: WeekViewProps) {
  const { currentUser } = useStore();
  const [schedule, setSchedule] = useState<Record<string, ScheduleEntry[]>>({});
  const [nonClassPeriods, setNonClassPeriods] = useState<Record<string, ScheduleEntry[]>>({});
  const [lessonData, setLessonData] = useState<Record<string, Record<number, LessonData>>>({});
  const [loading, setLoading] = useState(true);
  
  // CRITICAL: Log the weekOf prop received
  console.log('[WeekView] Component rendered/re-rendered with weekOf prop:', {
    weekOf: weekOf,
    note: 'This weekOf will be used to load plans and passed to onLessonClick'
  });

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
  const dayLabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  useEffect(() => {
    if (!currentUser) {
      setSchedule({});
      setNonClassPeriods({});
      setLessonData({});
      setLoading(false);
      return;
    }

    // Clear previous lesson data to avoid showing stale plans when switching weeks
    setLessonData({});

    const loadData = async () => {
      setLoading(true);
      try {
        // Load schedule for the current user (fetch all at once to avoid rate limiting)
        console.log(`[WeekView] Loading schedule for user: ${currentUser.id} (${currentUser.name})`);
        const allEntries = await scheduleApi.getSchedule(currentUser.id);
        console.log(`[WeekView] All schedule entries:`, allEntries);

        // Group by day
        const grouped: Record<string, ScheduleEntry[]> = {};
        const nonClassPeriods: Record<string, ScheduleEntry[]> = {};
        
        // Debug: Log all entries before grouping
        console.log('[WeekView] Total entries loaded:', allEntries.length);
        console.log('[WeekView] Entries by day_of_week:', {
          monday: allEntries.filter(e => e.day_of_week === 'monday').length,
          tuesday: allEntries.filter(e => e.day_of_week === 'tuesday').length,
          wednesday: allEntries.filter(e => e.day_of_week === 'wednesday').length,
          thursday: allEntries.filter(e => e.day_of_week === 'thursday').length,
          friday: allEntries.filter(e => e.day_of_week === 'friday').length,
          other: allEntries.filter(e => !days.includes(e.day_of_week || '')).length
        });
        
        days.forEach(day => {
          // Get all entries for this day (including non-active non-class periods)
          const dayEntries = allEntries
            .filter(e => {
              const entryDay = (e.day_of_week || '').toLowerCase();
              const match = entryDay === day.toLowerCase();
              if (!match && entryDay) {
                // Log mismatches for debugging
                const subjectUpper = (e.subject || '').toUpperCase();
                if (subjectUpper.includes('ROUTINE') || subjectUpper.includes('AM')) {
                  console.warn('[WeekView] Entry day mismatch:', {
                    subject: e.subject,
                    entry_day: e.day_of_week,
                    expected_day: day,
                    entryId: e.id
                  });
                }
              }
              return match;
            })
            .sort((a, b) => {
              // Sort by slot_number first - this is the assigned order in the schedule
              if (a.slot_number !== b.slot_number) {
                return a.slot_number - b.slot_number;
              }
              // If slot_numbers are equal, fall back to start_time
              const timeA = a.start_time || '';
              const timeB = b.start_time || '';
              return timeA.localeCompare(timeB);
            });
          
          // Deduplicate entries using shared helper
          const uniqueEntries = dedupeScheduleEntries(dayEntries);
          
          // Log all entries for this day to debug A.M. Routine issue
          uniqueEntries.forEach(e => {
            const subjectUpper = (e.subject || '').toUpperCase();
            if (subjectUpper.includes('ROUTINE') || subjectUpper.includes('AM') || 
                (e.start_time && e.end_time && 
                 (normalizeTime(e.start_time) === '08:15' && normalizeTime(e.end_time) === '08:30'))) {
              console.log(`[WeekView] ${day} - Entry at 08:15-08:30 or A.M. Routine:`, {
                subject: e.subject,
                subjectUpper: subjectUpper,
                isNonClass: isNonClassPeriod(e.subject),
                is_active: e.is_active,
                entryId: e.id,
                day: day,
                day_of_week: e.day_of_week,
                time: `${e.start_time}-${e.end_time}`,
                normalized_time: createTimeSlotKey(e.start_time || '', e.end_time || ''),
                slot_number: e.slot_number
              });
            }
          });
          
          // Separate lessons from non-class periods
          // Only show active entries as lessons, but include all non-class periods (even inactive) as reference
          // Defensive: Check isNonClassPeriod first to ensure non-class periods never end up in lessons array
          const lessonsForDay = uniqueEntries.filter(e => !isNonClassPeriod(e.subject) && e.is_active);
          const nonClassForDay = uniqueEntries.filter(e => isNonClassPeriod(e.subject));
          
          // Log any entries that might be misclassified
          uniqueEntries.forEach(e => {
            if (e.is_active && isNonClassPeriod(e.subject)) {
              console.warn('[WeekView] Active non-class period found (should be inactive):', {
                subject: e.subject,
                entryId: e.id,
                day: day,
                time: `${e.start_time}-${e.end_time}`,
                is_active: e.is_active
              });
            }
          });
          
          grouped[day] = lessonsForDay;
          nonClassPeriods[day] = nonClassForDay;
          
          console.log(`[WeekView] ${day}:`, {
            total_entries: uniqueEntries.length,
            lessons: lessonsForDay.length,
            nonClass: nonClassForDay.length,
            lesson_subjects: lessonsForDay.map(e => e.subject),
            nonClass_subjects: nonClassForDay.map(e => e.subject)
          });
        });

        setSchedule(grouped);
        setNonClassPeriods(nonClassPeriods);

        // Load lesson plan data and align plan slots with schedule entries
        try {
          const plansResponse = await planApi.list(currentUser.id, 10, currentUser.id);
          const plans = plansResponse.data || [];
          const plan = plans.find(p => p.week_of === weekOf);
          
          console.log('[WeekView] Plan lookup for weekOf:', {
            weekOf: weekOf,
            planFound: !!plan,
            planId: plan?.id,
            planWeekOf: plan?.week_of,
            availablePlansWeekOf: plans.map(p => p.week_of),
            note: 'Looking for plan matching weekOf prop'
          });
          
          if (plan) {
            const planDetailResponse = await lessonApi.getPlanDetail(plan.id, currentUser.id);
            const lessonJson = planDetailResponse.data.lesson_json;
            
            if (lessonJson && lessonJson.days) {
              const data: Record<string, Record<number, LessonData>> = {};
              
              days.forEach(day => {
                const dayData = lessonJson.days[day];
                const scheduleLessons = grouped[day] || [];
                
                if (dayData) {
                  if (scheduleLessons.length > 0) {
                    // Match plan slots with schedule entries
                    const slotData = buildSlotDataMap(dayData, scheduleLessons);
                    data[day] = {};
                    Object.entries(slotData).forEach(([slotNumber, slotInfo]) => {
                      data[day][Number(slotNumber)] = {
                        widaObjective: slotInfo.widaObjective,
                        grade: slotInfo.planSlot?.grade || scheduleLessons.find(entry => entry.slot_number === Number(slotNumber))?.grade,
                        planSlotNumber: slotInfo.planSlotNumber,
                        planSlotIndex: slotInfo.planSlotIndex,
                        planSlot: slotInfo.planSlot,
                      };
                    });
                  } else if (dayData.slots && Array.isArray(dayData.slots)) {
                    // No schedule entries, but we have plan slots - show them directly
                    data[day] = {};
                    dayData.slots.forEach((slot: any, index: number) => {
                      const slotNumber = slot.slot_number || (index + 1);
                      data[day][slotNumber] = {
                        widaObjective: slot.wida_objective || slot.objective,
                        grade: slot.grade,
                        planSlotNumber: slotNumber,
                        planSlotIndex: index,
                        planSlot: slot,
                      };
                    });
                  }
                }
              });
              
              setLessonData(data);
            } else {
              setLessonData({});
            }
          } else {
            setLessonData({});
          }
        } catch (err) {
          console.warn('Could not load lesson plan data:', err);
          setLessonData({});
        }
      } catch (error) {
        console.error('Failed to load schedule:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [currentUser, weekOf]);

  if (loading) {
    return <div className="text-center py-8">Loading schedule...</div>;
  }

  // Collect all unique time slots for the time column (including non-class periods)
  const allTimeSlots = new Set<string>();
  const entriesWithoutTimes: Record<string, ScheduleEntry[]> = {};
  
  days.forEach(day => {
    entriesWithoutTimes[day] = [];
    
    schedule[day]?.forEach(entry => {
      if (entry.start_time && entry.end_time) {
        const normalizedStart = normalizeTime(entry.start_time);
        const normalizedEnd = normalizeTime(entry.end_time);
        allTimeSlots.add(createTimeSlotKey(normalizedStart, normalizedEnd));
      } else {
        // Track entries without times to handle them separately
        entriesWithoutTimes[day].push(entry);
      }
    });
    
    nonClassPeriods[day]?.forEach(entry => {
      if (entry.start_time && entry.end_time) {
        const normalizedStart = normalizeTime(entry.start_time);
        const normalizedEnd = normalizeTime(entry.end_time);
        allTimeSlots.add(createTimeSlotKey(normalizedStart, normalizedEnd));
      } else {
        // Track non-class periods without times
        entriesWithoutTimes[day].push(entry);
      }
    });
  });
  
  const sortedTimeSlots = Array.from(allTimeSlots).sort();
  
  // If we have entries without times, create slot-based rows for them
  const hasEntriesWithoutTimes = days.some(day => entriesWithoutTimes[day].length > 0);
  const slotBasedRows: number[] = [];
  if (hasEntriesWithoutTimes) {
    // Collect all unique slot numbers from entries without times
    const slotNumbers = new Set<number>();
    days.forEach(day => {
      entriesWithoutTimes[day].forEach(entry => {
        if (entry.slot_number) {
          slotNumbers.add(entry.slot_number);
        }
      });
    });
    slotBasedRows.push(...Array.from(slotNumbers).sort((a, b) => a - b));
  }
  
  // Debug: Log time slots and entries per day
  console.log('[WeekView] Time slots found:', sortedTimeSlots);
  console.log('[WeekView] Entries without times:', entriesWithoutTimes);
  console.log('[WeekView] Slot-based rows:', slotBasedRows);
  days.forEach(day => {
    console.log(`[WeekView] ${day} entries:`, {
      lessons: schedule[day]?.map(e => ({
        subject: e.subject,
        time: `${e.start_time}-${e.end_time}`,
        normalized: createTimeSlotKey(e.start_time || '', e.end_time || ''),
        slot_number: e.slot_number
      })),
      nonClass: nonClassPeriods[day]?.map(e => ({
        subject: e.subject,
        time: `${e.start_time}-${e.end_time}`,
        normalized: createTimeSlotKey(e.start_time || '', e.end_time || ''),
        slot_number: e.slot_number
      }))
    });
  });
  
  // Build a map of time slot -> day -> entry for efficient lookup
  const timeSlotMap: Record<string, Record<string, ScheduleEntry>> = {};
  sortedTimeSlots.forEach(timeSlot => {
    timeSlotMap[timeSlot] = {};
    days.forEach(day => {
      const lessonEntry = schedule[day]?.find(e => {
        const entryTimeSlot = createTimeSlotKey(e.start_time || '', e.end_time || '');
        return entryTimeSlot === timeSlot;
      });
      const nonClassEntry = nonClassPeriods[day]?.find(e => {
        const entryTimeSlot = createTimeSlotKey(e.start_time || '', e.end_time || '');
        return entryTimeSlot === timeSlot;
      });
      // Prefer non-class entry if it exists, otherwise lesson entry
      if (nonClassEntry) {
        timeSlotMap[timeSlot][day] = nonClassEntry;
      } else if (lessonEntry) {
        timeSlotMap[timeSlot][day] = lessonEntry;
      }
    });
  });

  return (
    <div className="h-full w-full flex flex-col min-h-0">
      <div className="border rounded-lg overflow-x-auto flex-1 min-h-0">
        <table className="w-full border-collapse h-full">
          <thead className="sticky top-0 bg-card z-10">
            <tr className="bg-muted h-8">
              <th className="border px-2 py-1 text-left text-sm font-semibold min-w-[100px] sticky left-0 bg-muted z-20 h-8">Time</th>
              {days.map((day, dayIdx) => (
                <th 
                  key={day} 
                  className={`border px-2 py-1 text-center text-sm font-semibold min-w-[120px] h-8 ${onDayClick ? 'cursor-pointer hover:text-primary transition-colors' : ''}`}
                  onClick={() => onDayClick?.(day)}
                >
                  {dayLabels[dayIdx]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Render time-based rows */}
            {sortedTimeSlots.map((timeSlot) => {
          const [start, end] = timeSlot.split('-');
          const normalizedStart = normalizeTime(start);
          const normalizedEnd = normalizeTime(end);
          const entryForRow = timeSlotMap[timeSlot];
          
          return (
            <tr key={timeSlot} className="hover:bg-muted/30">
              {/* Time label */}
              <td className="border p-2 font-mono text-sm bg-muted/50 sticky left-0 z-10">
                {normalizedStart} - {normalizedEnd}
              </td>
              
              {/* Day columns for this time slot */}
              {days.map((day) => {
                const entry = entryForRow[day];
                
                // Show non-class period if it exists (meetings use teal via literal classes)
                if (entry && isNonClassPeriod(entry.subject)) {
                  const isMeeting = isMeetingPeriod(entry.subject);
                  const displayText = formatEntryDisplay(entry.subject, entry.grade, entry.homeroom, isMeeting);
                  const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                  const cellClass = isMeeting
                    ? `border p-2 text-sm font-medium min-w-[150px] ${MEETING_CLASSES} cursor-pointer hover:opacity-80 transition-opacity`
                    : `border p-2 text-sm font-medium min-w-[150px] ${colors.bg} ${colors.border} ${colors.text} cursor-pointer hover:opacity-80 transition-opacity`;
                  return (
                    <td
                      key={`${day}-${entry.id}`}
                      className={cellClass}
                    >
                      {displayText}
                    </td>
                  );
                }
                
                // Show lesson card if it exists
                if (entry && !isNonClassPeriod(entry.subject)) {
                  const slotData = lessonData[day]?.[entry.slot_number];
                  const dayLessons = schedule[day] || [];
                  const orderIndex = dayLessons.findIndex((e) => e.id === entry.id);
                  const fallbackPlanSlotNumber =
                    orderIndex >= 0 ? orderIndex + 1 : entry.slot_number;
                  const fallbackPlanSlotIndex = orderIndex >= 0 ? orderIndex : undefined;
                  const planSlotNumber = slotData?.planSlotNumber ?? fallbackPlanSlotNumber;
                  const planSlotIndex = slotData?.planSlotIndex ?? fallbackPlanSlotIndex;
                  const planSlot = slotData?.planSlot;
                  const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                  const isCurrentLesson = currentLessonId && entry.id === currentLessonId;
                  
                  return (
                    <td
                      key={entry.id}
                      className={`border p-2 cursor-pointer hover:opacity-80 transition-opacity min-w-[150px] ${colors.bg} ${colors.border} ${colors.text} ${isCurrentLesson ? 'ring-2 ring-primary shadow-md' : ''}`}
                      onClick={() => {
                        console.log('[WeekView] Clicking lesson:', {
                          subject: entry.subject,
                          day: day,
                          slot: planSlotNumber,
                          weekOf: weekOf,
                          entryId: entry.id,
                          note: 'Passing weekOf to onLessonClick'
                        });
                        onLessonClick(entry, day, planSlotNumber, planSlotIndex, planSlot, weekOf);
                      }}
                      title={`${entry.subject}${entry.grade ? ` - Grade ${entry.grade}` : ''}${entry.homeroom ? ` - ${entry.homeroom}` : ''}`}
                    >
                      <div className="space-y-0.5">
                        <div className={`text-sm font-medium ${colors.text}`}>{entry.subject}</div>
                        {isCurrentLesson && (
                          <div className="text-[10px] font-semibold text-primary uppercase tracking-wide">
                            Now
                          </div>
                        )}
                        {(entry.grade || slotData?.grade) && (
                          <div className="text-xs opacity-80 leading-tight">
                            Grade {entry.grade || slotData?.grade}
                          </div>
                        )}
                        {entry.homeroom && (
                          <div className="text-xs opacity-80 leading-tight">{entry.homeroom}</div>
                        )}
                        {entry.plan_slot_group_id && (
                          <div className="text-[10px] uppercase tracking-wide font-semibold opacity-80 mt-1">
                            Group: {entry.plan_slot_group_id}
                          </div>
                        )}
                        {slotData?.widaObjective && (
                          <div className="text-[10px] opacity-80 mt-0.5 line-clamp-1 leading-tight">
                            {slotData.widaObjective}
                          </div>
                        )}
                      </div>
                    </td>
                  );
                }
                
                // Empty slot
                return (
                  <td 
                    key={`${day}-empty`} 
                    className="border p-2"
                  ></td>
                );
              })}
            </tr>
          );
        })}
        
        {/* Render slot-based rows for entries without times */}
        {slotBasedRows.map((slotNumber) => {
          return (
            <tr key={`slot-${slotNumber}`} className="hover:bg-muted/30">
              {/* Slot label */}
              <td className="border p-2 font-mono text-sm bg-muted/50 sticky left-0 z-10">
                Slot {slotNumber}
              </td>
              
              {/* Day columns for this slot */}
              {days.map((day) => {
                const lessonEntry = entriesWithoutTimes[day]?.find(e => 
                  e.slot_number === slotNumber && !isNonClassPeriod(e.subject) && e.is_active
                );
                const nonClassEntry = entriesWithoutTimes[day]?.find(e => 
                  e.slot_number === slotNumber && isNonClassPeriod(e.subject)
                );
                
                // Show non-class period if it exists (meetings use teal via literal classes)
                if (nonClassEntry) {
                  const isMeeting = isMeetingPeriod(nonClassEntry.subject);
                  const displayText = formatEntryDisplay(nonClassEntry.subject, nonClassEntry.grade, nonClassEntry.homeroom, isMeeting);
                  const colors = getSubjectColors(nonClassEntry.subject, nonClassEntry.grade, nonClassEntry.homeroom);
                  const cellClass = isMeeting
                    ? `border p-2 text-sm font-medium min-w-[150px] ${MEETING_CLASSES} cursor-pointer hover:opacity-80 transition-opacity`
                    : `border p-2 text-sm font-medium min-w-[150px] ${colors.bg} ${colors.border} ${colors.text} cursor-pointer hover:opacity-80 transition-opacity`;
                  return (
                    <td
                      key={`${day}-${nonClassEntry.id}`}
                      className={cellClass}
                    >
                      {displayText}
                    </td>
                  );
                }
                
                // Show lesson card if it exists
                if (lessonEntry) {
                  const slotData = lessonData[day]?.[lessonEntry.slot_number];
                  const dayLessons = schedule[day] || [];
                  const orderIndex = dayLessons.findIndex((e) => e.id === lessonEntry.id);
                  const fallbackPlanSlotNumber =
                    orderIndex >= 0 ? orderIndex + 1 : lessonEntry.slot_number;
                  const fallbackPlanSlotIndex = orderIndex >= 0 ? orderIndex : undefined;
                  const planSlotNumber = slotData?.planSlotNumber ?? fallbackPlanSlotNumber;
                  const planSlotIndex = slotData?.planSlotIndex ?? fallbackPlanSlotIndex;
                  const planSlot = slotData?.planSlot;
                  const colors = getSubjectColors(lessonEntry.subject, lessonEntry.grade, lessonEntry.homeroom);
                  const isCurrentLesson = currentLessonId && lessonEntry.id === currentLessonId;
                  
                  return (
                    <td
                      key={lessonEntry.id}
                      className={`border p-2 cursor-pointer hover:opacity-80 transition-opacity min-w-[150px] ${colors.bg} ${colors.border} ${colors.text} ${isCurrentLesson ? 'ring-2 ring-primary shadow-md' : ''}`}
                      onClick={() => {
                        console.log('[WeekView] Clicking lesson (from lessonData):', {
                          subject: lessonEntry.subject,
                          day: day,
                          slot: planSlotNumber,
                          weekOf: weekOf,
                          entryId: lessonEntry.id,
                          note: 'Passing weekOf to onLessonClick'
                        });
                        onLessonClick(lessonEntry, day, planSlotNumber, planSlotIndex, planSlot, weekOf);
                      }}
                      title={`${lessonEntry.subject}${lessonEntry.grade ? ` - Grade ${lessonEntry.grade}` : ''}${lessonEntry.homeroom ? ` - ${lessonEntry.homeroom}` : ''}`}
                    >
                      <div className="space-y-0.5">
                        <div className={`text-sm font-medium ${colors.text}`}>{lessonEntry.subject}</div>
                        {isCurrentLesson && (
                          <div className="text-[10px] font-semibold text-primary uppercase tracking-wide">
                            Now
                          </div>
                        )}
                        {(lessonEntry.grade || slotData?.grade) && (
                          <div className="text-xs opacity-80 leading-tight">
                            Grade {lessonEntry.grade || slotData?.grade}
                          </div>
                        )}
                        {lessonEntry.homeroom && (
                          <div className="text-xs opacity-80 leading-tight">{lessonEntry.homeroom}</div>
                        )}
                        {lessonEntry.plan_slot_group_id && (
                          <div className="text-[10px] uppercase tracking-wide font-semibold opacity-80 mt-1">
                            Group: {lessonEntry.plan_slot_group_id}
                          </div>
                        )}
                        {slotData?.widaObjective && (
                          <div className="text-[10px] opacity-80 mt-0.5 line-clamp-1 leading-tight">
                            {slotData.widaObjective}
                          </div>
                        )}
                      </div>
                    </td>
                  );
                }
                
                // Empty slot
                return (
                  <td 
                    key={`${day}-empty-slot-${slotNumber}`} 
                    className="border p-2"
                  ></td>
                );
              })}
            </tr>
          );
        })}
          </tbody>
        </table>
      </div>
      
      {/* Fallback for when no time slots and no slot-based entries exist */}
      {sortedTimeSlots.length === 0 && slotBasedRows.length === 0 && (
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="grid grid-cols-[80px_repeat(5,1fr)] gap-0 p-4">
            <div className="text-xs text-muted-foreground font-medium">Slot</div>
            {days.map((day) => {
              const daySlots = lessonData[day];
              const scheduleEntries = schedule[day] || [];
              
              // If we have plan slots but no schedule, show plan slots directly
              if (daySlots && Object.keys(daySlots).length > 0 && scheduleEntries.length === 0) {
                const slotNumbers = Object.keys(daySlots).map(Number).sort((a, b) => a - b);
                return (
                  <div key={day} className="space-y-2">
                    {slotNumbers.map((slotNumber) => {
                      const slotData = daySlots[slotNumber];
                      const planSlot = slotData?.planSlot;
                      const subject = planSlot?.subject || planSlot?.unit || 'Lesson';
                      const grade = slotData?.grade || planSlot?.grade;
                      
                      return (
                        <Card
                          key={slotNumber}
                          className="p-3 cursor-pointer hover:opacity-80 transition-all bg-card border"
                          onClick={() => {
                            // Create a minimal schedule entry for the click handler
                            const mockEntry: ScheduleEntry = {
                              id: `plan-slot-${day}-${slotNumber}`,
                              user_id: currentUser?.id || '',
                              day_of_week: day,
                              slot_number: slotNumber,
                              subject: subject,
                              grade: grade || undefined,
                              is_active: true,
                            } as ScheduleEntry;
                            console.log('[WeekView] Clicking lesson (mock entry):', {
                              subject: subject,
                              day: day,
                              slot: slotData.planSlotNumber || slotNumber,
                              weekOf: weekOf,
                              note: 'Passing weekOf to onLessonClick'
                            });
                            onLessonClick(mockEntry, day, slotData.planSlotNumber || slotNumber, slotData.planSlotIndex, planSlot, weekOf);
                          }}
                        >
                          <div className="space-y-1">
                            <div className="font-semibold text-sm">{subject}</div>
                            {grade && (
                              <div className="text-xs opacity-80">Grade {grade}</div>
                            )}
                            {slotData?.widaObjective && (
                              <div className="text-xs opacity-80 mt-1 line-clamp-2">
                                {slotData.widaObjective}
                              </div>
                            )}
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                );
              }
              
              // If we have schedule entries, show them
              if (scheduleEntries.length > 0) {
                return (
                  <div key={day} className="space-y-2">
                    {scheduleEntries.map((entry) => {
                      const slotData = lessonData[day]?.[entry.slot_number];
                      const isMeeting = isMeetingPeriod(entry.subject);
                      const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                      const cardClass = isMeeting
                        ? `p-3 cursor-pointer hover:opacity-80 transition-all ${MEETING_CLASSES}`
                        : `p-3 cursor-pointer hover:opacity-80 transition-all ${colors.bg} ${colors.border} ${colors.text}`;
                      return (
                        <Card
                          key={entry.id}
                          className={cardClass}
                          onClick={() => {
                            const slotInfo = lessonData[day]?.[entry.slot_number];
                            const dayLessons = schedule[day] || [];
                            const orderIndex = dayLessons.findIndex((lesson) => lesson.id === entry.id);
                            const fallbackPlanSlotNumber =
                              orderIndex >= 0 ? orderIndex + 1 : entry.slot_number;
                            const fallbackPlanSlotIndex = orderIndex >= 0 ? orderIndex : undefined;
                            const planSlotNum = slotInfo?.planSlotNumber ?? fallbackPlanSlotNumber;
                            const planSlotIdx = slotInfo?.planSlotIndex ?? fallbackPlanSlotIndex;
                            const planSlotData = slotInfo?.planSlot;
                            console.log('[WeekView] Clicking lesson (from slotData):', {
                              subject: entry.subject,
                              day: day,
                              slot: planSlotNum,
                              weekOf: weekOf,
                              entryId: entry.id,
                              note: 'Passing weekOf to onLessonClick'
                            });
                            onLessonClick(entry, day, planSlotNum, planSlotIdx, planSlotData, weekOf);
                          }}
                        >
                          <div className="space-y-1">
                            <div className="font-semibold text-sm">{entry.subject}</div>
                            {(entry.grade || slotData?.grade) && (
                              <div className="text-xs opacity-80">
                                Grade {entry.grade || slotData?.grade}
                              </div>
                            )}
                            {entry.homeroom && (
                              <div className="text-xs opacity-80">{entry.homeroom}</div>
                            )}
                            {slotData?.widaObjective && (
                              <div className="text-xs opacity-80 mt-1 line-clamp-2">
                                {slotData.widaObjective}
                              </div>
                            )}
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                );
              }
              
              // No schedule and no plan data
              return (
                <div key={day} className="text-center text-sm text-muted-foreground py-4">
                  No lessons scheduled
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

