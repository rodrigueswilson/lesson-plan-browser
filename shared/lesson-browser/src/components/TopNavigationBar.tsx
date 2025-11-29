import { Clock, Grid, CalendarDays, FileText, PlayCircle, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Select } from '@lesson-ui/Select';
import { Label } from '@lesson-ui/Label';
import type { ScheduleEntry } from '@lesson-api';

interface TopNavigationBarProps {
  // Clock and date
  currentTime: Date;
  formatTime: (date: Date) => string;
  formatDate: (date: Date) => string;
  getDayAbbreviation: (date: Date) => string;

  // Lesson metadata (for display in lesson mode)
  lessonMetadata?: {
    subject?: string;
    grade?: string;
    homeroom?: string;
    start_time?: string;
    end_time?: string;
    day_of_week?: string;
    formatted_date?: string;
    scheduleStatus?: 'past' | 'current' | 'future'; // Schedule status from timer
  };

  // View mode buttons
  viewMode?: 'week' | 'day' | 'lesson' | 'lesson-mode';
  onWeekClick?: () => void;
  onDayClick?: () => void;
  onLessonClick?: () => void;
  onEnterLessonMode?: (scheduleEntry: ScheduleEntry, day?: string, slot?: number, planId?: string, previousViewMode?: 'week' | 'day' | 'lesson', weekOf?: string) => void;
  onExitLessonMode?: () => void;
  showLessonModeButton?: boolean; // Whether to highlight Lesson Mode button (when in lesson mode)

  // Week selector
  selectedWeek?: string | null;
  availableWeeks?: Array<{ week_of: string; display: string }>;
  onWeekChange?: (week: string | null) => void;

  // Refresh button
  onRefreshPlans?: () => void;
  refreshing?: boolean;

  // Today button
  onTodayClick?: () => void;

  // Lesson finding function
  findLessonForLessonMode?: () => Promise<{
    scheduleEntry: ScheduleEntry;
    day: string;
    slot: number;
    planId?: string;
  } | null>;
}

export function TopNavigationBar({
  currentTime,
  formatTime,
  formatDate,
  getDayAbbreviation,
  lessonMetadata,
  viewMode,
  onWeekClick,
  onDayClick,
  onLessonClick,
  onEnterLessonMode,
  onExitLessonMode,
  showLessonModeButton = false,
  selectedWeek,
  availableWeeks = [],
  onWeekChange,
  onRefreshPlans,
  refreshing = false,
  onTodayClick,
  findLessonForLessonMode,
}: TopNavigationBarProps) {
  // Determine lesson timing status (current, past, or future)
  // Use scheduleStatus from timer if available, otherwise calculate it
  const getLessonTimingStatus = (): 'current' | 'past' | 'future' | null => {
    // Prefer scheduleStatus from timer (more accurate, uses performance.now())
    if (lessonMetadata?.scheduleStatus) {
      return lessonMetadata.scheduleStatus;
    }

    // Fallback to calculating from metadata
    if (!lessonMetadata?.start_time || !lessonMetadata?.end_time) {
      return null;
    }

    try {
      const now = currentTime;
      const startTimeParts = lessonMetadata.start_time.split(':');
      const endTimeParts = lessonMetadata.end_time.split(':');
      
      if (startTimeParts.length < 2 || endTimeParts.length < 2) {
        return null;
      }
      
      const [startH, startM] = startTimeParts.map(Number);
      const [endH, endM] = endTimeParts.map(Number);
      
      if (isNaN(startH) || isNaN(startM) || isNaN(endH) || isNaN(endM)) {
        return null;
      }
      
      const start = new Date(now);
      start.setHours(startH, startM, 0, 0);
      
      const end = new Date(now);
      end.setHours(endH, endM, 0, 0);
      
      // Check if lesson is currently happening
      if (now >= start && now <= end) {
        return 'current';
      }
      
      // Check if lesson is in the past
      if (now > end) {
        return 'past';
      }
      
      // Lesson is in the future
      return 'future';
    } catch (error) {
      console.error('Error calculating lesson timing status:', error);
      return null;
    }
  };

  const lessonTimingStatus = getLessonTimingStatus();
  
  // Determine color classes based on timing status
  // Green: past (already happened)
  // Blue: current (happening now)
  // Orange: future (will happen)
  const getMetadataColorClasses = () => {
    switch (lessonTimingStatus) {
      case 'current':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'past':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'future':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      default:
        return 'bg-muted/30 border-muted';
    }
  };
  const headerBgColor = lessonTimingStatus === 'current' 
    ? 'bg-blue-50' 
    : lessonTimingStatus === 'past' 
    ? 'bg-green-50' 
    : lessonTimingStatus === 'future'
    ? 'bg-orange-50'
    : 'bg-muted/30';

  return (
    <div className={`border-b ${headerBgColor} px-6 py-3 flex-shrink-0 h-16`}>
      <div className="flex items-center gap-4 h-full">
        {/* Clock Display */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-md border">
          <Clock className="w-4 h-4 text-muted-foreground" />
          <span className="font-mono text-sm font-medium tabular-nums">
            {formatTime(currentTime)}
          </span>
          <span className="text-sm font-medium text-muted-foreground">
            {formatDate(currentTime)}. {getDayAbbreviation(currentTime)}
          </span>
        </div>

        {/* Lesson Metadata */}
        {lessonMetadata && (lessonMetadata.subject || lessonMetadata.grade || lessonMetadata.homeroom) && (() => {
          console.log('[TopNavigationBar] Rendering lessonMetadata:', {
            subject: lessonMetadata.subject,
            grade: lessonMetadata.grade,
            homeroom: lessonMetadata.homeroom,
            day_of_week: lessonMetadata.day_of_week,
            formatted_date: lessonMetadata.formatted_date,
            start_time: lessonMetadata.start_time,
            end_time: lessonMetadata.end_time
          });
          return true;
        })() && (
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${getMetadataColorClasses()}`}>
            <div className="text-sm text-muted-foreground flex items-center gap-0">
              {lessonMetadata.subject && (
                <span className="font-medium">{lessonMetadata.subject}</span>
              )}
              {lessonMetadata.grade && (
                <span className={lessonTimingStatus ? 'opacity-90' : ''}>
                  • Grade {lessonMetadata.grade}
                </span>
              )}
              {lessonMetadata.homeroom && (
                <span className={lessonTimingStatus ? 'opacity-90' : ''}>
                  • {lessonMetadata.homeroom}
                </span>
              )}
              {lessonMetadata.day_of_week && (
                <span className={lessonTimingStatus ? 'opacity-90' : ''}>
                  • {lessonMetadata.day_of_week}
                </span>
              )}
              {lessonMetadata.formatted_date && (
                <span className={lessonTimingStatus ? 'opacity-90' : ''}>
                  • {lessonMetadata.formatted_date}
                </span>
              )}
              {lessonMetadata.start_time && lessonMetadata.end_time && (
                <span className={lessonTimingStatus ? 'opacity-90' : ''}>
                  • {lessonMetadata.start_time} - {lessonMetadata.end_time}
                </span>
              )}
            </div>
          </div>
        )}

        {/* View Mode Buttons - Only show when NOT in lesson-mode */}
        {viewMode !== 'lesson-mode' && (
          <div className="flex gap-2">
            {onWeekClick && (
              <Button
                variant={viewMode === 'week' ? 'default' : 'outline'}
                size="sm"
                onClick={onWeekClick}
              >
                <Grid className="w-4 h-4 mr-2" />
                Week
              </Button>
            )}
            {onDayClick && (
              <Button
                variant={viewMode === 'day' ? 'default' : 'outline'}
                size="sm"
                onClick={onDayClick}
              >
                <CalendarDays className="w-4 h-4 mr-2" />
                Day
              </Button>
            )}
            {onLessonClick && (
              <Button
                variant={viewMode === 'lesson' ? 'default' : 'outline'}
                size="sm"
                onClick={onLessonClick}
              >
                <FileText className="w-4 h-4 mr-2" />
                Lesson
              </Button>
            )}
            {onEnterLessonMode && findLessonForLessonMode && (
              <Button
                variant={showLessonModeButton ? 'default' : 'outline'}
                size="sm"
                onClick={async () => {
                  const lessonData = await findLessonForLessonMode();
                  if (lessonData) {
                    onEnterLessonMode(
                      lessonData.scheduleEntry,
                      lessonData.day,
                      lessonData.slot,
                      lessonData.planId,
                      undefined, // previousViewMode
                      undefined // weekOf - will be calculated from lessonPlanData
                    );
                  } else {
                    console.warn('[TopNavigationBar] No lesson available for Lesson Mode');
                  }
                }}
              >
                <PlayCircle className="w-4 h-4 mr-2" />
                Lesson Mode
              </Button>
            )}
          </div>
        )}

        {/* Right-aligned controls */}
        <div className="flex items-center gap-2 ml-auto">
          {/* Week Selector - Only show when NOT in lesson-mode */}
          {viewMode !== 'lesson-mode' && selectedWeek !== undefined && availableWeeks.length > 0 && onWeekChange && (
            <div className="flex items-center gap-2">
              <Label htmlFor="week-select" className="text-sm">Week:</Label>
              <Select
                id="week-select"
                value={selectedWeek || ''}
                onChange={(e) => {
                  onWeekChange(e.target.value || null);
                }}
                className="w-48"
              >
                {availableWeeks.map((week) => (
                  <option key={week.week_of} value={week.week_of}>
                    {week.display}
                  </option>
                ))}
              </Select>
            </div>
          )}

          {/* Refresh Button - Only show when NOT in lesson-mode, after week selector */}
          {viewMode !== 'lesson-mode' && onRefreshPlans && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefreshPlans}
              disabled={refreshing}
              title="Refresh lesson plans"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          )}

          {/* Today Button - Only show when NOT in lesson-mode */}
          {viewMode !== 'lesson-mode' && onTodayClick && (
            <Button
              variant="outline"
              size="sm"
              onClick={onTodayClick}
            >
              Today
            </Button>
          )}

          {/* Exit Lesson Mode Button - Only show when IN lesson-mode, positioned on the right */}
          {viewMode === 'lesson-mode' && onExitLessonMode && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExitLessonMode}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Exit Lesson Mode
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

