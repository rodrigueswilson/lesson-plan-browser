import { ReactNode } from 'react';
import { BookOpen } from 'lucide-react';
import { DesktopNav } from '../desktop/DesktopNav';

type NavItem = 'home' | 'plans' | 'schedule' | 'browser' | 'lesson-mode' | 'history' | 'analytics' | 'settings';

interface DesktopLayoutProps {
  children: ReactNode;
  activeNavItem?: NavItem;
  onNavigate?: (item: NavItem) => void;
  availableNavItems?: NavItem[]; // Optional filter for available navigation items
}

export function DesktopLayout({ 
  children, 
  activeNavItem = 'home',
  onNavigate,
  availableNavItems
}: DesktopLayoutProps) {
  // Browser mode uses full screen with compact navigation
  const isBrowserMode = activeNavItem === 'browser' || activeNavItem === 'lesson-mode';
  
  return (
    <div className={`${isBrowserMode ? 'h-screen' : 'min-h-screen'} bg-background flex overflow-hidden`}>
      {/* Sidebar Navigation - Compact when Browser is active */}
      {onNavigate && (
        <DesktopNav 
          activeItem={activeNavItem} 
          onNavigate={onNavigate}
          compact={isBrowserMode}
          availableNavItems={availableNavItems}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Header - Hidden in Browser mode */}
        {!isBrowserMode && (
          <header className="border-b bg-card flex-shrink-0">
            <div className="px-6 py-4">
              <div className="flex items-center gap-3">
                <BookOpen className="w-8 h-8 text-primary" />
                <div>
                  <h1 className="text-2xl font-bold">Bilingual Lesson Planner</h1>
                  <p className="text-sm text-muted-foreground">
                    Weekly lesson plan generator with WIDA support
                  </p>
                </div>
              </div>
            </div>
          </header>
        )}

        {/* Main Content - Full screen in Browser mode */}
        <main className={`flex-1 min-h-0 ${isBrowserMode ? 'overflow-hidden h-full' : 'overflow-y-auto container mx-auto px-6 py-8'}`}>
          {children}
        </main>

        {/* Footer - Hidden in Browser mode */}
        {!isBrowserMode && (
          <footer className="border-t bg-card">
            <div className="px-6 py-4 text-center text-sm text-muted-foreground">
              Bilingual Lesson Planner v1.0.0
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}

