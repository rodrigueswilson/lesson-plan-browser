import { useEffect } from 'react';
import type { ScheduleEntry } from '@lesson-api';

interface LessonMetadataDisplayProps {
  // Can accept either a ScheduleEntry directly or pre-formatted metadata
  scheduleEntry?: ScheduleEntry;
  lessonMetadata?: {
    subject?: string;
    grade?: string;
    homeroom?: string;
    start_time?: string;
    end_time?: string;
    day_of_week?: string;
    formatted_date?: string;
    scheduleStatus?: 'past' | 'current' | 'future';
  };
  // Optional: day and weekOf for calculating date if not provided
  day?: string;
  weekOf?: string;
  // Optional: custom styling
  className?: string;
  showStatusBadge?: boolean; // Whether to show the Live/Past/Upcoming badge
  onStatusCalculate?: (status: 'past' | 'current' | 'future' | null) => void; // Callback for status calculation
}

/**
 * Shared component for displaying lesson metadata
 * Supports both ScheduleEntry and pre-formatted lessonMetadata
 */
export function LessonMetadataDisplay({
  scheduleEntry,
  lessonMetadata,
  day,
  weekOf,
  className = '',
  showStatusBadge = false,
  onStatusCalculate,
}: LessonMetadataDisplayProps) {
  // Helper to get day name (capitalize first letter)
  const getDayName = (dayStr: string): string => {
    if (!dayStr) return '';
    return dayStr.charAt(0).toUpperCase() + dayStr.slice(1);
  };

  // Format date as MM/DD/YY
  const formatDateShort = (date: Date | null): string | null => {
    if (!date || isNaN(date.getTime())) {
      return null;
    }
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    return `${month}/${day}/${year}`;
  };

  // Calculate lesson date from week_of and day_of_week if needed
  const getLessonDateObject = (): Date | null => {
    // If formatted_date is provided in metadata, parse it
    if (lessonMetadata?.formatted_date) {
      const dateParts = lessonMetadata.formatted_date.split('/');
      if (dateParts.length === 3) {
        const [month, day, year] = dateParts.map(Number);
        const fullYear = year < 100 ? 2000 + year : year;
        return new Date(fullYear, month - 1, day);
      }
    }

    // Otherwise, calculate from weekOf and day if available
    if (!weekOf || !day) return null;

    try {
      let mondayDate: Date;
      
      // Check if weekOf is in "W47" format (week number)
      if (weekOf.startsWith('W') || weekOf.startsWith('w')) {
        const weekNumber = parseInt(weekOf.substring(1), 10);
        if (isNaN(weekNumber) || weekNumber < 1 || weekNumber > 53) {
          return null;
        }
        
        const year = new Date().getFullYear();
        const jan1 = new Date(year, 0, 1);
        const dayOfWeek = jan1.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        const mondayOfWeek1 = new Date(jan1);
        mondayOfWeek1.setDate(jan1.getDate() - daysToMonday);
        const mondayOfTargetWeek = new Date(mondayOfWeek1);
        mondayOfTargetWeek.setDate(mondayOfWeek1.getDate() + (weekNumber - 1) * 7);
        mondayDate = mondayOfTargetWeek;
      } else {
        // weekOf format is "MM-DD-MM-DD" (Monday to Friday)
        const parts = weekOf.split('-');
        if (parts.length < 2) {
          return null;
        }
        
        const [startMonth, startDay] = parts.slice(0, 2).map(Number);
        if (isNaN(startMonth) || isNaN(startDay) || startMonth < 1 || startMonth > 12 || startDay < 1 || startDay > 31) {
          return null;
        }
        
        // Smart year detection: if the date is in the past (more than 30 days), assume next year
        // This handles cases where lesson plans are for future dates
        const currentYear = new Date().getFullYear();
        const currentDate = new Date();
        const testDate = new Date(currentYear, startMonth - 1, startDay);
        
        // If the date is more than 30 days in the past, it's likely for next year
        // (e.g., if today is Dec 2024 and weekOf is "11-20", it's probably Nov 2025)
        const daysDiff = (testDate.getTime() - currentDate.getTime()) / (1000 * 60 * 60 * 24);
        const year = daysDiff < -30 ? currentYear + 1 : currentYear;
        
        mondayDate = new Date(year, startMonth - 1, startDay);
        
        // Log for debugging
        console.log('[LessonMetadataDisplay] Year calculation:', {
          weekOf,
          startMonth,
          startDay,
          currentYear,
          calculatedYear: year,
          daysDiff: Math.round(daysDiff),
          reasoning: daysDiff < -30 ? 'Date is more than 30 days in past, using next year' : 'Using current year'
        });
      }
      
      const dayIndex = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].indexOf(day.toLowerCase());
      if (dayIndex === -1) {
        return null;
      }
      
      const lessonDate = new Date(mondayDate);
      lessonDate.setDate(mondayDate.getDate() + dayIndex);
      
      return lessonDate;
    } catch (error) {
      return null;
    }
  };

  // Determine timing status
  const getTimingStatus = (): 'past' | 'current' | 'future' | null => {
    // Use scheduleStatus from metadata if available
    if (lessonMetadata?.scheduleStatus) {
      return lessonMetadata.scheduleStatus;
    }

    const startTime = lessonMetadata?.start_time || scheduleEntry?.start_time;
    const endTime = lessonMetadata?.end_time || scheduleEntry?.end_time;
    
    if (!startTime || !endTime) {
      return null;
    }

    try {
      const now = new Date(); // Use current time for comparison
      const startTimeParts = startTime.split(':');
      const endTimeParts = endTime.split(':');
      
      if (startTimeParts.length < 2 || endTimeParts.length < 2) {
        return null;
      }
      
      const [startH, startM] = startTimeParts.map(Number);
      const [endH, endM] = endTimeParts.map(Number);
      
      if (isNaN(startH) || isNaN(startM) || isNaN(endH) || isNaN(endM)) {
        return null;
      }

      // Try to get the actual lesson date
      const lessonDate = getLessonDateObject();
      const baseDate = lessonDate || now;

      const start = new Date(baseDate);
      start.setHours(startH, startM, 0, 0);
      
      const end = new Date(baseDate);
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
      return null;
    }
  };

  const timingStatus = getTimingStatus();
  
  // Notify parent of calculated status
  useEffect(() => {
    if (onStatusCalculate) {
      onStatusCalculate(timingStatus);
    }
  }, [timingStatus, onStatusCalculate]);

  // Get color classes based on timing status
  const getMetadataColorClasses = () => {
    switch (timingStatus) {
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

  // Extract values - prefer lessonMetadata, fallback to scheduleEntry
  const subject = lessonMetadata?.subject || scheduleEntry?.subject;
  const grade = lessonMetadata?.grade || scheduleEntry?.grade;
  const homeroom = lessonMetadata?.homeroom || scheduleEntry?.homeroom;
  const startTime = lessonMetadata?.start_time || scheduleEntry?.start_time;
  const endTime = lessonMetadata?.end_time || scheduleEntry?.end_time;
  const dayOfWeek = lessonMetadata?.day_of_week || (day ? getDayName(day) : scheduleEntry?.day_of_week ? getDayName(scheduleEntry.day_of_week) : undefined);
  
  // Get formatted date
  let formattedDate: string | null = null;
  if (lessonMetadata?.formatted_date) {
    formattedDate = lessonMetadata.formatted_date;
  } else {
    const lessonDate = getLessonDateObject();
    formattedDate = lessonDate ? formatDateShort(lessonDate) : null;
  }

  // Don't render if no data
  if (!subject && !grade && !homeroom) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${getMetadataColorClasses()} ${className}`}>
      <div className="text-sm text-muted-foreground flex items-center gap-0 whitespace-nowrap">
        {subject && (
          <span className="font-medium">{subject}</span>
        )}
        {grade && (
          <span className={timingStatus ? 'opacity-90' : ''}>
            {' • '}Grade {grade}
          </span>
        )}
        {homeroom && (
          <span className={timingStatus ? 'opacity-90' : ''}>
            {' • '}{homeroom}
          </span>
        )}
        {dayOfWeek && (
          <span className={timingStatus ? 'opacity-90' : ''}>
            {' • '}{dayOfWeek}
          </span>
        )}
        {formattedDate && (
          <span className={timingStatus ? 'opacity-90' : ''}>
            {' • '}{formattedDate}
          </span>
        )}
        {startTime && endTime && (
          <span className={timingStatus ? 'opacity-90' : ''}>
            {' • '}{startTime} - {endTime}
          </span>
        )}
      </div>
      {showStatusBadge && (
        <div className={`text-xs px-2 py-0.5 rounded ${
          timingStatus === 'current' 
            ? 'bg-blue-100 text-blue-700' 
            : timingStatus === 'past' 
            ? 'bg-green-100 text-green-700' 
            : timingStatus === 'future'
            ? 'bg-orange-100 text-orange-700'
            : 'bg-gray-100 text-gray-700'
        }`}>
          {timingStatus === 'current' ? 'Live' : timingStatus === 'past' ? 'Past' : timingStatus === 'future' ? 'Upcoming' : 'Unknown'}
        </div>
      )}
    </div>
  );
}

