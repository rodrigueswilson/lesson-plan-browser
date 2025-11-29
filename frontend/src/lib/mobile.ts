/**
 * Mobile-specific utilities
 * Handles Android back button and other mobile features
 */

import { App } from '@capacitor/app';
import { isMobile } from './platform';

/**
 * Setup Android back button handler
 * @param onBackButton - Callback when back button is pressed
 */
export function setupBackButton(onBackButton?: () => boolean | void) {
  if (!isMobile) {
    return;
  }

  App.addListener('backButton', ({ canGoBack }) => {
    if (onBackButton) {
      const handled = onBackButton();
      if (handled === false) {
        // If callback returns false, don't prevent default behavior
        return;
      }
    }

    // If canGoBack is false, exit the app
    if (!canGoBack) {
      App.exitApp();
    }
  });
}

/**
 * Remove back button listener
 */
export function removeBackButtonListener() {
  if (!isMobile) {
    return;
  }

  App.removeAllListeners();
}

