import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { getPlatform } from './platform';

describe('Platform Detection', () => {
  let originalWindow: Window & typeof globalThis;

  beforeEach(() => {
    // Save original window
    originalWindow = global.window;
    vi.resetModules();
  });

  afterEach(() => {
    // Restore original window
    global.window = originalWindow;
    vi.resetModules();
  });

  describe('getPlatform', () => {
    it('should detect desktop platform when Tauri is present', () => {
      // Mock Tauri environment
      (global as any).window = {
        __TAURI_INTERNALS__: {},
      };

      expect(getPlatform()).toBe('desktop');
    });

    it('should detect mobile platform when Capacitor is present', () => {
      // Mock Capacitor environment
      (global as any).window = {
        Capacitor: {},
      };

      expect(getPlatform()).toBe('mobile');
    });

    it('should detect web platform when neither Tauri nor Capacitor is present', () => {
      // Mock web environment
      (global as any).window = {};

      expect(getPlatform()).toBe('web');
    });

    it('should prioritize Tauri over Capacitor', () => {
      // Mock both environments (Tauri should take precedence)
      (global as any).window = {
        __TAURI_INTERNALS__: {},
        Capacitor: {},
      };

      expect(getPlatform()).toBe('desktop');
    });

    it('should return web when window is undefined', () => {
      delete (global as any).window;
      expect(getPlatform()).toBe('web');
    });
  });

  describe('Platform checks', () => {
    it('isDesktop should be true when platform is desktop', async () => {
      (global as any).window = {
        __TAURI_INTERNALS__: {},
      };
      // Re-import to get fresh values
      const platformModule = await import('./platform');
      expect(platformModule.isDesktop).toBe(true);
    });

    it('isMobile should be true when platform is mobile', async () => {
      (global as any).window = {
        Capacitor: {},
      };
      const platformModule = await import('./platform');
      expect(platformModule.isMobile).toBe(true);
    });

    it('isWeb should be true when platform is web', async () => {
      (global as any).window = {};
      const platformModule = await import('./platform');
      expect(platformModule.isWeb).toBe(true);
    });

    it('isNative should be true for desktop or mobile', async () => {
      (global as any).window = {
        __TAURI_INTERNALS__: {},
      };
      const platformModule = await import('./platform');
      expect(platformModule.isNative).toBe(true);
    });
  });
});

