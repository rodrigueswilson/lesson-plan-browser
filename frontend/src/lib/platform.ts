/**
 * Platform detection utility
 * Detects if the app is running on desktop (Tauri), mobile (Capacitor), or web
 */

export type Platform = 'desktop' | 'mobile' | 'web';

/**
 * Detect the current platform
 */
export function getPlatform(): Platform {
  if (typeof window === 'undefined') {
    return 'web';
  }

  // Check for Tauri (desktop)
  if ('__TAURI_INTERNALS__' in window) {
    return 'desktop';
  }

  // Check for Capacitor (mobile)
  if ('Capacitor' in window) {
    return 'mobile';
  }

  return 'web';
}

/**
 * Current platform
 */
export const platform = getPlatform();

/**
 * Platform checks
 */
export const isDesktop = platform === 'desktop';
export const isMobile = platform === 'mobile';
export const isWeb = platform === 'web';

/**
 * Check if running in a native environment (desktop or mobile)
 */
export const isNative = isDesktop || isMobile;

