import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock Capacitor App
const mockAddListener = vi.fn();
const mockRemoveAllListeners = vi.fn();
const mockExitApp = vi.fn();

vi.mock('@capacitor/app', () => ({
  App: {
    addListener: mockAddListener,
    removeAllListeners: mockRemoveAllListeners,
    exitApp: mockExitApp,
  },
}));

describe('Mobile Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    // Clear window
    delete (global as any).window;
  });

  describe('setupBackButton', () => {
    it('should not setup listener when not on mobile', async () => {
      // Ensure window is undefined or doesn't have Capacitor
      delete (global as any).window;
      
      const { setupBackButton } = await import('./mobile');
      
      setupBackButton();
      
      expect(mockAddListener).not.toHaveBeenCalled();
    });

    it('should setup listener when on mobile', async () => {
      // Mock mobile environment
      (global as any).window = {
        Capacitor: {},
      };

      const { setupBackButton } = await import('./mobile');
      
      setupBackButton();
      
      expect(mockAddListener).toHaveBeenCalledWith('backButton', expect.any(Function));
    });

    it('should call callback when provided', async () => {
      (global as any).window = {
        Capacitor: {},
      };

      const { setupBackButton } = await import('./mobile');
      
      const mockCallback = vi.fn(() => true);
      
      setupBackButton(mockCallback);
      
      // Get the listener callback
      const listenerCall = mockAddListener.mock.calls[0];
      const listenerCallback = listenerCall[1];
      
      // Simulate back button press
      listenerCallback({ canGoBack: true });
      
      expect(mockCallback).toHaveBeenCalled();
    });

    it('should exit app when canGoBack is false', async () => {
      (global as any).window = {
        Capacitor: {},
      };

      const { setupBackButton } = await import('./mobile');
      
      setupBackButton();
      
      const listenerCall = mockAddListener.mock.calls[0];
      const listenerCallback = listenerCall[1];
      
      // Simulate back button press with canGoBack = false
      listenerCallback({ canGoBack: false });
      
      expect(mockExitApp).toHaveBeenCalled();
    });
  });

  describe('removeBackButtonListener', () => {
    it('should not remove listeners when not on mobile', async () => {
      delete (global as any).window;
      
      const { removeBackButtonListener } = await import('./mobile');
      
      removeBackButtonListener();
      
      expect(mockRemoveAllListeners).not.toHaveBeenCalled();
    });

    it('should remove listeners when on mobile', async () => {
      (global as any).window = {
        Capacitor: {},
      };

      const { removeBackButtonListener } = await import('./mobile');
      
      removeBackButtonListener();
      
      expect(mockRemoveAllListeners).toHaveBeenCalled();
    });
  });
});

