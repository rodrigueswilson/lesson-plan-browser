import { useState, useEffect, lazy, Suspense } from 'react';
import { BookOpen } from 'lucide-react';
import { LessonPlanBrowser, UserSelector, useStore } from '@lesson-browser';
import { ScheduleEntry } from '@lesson-api';
import { isMobile, isDesktop } from './lib/platform';
import { usePlatformFeatures } from './hooks/usePlatformFeatures';

// Lazy load Lesson Mode for code splitting
const LessonMode = lazy(() => 
  import('@lesson-mode/components/LessonMode').then(module => ({ default: module.LessonMode }))
);

// Lazy load PC-only components (not included in tablet bundle)
// Path: lesson-plan-browser/frontend/src/ -> ../../../frontend/src/ (3 levels up to root, then into frontend)
const ScheduleInput = lazy(() => import('../../../frontend/src/components/ScheduleInput'));
const Analytics = lazy(() => import('../../../frontend/src/components/Analytics'));
const PlanHistory = lazy(() => import('../../../frontend/src/components/PlanHistory'));
const BatchProcessor = lazy(() => import('../../../frontend/src/components/BatchProcessor'));
const SlotConfigurator = lazy(() => import('../../../frontend/src/components/SlotConfigurator'));
const SyncTestButton = lazy(() => import('../../../frontend/src/components/SyncTestButton'));

// Lazy load PC-only layout components
const DesktopLayout = lazy(() => import('../../../frontend/src/components/layouts/DesktopLayout').then(module => ({ default: module.DesktopLayout })));

// Mobile utilities (for Android back button) - optional, may not work with Tauri
let setupBackButton: ((handler: () => boolean) => void) | null = null;
if (isMobile) {
  import('../../../frontend/src/lib/mobile').then((mobileModule) => {
    setupBackButton = mobileModule.setupBackButton;
  }).catch((e) => {
    console.warn('Could not load mobile utilities (may not be available in Tauri):', e);
  });
}

type NavItem = 'home' | 'plans' | 'schedule' | 'browser' | 'lesson-mode' | 'history' | 'analytics' | 'settings';
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
  const features = usePlatformFeatures();

  // Tablet state (browser + lesson mode only)
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

  // PC state (full navigation)
  const [activeNavItem, setActiveNavItem] = useState<NavItem>('home');
  const [lessonModeEntry, setLessonModeEntry] = useState<{ scheduleEntry?: any; planId?: string; day?: string; slot?: number } | null>(null);
  const [shouldOpenLesson, setShouldOpenLesson] = useState(false);

  // Setup Android back button handler (tablet only)
  useEffect(() => {
    if (features.isTablet && setupBackButton) {
      setupBackButton(() => {
        // Handle back button - return false to allow default behavior
        return false;
      });

      return () => {
        // Cleanup if needed
      };
    }
  }, [features.isTablet]);

  // Tablet mode: Browser + Lesson Mode only (no navigation)
  if (features.isTablet) {
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

  // PC mode: Full navigation with all features
  if (features.isPC) {
    const handleNavigate = (item: NavItem) => {
      console.log('[App] Navigation requested:', item);
      setActiveNavItem(item);
    };

    // Render content based on active navigation item
    const renderContent = () => {
      // Always show UserSelector at the top
      const userSelectorSection = (
        <section>
          <UserSelector />
        </section>
      );

      // Show message if no user selected (but still show UserSelector)
      if (!currentUser) {
        return (
          <div className="space-y-8">
            {userSelectorSection}
            <div className="text-center py-16 text-muted-foreground">
              <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Select or create a user to get started</p>
            </div>
          </div>
        );
      }

      switch (activeNavItem) {
        case 'home':
          return (
            <div className="space-y-8">
              {userSelectorSection}
              <section>
                <Suspense fallback={<div className="p-4">Loading...</div>}>
                  <SyncTestButton />
                </Suspense>
              </section>
              <section>
                <Suspense fallback={<div className="p-4">Loading...</div>}>
                  <BatchProcessor />
                </Suspense>
              </section>
            </div>
          );

        case 'plans':
          return (
            <div className="space-y-8">
              {userSelectorSection}
              <section>
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-6 py-4 bg-card border-b">
                    <h2 className="text-lg font-semibold">Class Slots Configuration</h2>
                    <p className="text-sm text-muted-foreground">Configure up to 10 class slots</p>
                  </div>
                  <div className="p-6">
                    <Suspense fallback={<div className="p-4">Loading...</div>}>
                      <SlotConfigurator />
                    </Suspense>
                  </div>
                </div>
              </section>
            </div>
          );

        case 'schedule':
          return (
            <div className="space-y-8">
              {userSelectorSection}
              <section>
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-6 py-4 bg-card border-b">
                    <h2 className="text-lg font-semibold">Schedule Management</h2>
                    <p className="text-sm text-muted-foreground">Input your weekly schedule with subjects, grades, and homerooms</p>
                  </div>
                  <div className="p-6">
                    <Suspense fallback={<div className="p-4">Loading...</div>}>
                      <ScheduleInput />
                    </Suspense>
                  </div>
                </div>
              </section>
            </div>
          );

        case 'browser':
          return (
            <LessonPlanBrowser 
              onEnterLessonMode={(scheduleEntry, day?: string, slot?: number, planId?: string) => {
                setLessonModeEntry({ 
                  scheduleEntry,
                  day,
                  slot,
                  planId,
                });
                setActiveNavItem('lesson-mode');
              }}
              initialLesson={shouldOpenLesson && lessonModeEntry?.scheduleEntry && lessonModeEntry?.day && lessonModeEntry?.slot ? {
                scheduleEntry: lessonModeEntry.scheduleEntry,
                day: lessonModeEntry.day,
                slot: lessonModeEntry.slot,
                planId: lessonModeEntry.planId,
              } : undefined}
            />
          );

        case 'lesson-mode':
          if (!lessonModeEntry?.scheduleEntry && !lessonModeEntry?.planId) {
            return (
              <div className="h-full flex items-center justify-center p-8">
                <div className="text-center">
                  <p className="text-lg text-muted-foreground mb-4">
                    No lesson selected. Please select a lesson from the browser.
                  </p>
                  <button
                    onClick={() => setActiveNavItem('browser')}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Go to Lesson Browser
                  </button>
                </div>
              </div>
            );
          }
          return (
            <div className="h-full">
              <Suspense fallback={
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-lg text-muted-foreground">Loading Lesson Mode...</div>
                  </div>
                </div>
              }>
                <LessonMode
                  currentUser={currentUser}
                  scheduleEntry={lessonModeEntry?.scheduleEntry}
                  planId={lessonModeEntry?.planId}
                  day={lessonModeEntry?.day}
                  slot={lessonModeEntry?.slot}
                  onExit={(exitDay, exitSlot) => {
                    // Preserve the lesson mode entry data when exiting
                    setLessonModeEntry({
                      scheduleEntry: lessonModeEntry?.scheduleEntry,
                      planId: lessonModeEntry?.planId,
                      day: exitDay || lessonModeEntry?.day,
                      slot: exitSlot !== undefined ? exitSlot : lessonModeEntry?.slot,
                    });
                    setShouldOpenLesson(true);
                    setActiveNavItem('browser');
                    // Reset the flag after a short delay to allow the browser to process it
                    setTimeout(() => setShouldOpenLesson(false), 1000);
                  }}
                />
              </Suspense>
            </div>
          );

        case 'history':
          return (
            <div className="space-y-8">
              {userSelectorSection}
              <section>
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-6 py-4 bg-card border-b">
                    <h2 className="text-lg font-semibold">Plan History</h2>
                    <p className="text-sm text-muted-foreground">View past generated lesson plans</p>
                  </div>
                  <div className="p-6">
                    <Suspense fallback={<div className="p-4">Loading...</div>}>
                      <PlanHistory />
                    </Suspense>
                  </div>
                </div>
              </section>
            </div>
          );

        case 'analytics':
          return (
            <div className="space-y-8">
              {userSelectorSection}
              <section>
                <div className="border rounded-lg overflow-hidden">
                  <div className="px-6 py-4 bg-card border-b">
                    <h2 className="text-lg font-semibold">Analytics Dashboard</h2>
                    <p className="text-sm text-muted-foreground">Performance metrics and usage statistics</p>
                  </div>
                  <div className="p-6">
                    <Suspense fallback={<div className="p-4">Loading...</div>}>
                      <Analytics />
                    </Suspense>
                  </div>
                </div>
              </section>
            </div>
          );

        default:
          return (
            <div className="text-center py-16 text-muted-foreground">
              <p className="text-lg">Page not found</p>
            </div>
          );
      }
    };

    const content = renderContent();

    return (
      <Suspense fallback={
        <div className="h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg text-muted-foreground">Loading...</div>
          </div>
        </div>
      }>
        <DesktopLayout 
          activeNavItem={activeNavItem} 
          onNavigate={handleNavigate}
        >
          {content}
        </DesktopLayout>
      </Suspense>
    );
  }

  // Fallback (should not reach here, but handle gracefully)
  return (
    <div className="h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-lg text-muted-foreground">Platform not detected</p>
      </div>
    </div>
  );
}

export default App;
