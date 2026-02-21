import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import {
  playStartSound,
  preloadAudio,
} from '../utils/timerSounds';

// Detect if running on Android tablet
// Use same detection method as API client for consistency
const isTablet = () => {
  if (typeof window === 'undefined') return false;
  
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
  
  // Check if running in Tauri
  const isTauri =
    '__TAURI_INTERNALS__' in window ||
    '__TAURI__' in window ||
    (window as any).__TAURI_INTERNALS__ !== undefined ||
    (window as any).__TAURI__ !== undefined;
  
  // Check if Android
  const isAndroid =
    userAgent.includes('Android') ||
    userAgent.includes('android') ||
    /Android/i.test(userAgent);
  
  // Return true only if both Tauri AND Android (tablet app)
  return isAndroid && isTauri;
};

interface TimerDisplayProps {
  totalDuration: number; // seconds
  remainingTime: number; // seconds
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onAdjust?: () => void; // New: callback to open adjustment dialog
  onTimeAdjust?: (newRemainingTime: number) => void; // Callback when time is adjusted via drag
  isSynced?: boolean; // New: whether timer is synced with actual time
  originalDuration?: number; // New: original duration before adjustments
  maxDuration?: number; // Maximum duration allowed when dragging (defaults to totalDuration * 2)
  onComplete?: () => void; // Callback when timer reaches zero
}

export function TimerDisplay({
  totalDuration,
  remainingTime,
  isRunning,
  onStart,
  onStop,
  onReset,
  onAdjust,
  onTimeAdjust,
  isSynced = false,
  originalDuration,
  maxDuration,
  onComplete,
}: TimerDisplayProps) {
  // Use remainingTime directly instead of maintaining separate displayTime
  // Only use local displayTime for dragging adjustments
  const [displayTime, setDisplayTime] = useState(remainingTime);
  const [isDragging, setIsDragging] = useState(false);
  const [dragValue, setDragValue] = useState(0);
  const [isBlinking, setIsBlinking] = useState(false);
  const [shouldBlink, setShouldBlink] = useState(false);
  const previousShouldBlinkRef = useRef<boolean>(false);
  // Removed countdownRef - we use remainingTime from useLessonTimer hook directly
  const progressBarRef = useRef<HTMLDivElement>(null);
  const blinkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentRemainingTimeRef = useRef<number>(0);
  const isRunningRef = useRef<boolean>(false);
  const wasBlinkingRef = useRef<boolean>(false);
  const buttonsContainerRef = useRef<HTMLDivElement>(null);
  const lastSpaceLimitedStateRef = useRef<boolean | null>(null);
  const isTabletDevice = isTablet();
  const previousRemainingRef = useRef(remainingTime);
  const completedRef = useRef(false); // Track if onComplete has been called for current step
  const wasRunningRef = useRef(isRunning);
  const displayTimeRef = useRef(displayTime); // Track current displayTime for sync logic
  
  // Keep ref in sync with state
  useEffect(() => {
    displayTimeRef.current = displayTime;
  }, [displayTime]);
  
  // Use remainingTime as the source of truth when not dragging
  const effectiveDisplayTime = isDragging ? displayTime : remainingTime;
  
  // Debug logging - Platform detection
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userAgent = navigator.userAgent || '';
      const isTauri = '__TAURI_INTERNALS__' in window || '__TAURI__' in window;
      const hasAndroid = userAgent.includes('Android') || /Android/i.test(userAgent);
      console.log('[TimerDisplay] Platform detection:', {
        isTabletDevice,
        userAgent: userAgent.substring(0, 100),
        isTauri,
        hasAndroid,
        timestamp: new Date().toISOString(),
      });
    }
  }, [isTabletDevice]);

  // Debug logging - Timer state changes
  useEffect(() => {
    console.log('[TimerDisplay] Props received:', {
      remainingTime,
      isRunning,
      totalDuration,
      effectiveDisplayTime,
      isDragging,
      timestamp: new Date().toISOString(),
    });
  }, [remainingTime, isRunning, totalDuration, effectiveDisplayTime, isDragging]);

  useEffect(() => {
    if (isDragging) {
      return;
    }
    const previous = previousRemainingRef.current;
    
    console.log('[TimerDisplay] remainingTime changed:', {
      previous,
      current: remainingTime,
      isRunning,
      wasRunning: wasRunningRef.current,
      timestamp: new Date().toISOString(),
    });
    
    previousRemainingRef.current = remainingTime;
    wasRunningRef.current = isRunning;

    // Reset completed flag when remainingTime increases (new step started)
    if (remainingTime > previous) {
      completedRef.current = false;
      console.log('[TimerDisplay] New step detected - reset completed flag');
    }

    // Sync displayTime only when dragging ends or when remainingTime increases (new step)
    // When not dragging, we use remainingTime directly via effectiveDisplayTime
    if (!isDragging) {
      // Only sync when remainingTime increases (new step) to reset displayTime for next drag
      if (remainingTime > previous) {
        console.log('[TimerDisplay] Syncing displayTime for new step:', remainingTime);
        setDisplayTime(remainingTime);
      }
    }
  }, [remainingTime, isRunning, isDragging]);

  // Watch for remainingTime transitioning from >0 to 0 to trigger onComplete
  useEffect(() => {
    const previous = previousRemainingRef.current;
    
    // Call onComplete when remainingTime transitions from >0 to exactly 0
    if (previous > 0 && remainingTime === 0 && onComplete && !completedRef.current) {
      console.log('[TimerDisplay] remainingTime reached 0, calling onComplete:', {
        previous,
        current: remainingTime,
        hasOnComplete: !!onComplete,
        timestamp: new Date().toISOString(),
      });
      completedRef.current = true;
      onComplete();
    }
    
    previousRemainingRef.current = remainingTime;
  }, [remainingTime, onComplete]);

  // Preload audio on component mount (requires user interaction first)
  useEffect(() => {
    // Preload audio context when component mounts (will be activated on first user interaction)
    const handleFirstInteraction = () => {
      preloadAudio();
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('touchstart', handleFirstInteraction);
    };
    document.addEventListener('click', handleFirstInteraction, { once: true });
    document.addEventListener('touchstart', handleFirstInteraction, { once: true });
    
    return () => {
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('touchstart', handleFirstInteraction);
    };
  }, []);

  // Detect when space is limited using best practices:
  // Measure the buttons container width directly, but use a more lenient threshold
  // Default to showing text - only hide when we're certain space is limited
  useEffect(() => {
    const checkSpace = () => {
      // Default to showing text (space not limited)
      let shouldHideText = false;
      
      if (buttonsContainerRef.current) {
        const containerWidth = buttonsContainerRef.current.offsetWidth;
        
        // Only check if we have a valid measurement (at least 50px to avoid false positives)
        if (containerWidth > 50) {
          // Based on user feedback: 280px worked before
          // But let's be more lenient - use 250px to ensure text shows when there's reasonable space
          // Icon-only buttons: ~48px each (3 buttons = 144px) + gaps (24px) = ~168px
          // Buttons with text: ~100px each (3 buttons = 300px) + gaps (24px) = ~324px
          // So 250px is a good middle ground - if container is wider, show text
          const MIN_WIDTH_FOR_TEXT = 250;
          shouldHideText = containerWidth < MIN_WIDTH_FOR_TEXT;
          
          console.log('[TimerDisplay] Space detection:', {
            containerWidth,
            threshold: MIN_WIDTH_FOR_TEXT,
            shouldHideText,
            willShowText: !shouldHideText,
            currentState: lastSpaceLimitedStateRef.current,
            isTabletDevice
          });
        } else {
          // Container not ready or too small, default to showing text
          console.log('[TimerDisplay] Container not ready, defaulting to show text:', containerWidth);
          shouldHideText = false;
        }
      } else {
        // Ref not ready, default to showing text
        console.log('[TimerDisplay] Ref not ready, defaulting to show text');
        shouldHideText = false;
      }
      
      // Only update ref if it actually changed (prevent unnecessary re-renders)
      if (lastSpaceLimitedStateRef.current !== shouldHideText) {
        console.log('[TimerDisplay] Space state changed:', {
          from: lastSpaceLimitedStateRef.current,
          to: shouldHideText
        });
        
        lastSpaceLimitedStateRef.current = shouldHideText;
      }
    };

    // Initial check immediately and after delays to ensure container is rendered
    checkSpace(); // Check immediately
    
    const timeoutId1 = setTimeout(() => {
      requestAnimationFrame(checkSpace);
    }, 100);
    
    const timeoutId2 = setTimeout(() => {
      requestAnimationFrame(checkSpace);
    }, 500); // Also check after 500ms to catch late renders

    // Use ResizeObserver to watch for container size changes
    let resizeObserver: ResizeObserver | null = null;
    let observerTimeoutId: ReturnType<typeof setTimeout> | null = null;
    
    if (typeof ResizeObserver !== 'undefined') {
      observerTimeoutId = setTimeout(() => {
        if (buttonsContainerRef.current) {
          resizeObserver = new ResizeObserver(() => {
            requestAnimationFrame(checkSpace);
          });
          resizeObserver.observe(buttonsContainerRef.current);
        }
      }, 200);
    }
    
    // Also listen to window resize events as fallback
    let resizeTimeout: ReturnType<typeof setTimeout>;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        requestAnimationFrame(checkSpace);
      }, 150);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      clearTimeout(timeoutId1);
      clearTimeout(timeoutId2);
      if (observerTimeoutId) {
        clearTimeout(observerTimeoutId);
      }
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      if (resizeObserver && buttonsContainerRef.current) {
        resizeObserver.unobserve(buttonsContainerRef.current);
      }
    };
  }, [isTabletDevice]);

  // Update refs with current values
  useEffect(() => {
    currentRemainingTimeRef.current = effectiveDisplayTime;
  }, [effectiveDisplayTime]);

  useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

  // Determine if we should be blinking based on time and running state
  // Only update state when crossing the threshold to avoid restarting the blink loop
  useEffect(() => {
    const newShouldBlink = isRunning && effectiveDisplayTime <= 10 && effectiveDisplayTime > 0;
    if (newShouldBlink !== previousShouldBlinkRef.current) {
      setShouldBlink(newShouldBlink);
      previousShouldBlinkRef.current = newShouldBlink;
    }
  }, [isRunning, effectiveDisplayTime]);

  // Blinking effect for timer display with constant acceleration from 10 to 0
  // This effect only runs when shouldBlink changes (entering/leaving blink zone)
  useEffect(() => {
    // Clear any existing timeout
    if (blinkTimeoutRef.current) {
      clearTimeout(blinkTimeoutRef.current);
      blinkTimeoutRef.current = null;
    }

    if (!shouldBlink) {
      setIsBlinking(false);
      return;
    }

    // Calculate interval with constant acceleration
    // At 10 seconds: 500ms interval, at 0 seconds: 100ms interval
    // Linear acceleration: interval = 100 + 40 * remainingTime
    const calculateInterval = (remaining: number): number => {
      const clampedRemaining = Math.max(0, Math.min(10, remaining));
      return 100 + 40 * clampedRemaining; // 100ms to 500ms
    };

    // Recursive function to schedule next blink with accelerating interval
    const scheduleNextBlink = () => {
      const currentTime = currentRemainingTimeRef.current;
      const currentlyRunning = isRunningRef.current;
      
      // Check if we should still be blinking
      if (!currentlyRunning || currentTime <= 0 || currentTime > 10) {
        setIsBlinking(false);
        return;
      }

      // Toggle blink state
      setIsBlinking((prev) => !prev);

      // Calculate interval based on current remaining time
      const interval = calculateInterval(currentTime);

      // Schedule next blink with updated interval
      blinkTimeoutRef.current = setTimeout(() => {
        scheduleNextBlink();
      }, interval);
    };

    // Start with visible state
    setIsBlinking(false);
    // Start the blinking sequence immediately
    scheduleNextBlink();

    return () => {
      if (blinkTimeoutRef.current) {
        clearTimeout(blinkTimeoutRef.current);
        blinkTimeoutRef.current = null;
      }
    };
  }, [shouldBlink]);

  // Calculate progress based on current totalDuration
  // Use totalDuration as the max so progress bar shows correctly
  // During last 10 seconds, show narrowing effect: 100% at 10s, decreasing to 0% at 0s
  const progress = effectiveDisplayTime <= 10 && effectiveDisplayTime > 0
    ? (effectiveDisplayTime / 10) * 100  // Narrow from 100% to 0% over 10 seconds
    : totalDuration > 0 ? Math.min(100, (effectiveDisplayTime / totalDuration) * 100) : 0;
  
  // Helper function to interpolate between two RGB colors
  const interpolateColor = (color1: [number, number, number], color2: [number, number, number], factor: number): string => {
    const clampedFactor = Math.max(0, Math.min(1, factor));
    const r = Math.round(color1[0] + (color2[0] - color1[0]) * clampedFactor);
    const g = Math.round(color1[1] + (color2[1] - color1[1]) * clampedFactor);
    const b = Math.round(color1[2] + (color2[2] - color1[2]) * clampedFactor);
    return `rgb(${r}, ${g}, ${b})`;
  };

  // Calculate color scheme based on remaining time
  // Green: >20s, Gradual Orange to Red: 20s to 0s
  const getProgressBarColor = (): string => {
    if (effectiveDisplayTime > 20) {
      return '#22c55e'; // Green
    }
    // Gradual transition from orange to red (20s to 0s)
    const factor = 1 - (effectiveDisplayTime / 20); // 0 at 20s, 1 at 0s
    const orange: [number, number, number] = [249, 115, 22]; // #f97316
    const red: [number, number, number] = [239, 68, 68]; // #ef4444
    return interpolateColor(orange, red, factor);
  };

  const getTextColor = (): string => {
    if (effectiveDisplayTime > 20) {
      return '#16a34a'; // Green
    }
    // Gradual transition from orange to red (20s to 0s)
    const factor = 1 - (effectiveDisplayTime / 20); // 0 at 20s, 1 at 0s
    const orange: [number, number, number] = [234, 88, 12]; // #ea580c
    const red: [number, number, number] = [220, 38, 38]; // #dc2626
    return interpolateColor(orange, red, factor);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate time from mouse/touch position - memoized
  // Allow dragging beyond totalDuration to add more time
  const getTimeFromPosition = useCallback((clientX: number): number => {
    if (!progressBarRef.current) return remainingTime;
    
    const rect = progressBarRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    
    // Calculate max duration (allow up to 2x totalDuration or specified maxDuration)
    const effectiveMaxDuration = maxDuration || (totalDuration * 2);
    
    // Left = less time (0%), Right = more time (up to maxDuration)
    // Map percentage: 0% = 0 seconds, 100% = maxDuration
    const newTime = Math.round(effectiveMaxDuration * percentage);
    return Math.max(0, Math.min(effectiveMaxDuration, newTime));
  }, [totalDuration, remainingTime, maxDuration]);

  // Handle drag move (mouse and touch) - memoized
  const handleDragMove = useCallback((clientX: number) => {
    if (!isDragging || !onTimeAdjust) return;
    const newTime = getTimeFromPosition(clientX);
    setDragValue(newTime);
    setDisplayTime(newTime);
  }, [isDragging, onTimeAdjust, getTimeFromPosition]);

  // Handle drag end (mouse and touch) - memoized
  const handleDragEnd = useCallback(() => {
    if (!isDragging || !onTimeAdjust) return;
    const finalValue = dragValue;
    setIsDragging(false);
    if (finalValue !== remainingTime && onTimeAdjust) {
      onTimeAdjust(finalValue);
    }
    setDragValue(0);
  }, [isDragging, dragValue, remainingTime, onTimeAdjust]);

  // Handle drag start (mouse and touch)
  const handleDragStart = useCallback((clientX: number) => {
    if (!onTimeAdjust) return; // Allow dragging even when running
    setIsDragging(true);
    const newTime = getTimeFromPosition(clientX);
    setDragValue(newTime);
    setDisplayTime(newTime);
  }, [onTimeAdjust, getTimeFromPosition]);

  // Mouse event handlers - inline to avoid React type issues
  const handleMouseDown = useCallback((e: { clientX: number; preventDefault: () => void }) => {
    e.preventDefault();
    handleDragStart(e.clientX);
  }, [handleDragStart]);

  // Touch event handlers - inline to avoid React type issues
  const handleTouchStart = useCallback((e: { touches: ArrayLike<{ clientX: number }>; preventDefault: () => void }) => {
    e.preventDefault();
    const touch = e.touches[0];
    if (touch) {
      handleDragStart(touch.clientX);
    }
  }, [handleDragStart]);

  // Add global event listeners for drag
  useEffect(() => {
    if (isDragging && onTimeAdjust) {
      const handleMouseMoveGlobal = (e: MouseEvent) => handleDragMove(e.clientX);
      const handleMouseUpGlobal = () => handleDragEnd();
      const handleTouchMoveGlobal = (e: TouchEvent) => {
        e.preventDefault();
        const touch = e.touches[0];
        if (touch) handleDragMove(touch.clientX);
      };
      const handleTouchEndGlobal = () => handleDragEnd();
      
      document.addEventListener('mousemove', handleMouseMoveGlobal);
      document.addEventListener('mouseup', handleMouseUpGlobal);
      document.addEventListener('touchmove', handleTouchMoveGlobal, { passive: false });
      document.addEventListener('touchend', handleTouchEndGlobal);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMoveGlobal);
        document.removeEventListener('mouseup', handleMouseUpGlobal);
        document.removeEventListener('touchmove', handleTouchMoveGlobal);
        document.removeEventListener('touchend', handleTouchEndGlobal);
      };
    }
  }, [isDragging, handleDragMove, handleDragEnd, onTimeAdjust]);

  return (
    <Card className="p-8 md:p-6">
      <div className="space-y-6 md:space-y-4">
        {/* Progress Bar - Interactive slider - Larger on tablet */}
        <div 
          ref={progressBarRef}
          className={`w-full bg-muted rounded-full h-6 md:h-4 overflow-hidden relative ${
            onTimeAdjust ? 'cursor-pointer hover:opacity-90' : ''
          } ${isDragging ? 'opacity-90' : ''}`}
          onMouseDown={onTimeAdjust ? handleMouseDown : undefined}
          onTouchStart={onTimeAdjust ? handleTouchStart : undefined}
          style={{ touchAction: 'none' }} // Prevent scrolling while dragging on touch devices
        >
          <div
            className={`h-full ${isDragging ? '' : ''}`}
            style={{ 
              width: `${progress}%`,
              backgroundColor: getProgressBarColor(),
              opacity: isBlinking ? 0.3 : 1,
              transition: isDragging ? '' : 'opacity 0.1s ease-in-out, width 0.3s ease-in-out'
            }}
          />
          {isDragging && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-background/90 px-3 py-1 rounded text-sm font-semibold shadow-lg">
                {formatTime(dragValue)}
              </div>
            </div>
          )}
        </div>

        {/* Timer Display - Larger text for tablet */}
        <div className="text-center">
          <div 
            className="text-6xl md:text-4xl font-bold"
            style={{
              color: getTextColor(),
              opacity: isBlinking ? 0.3 : 1,
              transition: 'opacity 0.1s ease-in-out'
            }}
          >
            {formatTime(effectiveDisplayTime)}
          </div>
          <div className="text-base md:text-sm text-muted-foreground mt-2 md:mt-1">
            {isRunning ? 'Running' : 'Paused'}
          </div>
        </div>

        {/* Sync Status */}
        {isSynced && (
          <div className="text-center text-xs text-muted-foreground mb-2">
            Synced with actual time
          </div>
        )}
        {originalDuration && originalDuration !== totalDuration && (
          <div className="text-center text-xs text-muted-foreground mb-2">
            Original: {formatTime(originalDuration)} | Adjusted: {formatTime(totalDuration)}
          </div>
        )}

        {/* Controls - Consistent button sizes on all platforms */}
        <div ref={buttonsContainerRef} className="flex justify-center gap-3">
          {!isRunning ? (
            <Button 
              onClick={() => {
                playStartSound();
                onStart();
              }} 
              size="sm" 
              className="h-12 w-12 p-0"
              title="Start"
            >
              <Play className="w-5 h-5" />
            </Button>
          ) : (
            <Button 
              onClick={onStop} 
              variant="outline" 
              size="sm" 
              className="h-12 w-12 p-0"
              title="Pause"
            >
              <Pause className="w-5 h-5" />
            </Button>
          )}
          <Button 
            onClick={onReset} 
            variant="outline" 
            size="sm" 
            className="h-12 w-12 p-0"
            title="Reset"
          >
            <RotateCcw className="w-5 h-5" />
          </Button>
          {onAdjust && (
            <Button 
              onClick={onAdjust} 
              variant="outline" 
              size="sm" 
              className="h-12 w-12 p-0"
              title="Adjust"
            >
              <Settings className="w-5 h-5" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

