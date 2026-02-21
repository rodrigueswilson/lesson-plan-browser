import { useState } from 'react';
import { Clock, Grid, CalendarDays, FileText, PlayCircle, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Select } from '@lesson-ui/Select';
import { Label } from '@lesson-ui/Label';
import type { ScheduleEntry } from '@lesson-api';
import { LessonMetadataDisplay } from './LessonMetadataDisplay';

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
  // Get timing status for header background color
  // Prefer scheduleStatus from timer if available, otherwise will be calculated by LessonMetadataDisplay
  const [calculatedStatus, setCalculatedStatus] = useState<'past' | 'current' | 'future' | null>(null);
  const lessonTimingStatus = lessonMetadata?.scheduleStatus || calculatedStatus;
  
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
        {lessonMetadata && (lessonMetadata.subject || lessonMetadata.grade || lessonMetadata.homeroom) && (
          <LessonMetadataDisplay
            lessonMetadata={lessonMetadata}
            day={lessonMetadata.day_of_week}
            weekOf={selectedWeek || undefined}
            showStatusBadge={true}
            onStatusCalculate={setCalculatedStatus}
          />
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
                      selectedWeek || undefined // weekOf - use selectedWeek if available
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

