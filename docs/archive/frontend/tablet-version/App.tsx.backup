import { useState, lazy, Suspense } from 'react';
import { LessonPlanBrowser, UserSelector, useStore } from '@lesson-browser';
import { ScheduleEntry } from '@lesson-api';

// Lazy load Lesson Mode for code splitting (only loads when needed)
// This reduces initial bundle size - Lesson Mode components only load when user enters Lesson Mode
const LessonMode = lazy(() => 
  import('@lesson-mode/components/LessonMode').then(module => ({ default: module.LessonMode }))
);

type View = 'browser' | 'lesson-mode';

interface LessonModeProps {
  scheduleEntry: ScheduleEntry;
  day?: string;
  slot?: number;
  planId?: string;
  weekOf?: string;
}

function App() {
  const { currentUser } = useStore();
  const [view, setView] = useState<View>('browser');
  const [lessonModeProps, setLessonModeProps] = useState<LessonModeProps | null>(null);
  const [exitDay, setExitDay] = useState<string | undefined>(undefined);
  const [previousViewInfo, setPreviousViewInfo] = useState<{
    viewMode: 'week' | 'day' | 'lesson';
    lessonInfo?: {
      scheduleEntry: ScheduleEntry;
      day: string;
      slot: number;
    };
  } | null>(null);

  const handleEnterLessonMode = (
    scheduleEntry: ScheduleEntry,
    day?: string,
    slot?: number,
    planId?: string,
    previousViewMode?: 'week' | 'day' | 'lesson',
    weekOf?: string
  ) => {
    // Store previous view info if we came from lesson view
    if (previousViewMode === 'lesson' && day && slot) {
      setPreviousViewInfo({
        viewMode: 'lesson',
        lessonInfo: {
          scheduleEntry,
          day,
          slot,
        },
      });
    } else if (previousViewMode) {
      // Store just the view mode for week/day views
      setPreviousViewInfo({
        viewMode: previousViewMode,
      });
    } else {
      // Default: assume we came from day view if no info provided
      setPreviousViewInfo({
        viewMode: 'day',
      });
    }

    setLessonModeProps({
      scheduleEntry,
      day,
      slot,
      planId,
      weekOf,
    });
    setView('lesson-mode');
  };

  const handleExitLessonMode = (day?: string, slot?: number) => {
    console.log('[App] Exiting lesson mode, previousViewInfo:', previousViewInfo);
    
    // If we came from lesson view, restore it using initialLesson (don't set exitDay)
    if (previousViewInfo?.viewMode === 'lesson' && previousViewInfo.lessonInfo) {
      // Don't set exitDay - initialLesson will handle restoring the lesson view
      setExitDay(undefined);
      setTimeout(() => {
        setView('browser');
        // Clear after processing
        setTimeout(() => {
          setPreviousViewInfo(null);
        }, 1000);
      }, 10);
    } else {
      // Otherwise, go to day view (or week view if that's what we came from)
      if (previousViewInfo?.viewMode === 'week') {
        setExitDay(undefined); // No day means week view
      } else {
        setExitDay(day); // Default to day view
      }
      setTimeout(() => {
        setView('browser');
        setTimeout(() => {
          setExitDay(undefined);
          setPreviousViewInfo(null);
        }, 1000);
      }, 10);
    }
  };

  // Show user selector if no user selected
  if (!currentUser) {
    return (
      <div className="min-h-screen p-4">
        <div className="max-w-md mx-auto mt-8">
          <UserSelector />
        </div>
      </div>
    );
  }

  // Render current view
  if (view === 'lesson-mode' && lessonModeProps) {
    return (
      <div className="h-screen w-full">
        <Suspense fallback={
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-lg text-muted-foreground">Loading Lesson Mode...</div>
            </div>
          </div>
        }>
          <LessonMode
            currentUser={currentUser}
            scheduleEntry={lessonModeProps.scheduleEntry}
            planId={lessonModeProps.planId}
            day={lessonModeProps.day}
            slot={lessonModeProps.slot}
            weekOf={lessonModeProps.weekOf}
            onExit={handleExitLessonMode}
          />
        </Suspense>
      </div>
    );
  }

  // Browser view (default)
  return (
    <div className="h-screen w-full">
      <LessonPlanBrowser
        onEnterLessonMode={handleEnterLessonMode}
        onExitLessonMode={handleExitLessonMode}
        showLessonModeButton={view === 'lesson-mode'}
        initialDay={exitDay}
        initialLesson={
          previousViewInfo?.viewMode === 'lesson' && previousViewInfo.lessonInfo
            ? {
                scheduleEntry: previousViewInfo.lessonInfo.scheduleEntry,
                day: previousViewInfo.lessonInfo.day,
                slot: previousViewInfo.lessonInfo.slot,
              }
            : null
        }
      />
    </div>
  );
}

export default App;
