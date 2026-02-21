import { isDesktop, isMobile, isWeb } from '../lib/platform';

/**
 * Feature gating hook based on platform detection
 * Returns flags indicating which features should be available on the current platform
 */
export function usePlatformFeatures() {
  // Web platform should be treated as PC (desktop) for feature access
  const isPC = isDesktop || isWeb;
  
  return {
    isTablet: isMobile,
    isPC: isPC,
    showNavigation: isPC,
    showScheduleEditor: isPC,
    showAnalytics: isPC,
    showPlanHistory: isPC,
    showBatchProcessor: isPC,
    showSlotConfigurator: isPC,
    showBrowser: true, // Available on both
    showLessonMode: true, // Available on both
  };
}

