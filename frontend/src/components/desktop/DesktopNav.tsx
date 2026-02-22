import { Home, FileText, Calendar, History, BookOpen, Settings, Tablet } from 'lucide-react';
import { clsx } from 'clsx';

type NavItem = 'home' | 'plans' | 'schedule' | 'browser' | 'lesson-mode' | 'history' | 'analytics' | 'settings' | 'database' | 'tablet';

interface DesktopNavProps {
  activeItem: NavItem;
  onNavigate: (item: NavItem) => void;
  compact?: boolean;
  availableNavItems?: NavItem[]; // Optional filter for available navigation items
}

export function DesktopNav({ activeItem, onNavigate, compact = false, availableNavItems }: DesktopNavProps) {
  const allNavItems = [
    { id: 'home' as NavItem, label: 'Home', icon: Home },
    { id: 'plans' as NavItem, label: 'Lesson Plans', icon: FileText },
    { id: 'schedule' as NavItem, label: 'Schedule', icon: Calendar },
    { id: 'browser' as NavItem, label: 'Browser', icon: BookOpen },
    { id: 'history' as NavItem, label: 'History', icon: History },
    { id: 'settings' as NavItem, label: 'Settings', icon: Settings },
    { id: 'tablet' as NavItem, label: 'Tablet', icon: Tablet },
  ];

  // Filter nav items if availableNavItems is provided
  const navItems = availableNavItems
    ? allNavItems.filter(item => availableNavItems.includes(item.id))
    : allNavItems;

  if (compact) {
    // Compact icon-only navigation for Browser mode
    return (
      <nav className="border-r bg-card w-16 min-h-screen flex flex-col">
        {/* Logo/Header - Icon only */}
        <div className="p-3 border-b flex justify-center">
          <FileText className="w-6 h-6 text-primary" />
        </div>

        {/* Navigation Items - Icon only */}
        <div className="flex-1 p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeItem === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  console.log('[DesktopNav] Navigation clicked:', item.id);
                  onNavigate(item.id);
                }}
                className={clsx(
                  'w-full flex items-center justify-center p-3 rounded-lg transition-colors cursor-pointer',
                  'hover:bg-muted',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                )}
                type="button"
                title={item.label}
              >
                <Icon className="w-5 h-5" />
              </button>
            );
          })}
        </div>

        {/* Footer/Version - Hidden in compact mode */}
      </nav>
    );
  }

  // Full navigation (default)
  return (
    <nav className="border-r bg-card w-64 min-h-screen flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          <span className="font-bold text-lg">Lesson Planner</span>
        </div>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;

          return (
            <button
              key={item.id}
              onClick={() => {
                console.log('[DesktopNav] Navigation clicked:', item.id);
                onNavigate(item.id);
              }}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left cursor-pointer',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
              type="button"
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Footer/Version */}
      <div className="p-4 border-t text-xs text-muted-foreground text-center">
        v1.0.0
      </div>
    </nav>
  );
}

