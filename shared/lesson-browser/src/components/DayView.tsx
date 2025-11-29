import { Card } from '@lesson-ui/Card';
import { Button } from '@lesson-ui/Button';
import { scheduleApi, ScheduleEntry, planApi, lessonApi } from '@lesson-api';
import { useStore } from '../store/useStore';
import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getSubjectColors } from '../utils/scheduleColors';
import { dedupeScheduleEntries } from '../utils/scheduleEntries';
import { buildSlotDataMap } from '../utils/planMatching';

interface DayViewProps {
  weekOf: string;
  day: string;
  onLessonClick: (
    scheduleEntry: ScheduleEntry,
    day: string,
    slot: number,
    planSlotIndex?: number,
    planSlotData?: any
  ) => void | Promise<void>;
  onDaySwitch?: (day: string) => void;
}

interface LessonSlotData {
  studentGoal?: string;
  widaObjective?: string;
  tailoredInstruction?: string;
  planSlotNumber?: number;
  planSlotIndex?: number;
  planSlot?: any;
}

// Helper function to check if entry is a non-class period
const isNonClassPeriod = (subject: string): boolean => {
  if (!subject) return false;
  // Normalize by removing extra spaces and converting to uppercase
  const normalized = subject.replace(/\s+/g, ' ').trim().toUpperCase();
  // Check for A.M. Routine variations (with or without space after A.)
  const amRoutinePattern = /^A\.?\s*M\.?\s*ROUTINE$/;
  return ['PREP', 'PREP TIME', 'LUNCH', 'A.M. ROUTINE', 'A. M. ROUTINE', 'AM ROUTINE', 'MORNING ROUTINE', 'DISMISSAL'].includes(normalized) ||
         amRoutinePattern.test(normalized);
};

export function DayView({ weekOf, day, onLessonClick, onDaySwitch }: DayViewProps) {
  const { currentUser } = useStore();
  const [lessons, setLessons] = useState<ScheduleEntry[]>([]);
  const [nonClassPeriods, setNonClassPeriods] = useState<ScheduleEntry[]>([]);
  const [lessonData, setLessonData] = useState<Record<number, LessonSlotData>>({});
  const [loading, setLoading] = useState(true);

  const dayLabels: Record<string, string> = {
    monday: 'Monday',
    tuesday: 'Tuesday',
    wednesday: 'Wednesday',
    thursday: 'Thursday',
    friday: 'Friday',
  };

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
  const currentDayIndex = days.indexOf(day);
  const hasPreviousDay = currentDayIndex > 0;
  const hasNextDay = currentDayIndex < days.length - 1;

  const handlePreviousDay = () => {
    if (hasPreviousDay && onDaySwitch) {
      onDaySwitch(days[currentDayIndex - 1]);
    }
  };

  const handleNextDay = () => {
    if (hasNextDay && onDaySwitch) {
      onDaySwitch(days[currentDayIndex + 1]);
    }
  };

  useEffect(() => {
    if (!currentUser || !day) {
      setLessons([]);
      setNonClassPeriods([]);
      setLessonData({});
      setLoading(false);
      return;
    }

    const loadDayData = async () => {
      setLoading(true);
      try {
        // Load schedule - this is the source of truth for what's actually scheduled
        console.log(`[DayView] Loading schedule for user: ${currentUser.id} (${currentUser.name}), day: ${day}`);
        const response = await scheduleApi.getSchedule(currentUser.id, day);
        console.log(`[DayView] Schedule entries received:`, response);
        const allEntries = response
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
        
        // Deduplicate entries
        const uniqueEntries = dedupeScheduleEntries(allEntries);
        
        // Separate lessons from non-class periods
        // Only show active entries as lessons, but include all non-class periods (even inactive) as reference
        // Defensive: Check isNonClassPeriod first to ensure non-class periods never end up in lessons array
        const lessonsOnly = uniqueEntries.filter(e => !isNonClassPeriod(e.subject) && e.is_active);
        const nonClassOnly = uniqueEntries.filter(e => isNonClassPeriod(e.subject));
        
        setLessons(lessonsOnly);
        setNonClassPeriods(nonClassOnly);

        // Load lesson plan data
        try {
          const plansResponse = await planApi.list(currentUser.id, 10, currentUser.id);
          const plans = plansResponse.data || [];
          const plan = plans.find(p => p.week_of === weekOf);
          
          if (plan) {
            const planDetailResponse = await lessonApi.getPlanDetail(plan.id, currentUser.id);
            const lessonJson = planDetailResponse.data.lesson_json;
            
            if (lessonJson && lessonJson.days && lessonJson.days[day]) {
              const dayData = lessonJson.days[day];
              const slotData = buildSlotDataMap(dayData, lessonsOnly);
              setLessonData(slotData as Record<number, LessonSlotData>);
            }
          }
        } catch (err) {
          console.warn('Could not load lesson plan data:', err);
        }
      } catch (error) {
        console.error('Failed to load day schedule:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDayData();
  }, [currentUser, day, weekOf]);

  if (loading) {
    return <div className="text-center py-8">Loading lessons...</div>;
  }

  return (
    <div className="h-full w-full flex flex-col min-h-0">
      {/* Day Header with Navigation */}
      <div className="flex items-center justify-between mb-1 px-2 flex-shrink-0 h-8">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePreviousDay}
            disabled={!hasPreviousDay || !onDaySwitch}
            className="h-7 px-2"
          >
            <ChevronLeft className="w-3 h-3" />
          </Button>
          <h2 className="text-sm font-semibold">{dayLabels[day] || day}</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextDay}
            disabled={!hasNextDay || !onDaySwitch}
            className="h-7 px-2"
          >
            <ChevronRight className="w-3 h-3" />
          </Button>
        </div>
        
        {/* Day Selector */}
        {onDaySwitch && (
          <div className="flex gap-1">
            {days.map((d) => (
              <Button
                key={d}
                variant={d === day ? 'default' : 'outline'}
                size="sm"
                onClick={() => onDaySwitch(d)}
                className="text-xs h-7 px-2"
              >
                {dayLabels[d].substring(0, 3)}
              </Button>
            ))}
          </div>
        )}
      </div>
      
      {/* Combine lessons and non-class periods, sorted by time */}
      {(() => {
        const allEntries = [...lessons, ...nonClassPeriods].sort((a, b) => {
          // Sort by start_time
          const timeA = a.start_time || '';
          const timeB = b.start_time || '';
          if (timeA !== timeB) {
            return timeA.localeCompare(timeB);
          }
          // If times are equal, sort by slot_number
          return a.slot_number - b.slot_number;
        });

        if (allEntries.length === 0) {
          return (
            <div className="text-center py-4 text-muted-foreground text-sm">
              No lessons scheduled for {dayLabels[day] || day}
            </div>
          );
        }

        return (
          <div className="flex-1 overflow-y-auto min-h-0">
            <div className="h-full w-full flex flex-col">
              {allEntries.map((entry) => {
                // Check if it's a non-class period
                const isNonClass = isNonClassPeriod(entry.subject);
                
                return (
                  <div 
                    key={entry.id} 
                    className={`grid grid-cols-[80px_1fr] gap-0 items-stretch border-b ${
                      isNonClass ? 'flex-[0.8]' : 'flex-[2]'
                    }`}
                  >
                    {/* Time label */}
                    <div className="text-xs font-medium text-muted-foreground py-2 flex items-center justify-end pr-2 border-r border-muted">
                      {entry.start_time} - {entry.end_time}
                    </div>
                    
                    {/* Content */}
                    {isNonClass ? (
                      (() => {
                        const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                        return (
                          <div className={`text-xs px-3 py-1 flex items-center ${colors.bg} ${colors.border} ${colors.text}`}>
                            {entry.subject}
                          </div>
                        );
                      })()
                    ) : (
                      (() => {
                        // Defensive: Double-check that this is not a non-class period
                        if (isNonClassPeriod(entry.subject)) {
                          console.warn('[DayView] Non-class period found in lessons array:', {
                            subject: entry.subject,
                            entryId: entry.id,
                            day: day,
                            time: `${entry.start_time}-${entry.end_time}`
                          });
                          const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                          return (
                            <div className={`text-xs px-3 py-1 flex items-center ${colors.bg} ${colors.border} ${colors.text}`}>
                              {entry.subject}
                            </div>
                          );
                        }
                        
                        const colors = getSubjectColors(entry.subject, entry.grade, entry.homeroom);
                        const slotData = lessonData[entry.slot_number] || {};
                        const lessonIndex = lessons.findIndex((lesson) => lesson.id === entry.id);
                        const fallbackPlanSlotNumber =
                          lessonIndex >= 0 ? lessonIndex + 1 : entry.slot_number;
                        const fallbackPlanSlotIndex = lessonIndex >= 0 ? lessonIndex : undefined;
                        const planSlotNumber = slotData.planSlotNumber ?? fallbackPlanSlotNumber;
                        const planSlotIndex = slotData.planSlotIndex ?? fallbackPlanSlotIndex;
                        const planSlotData = slotData.planSlot;
                        return (
                          <Card
                            className={`p-2 cursor-pointer hover:opacity-80 transition-all rounded-none border-0 h-full flex flex-col ${colors.bg} ${colors.border} ${colors.text}`}
                            onClick={() => onLessonClick(entry, day, planSlotNumber, planSlotIndex, planSlotData)}
                          >
                            <div className="space-y-1.5 flex-1 flex flex-col justify-center">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="font-semibold text-sm leading-tight">{entry.subject}</div>
                                  <div className="flex items-center gap-2 mt-0.5">
                                    {entry.grade && (
                                      <div className="text-xs opacity-80">Grade {entry.grade}</div>
                                    )}
                                    {entry.homeroom && (
                                      <div className="text-xs opacity-80">{entry.homeroom}</div>
                                    )}
                                  </div>
                                </div>
                              </div>
                              
                              {slotData.studentGoal && (
                                <div className="pt-1 border-t border-current/20">
                                  <div className="text-[10px] font-semibold mb-0.5 opacity-80">Student Goal:</div>
                                  <div className="text-xs leading-tight line-clamp-2">{slotData.studentGoal}</div>
                                </div>
                              )}
                              
                              {slotData.widaObjective && (
                                <div className="pt-1 border-t border-current/20">
                                  <div className="text-[10px] font-semibold mb-0.5 opacity-80">WIDA Objective:</div>
                                  <div className="text-xs leading-tight line-clamp-2">{slotData.widaObjective}</div>
                                </div>
                              )}
                              
                              {slotData.tailoredInstruction && (
                                <div className="pt-1 border-t border-current/20">
                                  <div className="text-[10px] font-semibold mb-0.5 opacity-80">Tailored Instruction:</div>
                                  <div className="text-xs leading-tight line-clamp-2">{slotData.tailoredInstruction}</div>
                                </div>
                              )}
                            </div>
                          </Card>
                        );
                      })()
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}
    </div>
  );
}

