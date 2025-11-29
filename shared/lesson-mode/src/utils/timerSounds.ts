/**
 * Timer Sound Utilities
 * 
 * Provides non-disruptive audio notifications for timer events:
 * - Warning sound: When time is ending (last 10 seconds)
 * - Completion sound: When timer reaches zero
 * - Start sound: When a new timer starts
 * 
 * Uses Web Audio API to generate simple, clear tones that are informative but not jarring.
 */

// Sound configuration - Following professional UX best practices
const SOUND_CONFIG = {
  warningEarly: {
    frequency: 800, // Hz - Higher pitch for attention
    duration: 150, // ms - Short beep
    type: 'sine' as OscillatorType,
    volume: 0.3, // 30% volume - moderate, non-disruptive
  },
  warning: {
    frequency: 800, // Hz - Higher pitch for attention
    duration: 150, // ms - Short beep
    type: 'sine' as OscillatorType,
    volume: 0.3, // 30% volume - moderate
  },
  warningDouble: {
    frequency: 850, // Hz - Slightly higher pitch for increased urgency
    duration: 100, // ms - Shorter for rapid beeps
    type: 'sine' as OscillatorType,
    volume: 0.35, // 35% volume - slightly louder for final countdown
    gap: 50, // ms gap between double beeps
  },
  completion: {
    frequency: 600, // Hz - Lower, more final tone
    duration: 300, // ms - Slightly longer for completion
    type: 'sine' as OscillatorType,
    volume: 0.4, // 40% volume - slightly louder for completion
  },
  start: {
    frequency: 500, // Hz - Mid-range, pleasant tone
    duration: 100, // ms - Very short
    type: 'sine' as OscillatorType,
    volume: 0.25, // 25% volume - subtle
  },
};

// Track if sounds are enabled (user preference)
let soundsEnabled = true;
let audioContext: AudioContext | null = null;

/**
 * Initialize audio context (lazy initialization)
 */
function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  
  try {
    if (!audioContext) {
      audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    // Resume context if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }
    return audioContext;
  } catch (error) {
    console.warn('[TimerSounds] Audio context not available:', error);
    return null;
  }
}

/**
 * Play a simple tone using Web Audio API
 */
function playTone(
  frequency: number,
  duration: number,
  type: OscillatorType = 'sine',
  volume: number = 0.3
): void {
  if (!soundsEnabled) return;
  
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = type;

    // Envelope for smooth sound (avoid clicks)
    const now = ctx.currentTime;
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(volume, now + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration / 1000);

    oscillator.start(now);
    oscillator.stop(now + duration / 1000);
  } catch (error) {
    console.warn('[TimerSounds] Error playing tone:', error);
  }
}

/**
 * Play early warning sound (for 30s, 20s, 15s markers)
 * Called at strategic intervals for longer timers
 */
export function playEarlyWarningSound(): void {
  const config = SOUND_CONFIG.warningEarly;
  playTone(config.frequency, config.duration, config.type, config.volume);
}

/**
 * Play warning sound (time ending)
 * Called when timer has 10 seconds or less remaining
 */
export function playWarningSound(): void {
  const config = SOUND_CONFIG.warning;
  playTone(config.frequency, config.duration, config.type, config.volume);
}

/**
 * Play double warning beep (for final 5 seconds)
 * Two quick beeps per second
 */
export function playWarningDoubleSound(): void {
  const config = SOUND_CONFIG.warningDouble;
  const ctx = getAudioContext();
  if (!ctx || !soundsEnabled) return;

  try {
    // First beep
    playTone(config.frequency, config.duration, config.type, config.volume);
    
    // Second beep after gap
    setTimeout(() => {
      playTone(config.frequency, config.duration, config.type, config.volume);
    }, config.duration + config.gap);
  } catch (error) {
    console.warn('[TimerSounds] Error playing double warning:', error);
  }
}

/**
 * Play completion sound (time ended)
 * Called when timer reaches zero
 */
export function playCompletionSound(): void {
  const config = SOUND_CONFIG.completion;
  playTone(config.frequency, config.duration, config.type, config.volume);
}

/**
 * Play start sound (new time started)
 * Called when timer starts counting
 */
export function playStartSound(): void {
  const config = SOUND_CONFIG.start;
  playTone(config.frequency, config.duration, config.type, config.volume);
}

/**
 * Enable or disable sounds
 */
export function setSoundsEnabled(enabled: boolean): void {
  soundsEnabled = enabled;
}

/**
 * Check if sounds are enabled
 */
export function areSoundsEnabled(): boolean {
  return soundsEnabled;
}

/**
 * Preload audio context (call on user interaction to avoid autoplay restrictions)
 */
export function preloadAudio(): void {
  getAudioContext();
}

