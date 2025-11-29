import { ReactNode } from 'react';
import { BookOpen } from 'lucide-react';
import { MobileNav } from '../mobile/MobileNav';

interface MobileLayoutProps {
  children: ReactNode;
}

export function MobileLayout({ children }: MobileLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Mobile Header - Compact */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="px-4 py-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary" />
            <div>
              <h1 className="text-lg font-bold">Lesson Planner</h1>
              <p className="text-xs text-muted-foreground">
                Bilingual weekly plans
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Scrollable */}
      <main className="flex-1 overflow-y-auto px-4 py-4">
        <div className="space-y-6 pb-20">
          {children}
        </div>
      </main>

      {/* Bottom Navigation */}
      <MobileNav />
    </div>
  );
}

