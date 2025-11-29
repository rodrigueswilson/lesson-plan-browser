import { useState, useEffect } from 'react';
import { BookOpen } from 'lucide-react';
import { LessonPlanBrowser, UserSelector, useStore } from '@lesson-browser';
import { SlotConfigurator } from './components/SlotConfigurator';
import { BatchProcessor } from './components/BatchProcessor';
import { PlanHistory } from './components/PlanHistory';
import { Analytics } from './components/Analytics';
import { ScheduleInput } from './components/ScheduleInput';
import { LessonMode } from '@lesson-mode/components/LessonMode';
import { isMobile } from './lib/platform';
import { DesktopLayout } from './components/layouts/DesktopLayout';
import { MobileLayout } from './components/layouts/MobileLayout';
import { setupBackButton } from './lib/mobile';
import { SyncTestButton } from './components/SyncTestButton';

type NavItem = 'home' | 'plans' | 'schedule' | 'browser' | 'lesson-mode' | 'history' | 'analytics' | 'settings';

function AppContent() {
  const { currentUser } = useStore();
  const [activeNavItem, setActiveNavItem] = useState<NavItem>('home');
  const [lessonModeEntry, setLessonModeEntry] = useState<{ scheduleEntry?: any; planId?: string; day?: string; slot?: number } | null>(null);
  const [shouldOpenLesson, setShouldOpenLesson] = useState(false);

  const handleNavigate = (item: NavItem) => {
    console.log('[App] Navigation requested:', item);
    setActiveNavItem(item);
  };

  // Setup Android back button handler
  useEffect(() => {
    if (isMobile) {
      setupBackButton(() => {
        // Handle back button - return false to allow default behavior
        // Return true to prevent default (stay in app)
        return false;
      });

      return () => {
        // Cleanup if needed
      };
    }
  }, []);

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
              <SyncTestButton />
            </section>
            <section>
              <BatchProcessor />
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
                  <SlotConfigurator />
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
                  <ScheduleInput />
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
            <LessonMode
              currentUser={currentUser}
              scheduleEntry={lessonModeEntry?.scheduleEntry}
              planId={lessonModeEntry?.planId}
              day={lessonModeEntry?.day}
              slot={lessonModeEntry?.slot}
              onExit={(exitDay, exitSlot) => {
                // Preserve the lesson mode entry data when exiting
                // Use the day and slot passed back from LessonMode (which were resolved from scheduleEntry)
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
                  <PlanHistory />
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
                  <Analytics />
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

  // Render with appropriate layout based on platform
  if (isMobile) {
    return <MobileLayout>{content}</MobileLayout>;
  }

  return (
    <DesktopLayout 
      activeNavItem={activeNavItem} 
      onNavigate={handleNavigate}
    >
      {content}
    </DesktopLayout>
  );
}

function App() {
  return <AppContent />;
}

export default App;
