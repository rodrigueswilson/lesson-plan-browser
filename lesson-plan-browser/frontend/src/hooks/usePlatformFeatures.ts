import { isDesktop, isMobile } from '../lib/platform';

/**
 * Feature gating hook based on platform detection
 * Returns flags indicating which features should be available on the current platform
 */
export function usePlatformFeatures() {
  return {
    isTablet: isMobile,
    isPC: isDesktop,
    showNavigation: isDesktop,
    showScheduleEditor: isDesktop,
    showAnalytics: isDesktop,
    showPlanHistory: isDesktop,
    showBatchProcessor: isDesktop,
    showSlotConfigurator: isDesktop,
    showBrowser: true, // Available on both
    showLessonMode: true, // Available on both
  };
}

