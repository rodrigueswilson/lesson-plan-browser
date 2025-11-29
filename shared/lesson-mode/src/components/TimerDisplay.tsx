import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { Card } from '@lesson-ui/Card';
import { playEarlyWarningSound, playWarningSound, playWarningDoubleSound, playCompletionSound, playStartSound, preloadAudio } from '../utils/timerSounds';

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
}: TimerDisplayProps) {
  const [displayTime, setDisplayTime] = useState(remainingTime);
  const [isDragging, setIsDragging] = useState(false);
  const [dragValue, setDragValue] = useState(0);
  const [isBlinking, setIsBlinking] = useState(false);
  // Default to false (show text) - only hide when we're certain space is limited
  const [isSpaceLimited, setIsSpaceLimited] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const blinkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const buttonsContainerRef = useRef<HTMLDivElement>(null);
  const lastSpaceLimitedStateRef = useRef<boolean | null>(null);
  const isTabletDevice = isTablet();
  
  // Debug logging
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
      });
    }
  }, [isTabletDevice]);

  useEffect(() => {
    setDisplayTime(remainingTime);
  }, [remainingTime]);

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

  useEffect(() => {
    if (isRunning && displayTime > 0) {
      intervalRef.current = setInterval(() => {
        setDisplayTime((prev) => {
          const newTime = prev - 1;
          
          // Play warning sounds following professional escalation patterns
          // For timers >60s: warnings at 30s, 20s, 15s
          if (totalDuration > 60) {
            if (newTime === 30 || newTime === 20 || newTime === 15) {
              playEarlyWarningSound();
            }
          }
          
          // Regular countdown warnings
          if (newTime === 20) {
            playEarlyWarningSound();
          } else if (newTime === 15) {
            playEarlyWarningSound();
          } else if (newTime <= 5 && newTime > 0) {
            // Two beeps per second from 5 to 0 (increased urgency)
            playWarningDoubleSound();
          } else if (newTime <= 10 && newTime > 5) {
            // Single beep per second from 10 to 6
            playWarningSound();
          }
          
          return Math.max(0, newTime);
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, displayTime]);

  // Note: Timer completion is handled by useLessonTimer hook
  // We don't need to call onStop() here as it would interfere with auto-advance
  // The completion sound is also played by useLessonTimer

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
      
      // Only update state if it actually changed (prevent unnecessary re-renders)
      if (lastSpaceLimitedStateRef.current !== shouldHideText) {
        console.log('[TimerDisplay] Updating state:', {
          from: lastSpaceLimitedStateRef.current,
          to: shouldHideText
        });
        
        setIsSpaceLimited(shouldHideText);
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
    let observerTimeoutId: NodeJS.Timeout | null = null;
    
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
    let resizeTimeout: NodeJS.Timeout;
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

  // Blinking effect for timer display
  useEffect(() => {
    // Clear any existing blink interval
    if (blinkIntervalRef.current) {
      clearInterval(blinkIntervalRef.current);
      blinkIntervalRef.current = null;
    }

    // Start blinking when 10 seconds or less remaining
    if (isRunning && displayTime <= 10 && displayTime > 0) {
      if (displayTime <= 5) {
        // Blink 2 times per second from 5 to 0 (every 250ms)
        blinkIntervalRef.current = setInterval(() => {
          setIsBlinking((prev) => !prev);
        }, 250);
      } else {
        // Blink once per second from 10 to 6 (every 500ms)
        blinkIntervalRef.current = setInterval(() => {
          setIsBlinking((prev) => !prev);
        }, 500);
      }
    } else {
      // Stop blinking when timer stops or goes above 10 seconds
      setIsBlinking(false);
    }

    return () => {
      if (blinkIntervalRef.current) {
        clearInterval(blinkIntervalRef.current);
        blinkIntervalRef.current = null;
      }
    };
  }, [isRunning, displayTime]);

  // Calculate progress based on current totalDuration, but allow display beyond it
  const effectiveMaxDuration = maxDuration || (totalDuration * 2);
  const progress = effectiveMaxDuration > 0 ? (displayTime / effectiveMaxDuration) * 100 : 0;
  
  // Calculate color scheme based on remaining time (following professional UX patterns)
  // Green: >10s, Yellow: 10-5s, Red: <5s
  const actualColorScheme = 
    displayTime > 10 ? 'green' :
    displayTime > 5 ? 'yellow' : 'red';

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressBarColor = 
    actualColorScheme === 'green' ? 'bg-green-500' :
    actualColorScheme === 'yellow' ? 'bg-yellow-500' : 'bg-red-500';

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

  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(e.clientX);
  }, [handleDragStart]);

  // Touch event handlers
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
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
            className={`h-full transition-all ${isDragging ? '' : 'duration-300'} ${progressBarColor}`}
            style={{ width: `${progress}%` }}
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
          <div className={`text-6xl md:text-4xl font-bold transition-opacity duration-150 ${
            actualColorScheme === 'green' ? 'text-green-600' :
            actualColorScheme === 'yellow' ? 'text-yellow-600' : 'text-red-600'
          } ${isBlinking ? 'opacity-30' : 'opacity-100'}`}>
            {formatTime(displayTime)}
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

