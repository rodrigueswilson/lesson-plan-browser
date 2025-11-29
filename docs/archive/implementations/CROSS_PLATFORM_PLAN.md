# Cross-Platform App Development Plan

## Goal
Add Android tablet support to the existing desktop app, sharing most code between PC and Android versions.

## Current Situation
- Desktop app: Tauri + React + TypeScript (Windows)
- Backend: FastAPI (Python)
- Frontend: React components in `frontend/src/`
- API layer already detects platform (Tauri vs browser)

## Approach: Capacitor for Android
- Reuses existing React code
- Minimal changes needed
- Works with current Vite setup
- Easy to build Android APK

## Step-by-Step Plan

### Phase 1: Setup Platform Detection (30 minutes)

**1.1 Create platform utility**
- File: `frontend/src/lib/platform.ts`
- Purpose: Detect if running on desktop (Tauri) or mobile (Capacitor)
- Code: Simple checks for `__TAURI_INTERNALS__` and `Capacitor` objects

**1.2 Update existing API detection**
- File: `frontend/src/lib/api.ts`
- Change: Use new platform utility instead of inline checks
- Benefit: Centralized platform detection

### Phase 2: Install Capacitor (15 minutes)

**2.1 Install Capacitor packages**
- Run: `npm install @capacitor/core @capacitor/cli @capacitor/android`
- Location: `frontend/` directory
- Purpose: Add Android support

**2.2 Initialize Capacitor**
- Run: `npx cap init`
- Configure: App ID, app name, web directory
- Creates: `capacitor.config.ts`

**2.3 Add Android platform**
- Run: `npx cap add android`
- Creates: `android/` folder with native Android project

### Phase 3: Organize Code Structure (1 hour)

**3.1 Create platform-specific folders**
- Create: `frontend/src/components/desktop/` (for desktop-only components)
- Create: `frontend/src/components/mobile/` (for mobile-only components)
- Keep: `frontend/src/components/` for shared components

**3.2 Create layout components**
- File: `frontend/src/components/layouts/DesktopLayout.tsx`
  - Wraps current desktop UI structure
  - Uses existing header/footer from `App.tsx`
  
- File: `frontend/src/components/layouts/MobileLayout.tsx`
  - Mobile-optimized layout
  - Bottom navigation for Android
  - Touch-friendly spacing

**3.3 Update main App component**
- File: `frontend/src/App.tsx`
- Change: Detect platform and render appropriate layout
- Keep: All existing components (they'll work on both platforms)

### Phase 4: Mobile-Specific Features (2 hours)

**4.1 Mobile navigation**
- File: `frontend/src/components/mobile/MobileNav.tsx`
- Features: Bottom tab bar for Android
- Tabs: Home, Plans, History, Settings

**4.2 Touch optimizations**
- Update: Button sizes in shared components
- Add: Touch-friendly spacing (min 44px touch targets)
- File: `frontend/src/index.css` - add mobile-specific styles

**4.3 Android back button handling**
- File: `frontend/src/lib/mobile.ts`
- Purpose: Handle Android hardware back button
- Uses: Capacitor App plugin

### Phase 5: Build Configuration (1 hour)

**5.1 Update package.json scripts**
- File: `frontend/package.json`
- Add scripts:
  - `dev:desktop` - Run Tauri desktop app
  - `dev:mobile` - Run Capacitor Android app
  - `build:mobile` - Build for Android
  - `cap:sync` - Sync web code to Android

**5.2 Configure Capacitor**
- File: `frontend/capacitor.config.ts`
- Set: Backend API URL (localhost for dev, production URL for release)
- Configure: App ID, app name, web directory

**5.3 Android build setup**
- File: `android/app/build.gradle` (auto-generated)
- Configure: Minimum SDK version, target SDK
- Set: App icon, splash screen

### Phase 6: Testing & Refinement (2 hours)

**6.1 Test shared components**
- Verify: UserSelector works on mobile
- Verify: SlotConfigurator is touch-friendly
- Verify: PlanHistory displays correctly

**6.2 Test mobile-specific features**
- Test: Bottom navigation
- Test: Android back button
- Test: Touch interactions

**6.3 Responsive design adjustments**
- Update: Tailwind classes for mobile breakpoints
- Ensure: Forms are mobile-friendly
- Check: Tables/lists scroll properly

## File Structure After Changes

```
frontend/
├── src/
│   ├── components/
│   │   ├── shared/              # Works on both platforms
│   │   │   ├── UserSelector.tsx
│   │   │   ├── SlotConfigurator.tsx
│   │   │   ├── BatchProcessor.tsx
│   │   │   ├── PlanHistory.tsx
│   │   │   └── Analytics.tsx
│   │   │
│   │   ├── layouts/
│   │   │   ├── DesktopLayout.tsx
│   │   │   └── MobileLayout.tsx
│   │   │
│   │   ├── desktop/              # Desktop-only
│   │   │   └── DesktopNav.tsx (if needed)
│   │   │
│   │   └── mobile/               # Mobile-only
│   │       └── MobileNav.tsx
│   │
│   ├── lib/
│   │   ├── platform.ts          # NEW: Platform detection
│   │   ├── mobile.ts            # NEW: Mobile utilities
│   │   └── api.ts               # UPDATE: Use platform.ts
│   │
│   └── App.tsx                  # UPDATE: Platform detection
│
├── android/                      # NEW: Android native project
├── capacitor.config.ts          # NEW: Capacitor config
└── package.json                 # UPDATE: Add scripts
```

## Development Workflow

**For Desktop Development:**
```bash
cd frontend
npm run dev:desktop  # Runs Tauri desktop app
```

**For Android Development:**
```bash
cd frontend
npm run build        # Build React app
npm run cap:sync     # Sync to Android
npm run dev:mobile   # Open Android Studio
```

## What Stays the Same

- All backend code (no changes needed)
- Most React components (work on both platforms)
- API layer (already platform-agnostic)
- State management (Zustand works everywhere)
- TailwindCSS styling (responsive by default)

## What's New

- Platform detection utility
- Mobile layout component
- Android native project folder
- Capacitor configuration
- Mobile-specific navigation

## Estimated Time
- Setup: 1-2 hours
- Code organization: 2-3 hours
- Mobile features: 2-3 hours
- Testing: 2-3 hours
- **Total: 7-11 hours** (spread over several days)

## Prerequisites
- Node.js installed
- Android Studio installed (for building Android app)
- Java JDK installed (required by Android Studio)

## Implementation Tasks

1. Create platform.ts utility to detect desktop vs mobile platform
2. Install Capacitor packages and initialize Android platform
3. Create platform-specific component folders and layout components
4. Update App.tsx to use platform detection and render appropriate layout
5. Create mobile navigation component with bottom tab bar
6. Create mobile.ts with Android back button handling
7. Add npm scripts for desktop and mobile development
8. Configure capacitor.config.ts with app settings and API URLs
9. Test that shared components work correctly on mobile
10. Make responsive design adjustments for mobile/tablet screens

## Next Steps After This Plan
1. Test on Android tablet
2. Add mobile-specific features (gestures, notifications)
3. Optimize for tablet screen sizes
4. Create Android app icon and splash screen
5. Build release APK for distribution

