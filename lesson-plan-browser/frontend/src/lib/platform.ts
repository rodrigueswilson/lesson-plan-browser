/**
 * Platform detection utility
 * Detects if the app is running on desktop (Tauri), mobile (Android Tauri or Capacitor), or web
 */

export type Platform = 'desktop' | 'mobile' | 'web';

/**
 * Detect the current platform
 */
export function getPlatform(): Platform {
  if (typeof window === 'undefined') {
    return 'web';
  }

  // Check for Tauri (can be desktop or Android)
  const isTauri = '__TAURI_INTERNALS__' in window || '__TAURI__' in window;
  
  if (isTauri) {
    // Distinguish Android Tauri from Desktop Tauri
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
    const isAndroid = userAgent.includes('Android') || /Android/i.test(userAgent);
    
    if (isAndroid) {
      return 'mobile'; // Android Tauri
    }
    return 'desktop'; // Desktop Tauri
  }

  // Check for Capacitor (not used, but keep for completeness)
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

