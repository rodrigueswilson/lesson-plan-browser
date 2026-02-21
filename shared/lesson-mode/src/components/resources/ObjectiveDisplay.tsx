import { useState, useEffect, useRef, useCallback } from 'react';
import type { LessonStep } from '@lesson-api';
import { calculateMaxFittingSize } from '../../utils/fontSizeCalculation';
import { parseMarkdown } from '../../utils/markdownUtils';

interface ObjectiveDisplayProps {
  steps: LessonStep[];
  objective?: string | null;
}

export function ObjectiveDisplay({ steps, objective }: ObjectiveDisplayProps) {
  const [fontSize, setFontSize] = useState<number>(64);
  const [isManualAdjustment, setIsManualAdjustment] = useState<boolean>(false);
  const [maxFittingSize, setMaxFittingSize] = useState<number>(200); // Maximum size that fits in container
  const textRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isCalculatingRef = useRef<boolean>(false);
  const lastContainerSizeRef = useRef<{ width: number; height: number } | null>(null);
  const lastFontSizeRef = useRef<number | null>(null);

  // Touch gesture tracking for pinch-to-zoom
  const touchStartDistanceRef = useRef<number | null>(null);
  const touchStartFontSizeRef = useRef<number | null>(null);

  // First try to use objective from lesson plan data
  // If not available, try to find objective step
  const objectiveStep = steps.find(
    (step) => step.content_type === 'objective'
  );

  const objectiveText = objective || objectiveStep?.display_content || null;

  console.log('[ObjectiveDisplay] Objective prop:', objective);
  console.log('[ObjectiveDisplay] Objective step:', objectiveStep);
  console.log('[ObjectiveDisplay] Final objective text:', objectiveText);

  // Calculate maximum font size that fits in container (for limiting manual adjustments)
  // Uses shared utility following SSO/DRY principle
  const calculateMaxFittingSizeLocal = useCallback(() => {
    if (!objectiveText || !textRef.current || !containerRef.current) {
      return 200; // Default to 200px if can't calculate
    }

    const container = containerRef.current;
    const textElement = textRef.current;
    const headingHeight = container.querySelector('h3')?.getBoundingClientRect().height || 0;

    return calculateMaxFittingSize({
      text: objectiveText,
      textElement,
      container,
      headingHeight,
      minSize: 20,
      maxSize: 200,
      fontWeight: 'medium',
      lineHeight: '1.5',
      textAlign: 'center',
    });
  }, [objectiveText]);

  // Adjust font size with constraints (20px minimum, maxFittingSize maximum)
  const adjustFontSize = useCallback((delta: number) => {
    setFontSize((prevSize) => {
      const maxSize = maxFittingSize;
      const newSize = Math.max(20, Math.min(maxSize, prevSize + delta));
      setIsManualAdjustment(true);
      lastFontSizeRef.current = newSize;
      return newSize;
    });
  }, [maxFittingSize]);

  // Handle mouse wheel scroll to adjust font size
  const handleWheel = useCallback((e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -2 : 2; // Scroll down = smaller, scroll up = larger
    adjustFontSize(delta);
  }, [adjustFontSize]);

  // Calculate distance between two touch points
  const getTouchDistance = (touch1: { clientX: number; clientY: number }, touch2: { clientX: number; clientY: number }): number => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Handle touch start for pinch-to-zoom
  const handleTouchStart = useCallback((e: React.TouchEvent<HTMLDivElement>) => {
    if (e.touches.length === 2) {
      const distance = getTouchDistance(e.touches[0], e.touches[1]);
      touchStartDistanceRef.current = distance;
      touchStartFontSizeRef.current = fontSize;
      setIsManualAdjustment(true);
    }
  }, [fontSize]);

  // Handle touch move for pinch-to-zoom
  const handleTouchMove = useCallback((e: React.TouchEvent<HTMLDivElement>) => {
    if (e.touches.length === 2 && touchStartDistanceRef.current !== null && touchStartFontSizeRef.current !== null) {
      e.preventDefault(); // Prevent scrolling while pinching
      const currentDistance = getTouchDistance(e.touches[0], e.touches[1]);
      const scale = currentDistance / touchStartDistanceRef.current;
      const newSize = Math.max(20, Math.min(maxFittingSize, touchStartFontSizeRef.current * scale));
      setFontSize(newSize);
      lastFontSizeRef.current = newSize;
    }
  }, [maxFittingSize]);

  // Handle touch end
  const handleTouchEnd = useCallback(() => {
    touchStartDistanceRef.current = null;
    touchStartFontSizeRef.current = null;
  }, []);

  // Calculate optimal font size - reused from ExpandableItemView logic
  const calculateFontSize = useCallback(() => {
    if (isCalculatingRef.current || isManualAdjustment) {
      return;
    }

    if (!objectiveText || !textRef.current || !containerRef.current) {
      return;
    }

    const container = containerRef.current;
    const currentWidth = container.offsetWidth;
    const currentHeight = container.offsetHeight;

    if (lastContainerSizeRef.current) {
      const widthDiff = Math.abs(currentWidth - lastContainerSizeRef.current.width);
      const heightDiff = Math.abs(currentHeight - lastContainerSizeRef.current.height);
      const threshold = 5;

      if (widthDiff < threshold && heightDiff < threshold && lastFontSizeRef.current === fontSize) {
        return;
      }
    }

    isCalculatingRef.current = true;
    const textElement = textRef.current;
    const computedStyle = window.getComputedStyle(textElement);
    const containerComputedStyle = window.getComputedStyle(container);
    const containerRect = container.getBoundingClientRect();
    const containerPadding = {
      top: parseFloat(containerComputedStyle.paddingTop) || 0,
      right: parseFloat(containerComputedStyle.paddingRight) || 0,
      bottom: parseFloat(containerComputedStyle.paddingBottom) || 0,
      left: parseFloat(containerComputedStyle.paddingLeft) || 0,
    };

    const headingHeight = container.querySelector('h3')?.getBoundingClientRect().height || 0;
    const availableWidth = containerRect.width - containerPadding.left - containerPadding.right;
    const availableHeight = containerRect.height - containerPadding.top - containerPadding.bottom - headingHeight - 20;

    if (availableWidth <= 0 || availableHeight <= 0) {
      isCalculatingRef.current = false;
      return;
    }

    const measureElement = document.createElement('div');
    measureElement.style.position = 'absolute';
    measureElement.style.visibility = 'hidden';
    measureElement.style.whiteSpace = 'normal';
    measureElement.style.wordWrap = 'normal';
    measureElement.style.overflowWrap = 'normal';
    measureElement.style.wordBreak = 'normal';
    measureElement.style.hyphens = 'none';
    measureElement.style.width = `${availableWidth}px`;
    measureElement.style.maxWidth = `${availableWidth}px`;
    measureElement.style.fontWeight = computedStyle.fontWeight || 'medium';
    measureElement.style.fontFamily = computedStyle.fontFamily;
    measureElement.style.fontStyle = computedStyle.fontStyle;
    measureElement.style.letterSpacing = computedStyle.letterSpacing;
    measureElement.style.textAlign = 'center';
    measureElement.style.lineHeight = computedStyle.lineHeight || '1.5';
    measureElement.style.boxSizing = 'border-box';
    measureElement.style.padding = '0';
    measureElement.style.margin = '0';
    measureElement.textContent = objectiveText;

    document.body.appendChild(measureElement);

    const maxHeight = availableHeight;
    const maxWidth = availableWidth;
    const textLength = objectiveText.length || 100;
    const areaRatio = (availableWidth * availableHeight) / (textLength * 100);
    const estimatedSize = Math.min(Math.max(Math.sqrt(areaRatio) * 20, 32), 512);

    // Font size must be in range 20-80px for auto-calculation
    // (Manual adjustment can go up to 200px)
    let optimalSize = Math.min(estimatedSize * 1.5, 80);
    let minSize = 20;
    let maxSize = 80; // Maximum for auto-calculation
    let iterations = 0;
    const maxIterations = 40;

    while (minSize <= maxSize && iterations < maxIterations) {
      iterations++;
      const testSize = Math.floor((minSize + maxSize) / 2);
      measureElement.style.fontSize = `${testSize}px`;
      void measureElement.offsetHeight;

      const textHeight = measureElement.scrollHeight;
      const words = objectiveText.split(/\s+/);
      let longestWordWidth = 0;
      if (words.length > 0) {
        const wordMeasure = document.createElement('span');
        wordMeasure.style.position = 'absolute';
        wordMeasure.style.visibility = 'hidden';
        wordMeasure.style.fontSize = `${testSize}px`;
        wordMeasure.style.fontFamily = measureElement.style.fontFamily;
        wordMeasure.style.fontWeight = measureElement.style.fontWeight;
        wordMeasure.style.fontStyle = measureElement.style.fontStyle;
        wordMeasure.style.letterSpacing = measureElement.style.letterSpacing;
        document.body.appendChild(wordMeasure);

        for (const word of words) {
          wordMeasure.textContent = word;
          const wordWidth = wordMeasure.offsetWidth;
          if (wordWidth > longestWordWidth) {
            longestWordWidth = wordWidth;
          }
        }

        document.body.removeChild(wordMeasure);
      }

      const fitsHeight = textHeight <= maxHeight;
      const longestWordFits = longestWordWidth <= maxWidth;

      if (fitsHeight && longestWordFits) {
        optimalSize = testSize;
        minSize = testSize + 1;
      } else {
        maxSize = testSize - 1;
      }
    }

    // Cap optimalSize to 80px maximum for auto-calculation
    optimalSize = Math.min(optimalSize, 80);
    measureElement.style.fontSize = `${optimalSize}px`;
    void measureElement.offsetHeight;

    const words = objectiveText.split(/\s+/);
    let longestWordWidth = 0;
    if (words.length > 0) {
      const wordMeasure = document.createElement('span');
      wordMeasure.style.position = 'absolute';
      wordMeasure.style.visibility = 'hidden';
      wordMeasure.style.fontSize = `${optimalSize}px`;
      wordMeasure.style.fontFamily = measureElement.style.fontFamily;
      wordMeasure.style.fontWeight = measureElement.style.fontWeight;
      wordMeasure.style.fontStyle = measureElement.style.fontStyle;
      wordMeasure.style.letterSpacing = measureElement.style.letterSpacing;
      document.body.appendChild(wordMeasure);

      for (const word of words) {
        wordMeasure.textContent = word;
        const wordWidth = wordMeasure.offsetWidth;
        if (wordWidth > longestWordWidth) {
          longestWordWidth = wordWidth;
        }
      }

      document.body.removeChild(wordMeasure);
    }

    while ((measureElement.scrollHeight > maxHeight ||
      longestWordWidth > maxWidth) &&
      optimalSize > minSize) {
      optimalSize -= 1;
      measureElement.style.fontSize = `${optimalSize}px`;
      void measureElement.offsetHeight;
    }

    // Cap at 80px maximum for auto-calculation
    let testLarger = optimalSize + 1;
    let maxAttempts = 20;
    while (testLarger <= 80 && maxAttempts > 0) {
      measureElement.style.fontSize = `${testLarger}px`;
      void measureElement.offsetHeight;

      let longestWordWidth = 0;
      if (words.length > 0) {
        const wordMeasure = document.createElement('span');
        wordMeasure.style.position = 'absolute';
        wordMeasure.style.visibility = 'hidden';
        wordMeasure.style.fontSize = `${testLarger}px`;
        wordMeasure.style.fontFamily = measureElement.style.fontFamily;
        wordMeasure.style.fontWeight = measureElement.style.fontWeight;
        wordMeasure.style.fontStyle = measureElement.style.fontStyle;
        wordMeasure.style.letterSpacing = measureElement.style.letterSpacing;
        document.body.appendChild(wordMeasure);

        for (const word of words) {
          wordMeasure.textContent = word;
          const wordWidth = wordMeasure.offsetWidth;
          if (wordWidth > longestWordWidth) {
            longestWordWidth = wordWidth;
          }
        }

        document.body.removeChild(wordMeasure);
      }

      if (measureElement.scrollHeight <= maxHeight &&
        longestWordWidth <= maxWidth) {
        optimalSize = testLarger;
        testLarger += 1;
        maxAttempts -= 1;
      } else {
        break;
      }
    }

    document.body.removeChild(measureElement);

    // Set the optimal font size if it changed
    if (optimalSize !== fontSize) {
      setFontSize(optimalSize);
      // Set maxFittingSize to optimalSize initially (as requested)
      setMaxFittingSize(optimalSize);
      lastFontSizeRef.current = optimalSize;
    }

    lastContainerSizeRef.current = { width: currentWidth, height: currentHeight };

    if (textElement) {
      textElement.style.fontSize = `${optimalSize}px`;
      textElement.style.maxWidth = `${availableWidth}px`;
      textElement.style.overflow = 'hidden';
      textElement.style.wordWrap = 'normal';
      textElement.style.overflowWrap = 'normal';
      textElement.style.wordBreak = 'normal';
      textElement.style.hyphens = 'none';

      // Calculate true maximum that fits and update maxFittingSize to allow increases
      setTimeout(() => {
        isCalculatingRef.current = false;
        requestAnimationFrame(() => {
          const trueMax = calculateMaxFittingSizeLocal();
          setMaxFittingSize(trueMax);
        });
      }, 200);
    } else {
      setTimeout(() => {
        isCalculatingRef.current = false;
        requestAnimationFrame(() => {
          const trueMax = calculateMaxFittingSizeLocal();
          setMaxFittingSize(trueMax);
        });
      }, 200);
    }
  }, [objectiveText]); // Removed fontSize from dependencies

  // Calculate max fitting size when objective changes or container resizes
  useEffect(() => {
    if (objectiveText) {
      // Use requestAnimationFrame to ensure layout is ready
      let rafId: number;
      const timeoutId = setTimeout(() => {
        rafId = requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const maxSize = calculateMaxFittingSizeLocal();
            setMaxFittingSize(maxSize);
          });
        });
      }, 200);

      return () => {
        clearTimeout(timeoutId);
        if (rafId) cancelAnimationFrame(rafId);
      };
    }
  }, [objectiveText, calculateMaxFittingSizeLocal]);

  useEffect(() => {
    if (objectiveText && !isManualAdjustment) {
      setIsManualAdjustment(false);
      let rafId: number;
      const timeoutId = setTimeout(() => {
        rafId = requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            if (!isManualAdjustment) {
              calculateFontSize();
            }
          });
        });
      }, 150);

      return () => {
        clearTimeout(timeoutId);
        if (rafId) cancelAnimationFrame(rafId);
      };
    }
  }, [objectiveText, calculateFontSize, isManualAdjustment]);

  useEffect(() => {
    if (objectiveText && containerRef.current) {
      let resizeObserver: ResizeObserver | null = null;
      let debounceTimer: NodeJS.Timeout;

      const handleResize = () => {
        if (isCalculatingRef.current || isManualAdjustment) {
          return;
        }

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          if (!isCalculatingRef.current && !isManualAdjustment) {
            requestAnimationFrame(() => {
              if (!isCalculatingRef.current && !isManualAdjustment) {
                calculateFontSize();
              }
            });
          }
        }, 300);
      };

      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver((entries) => {
          for (const entry of entries) {
            const { width, height } = entry.contentRect;
            if (lastContainerSizeRef.current) {
              const widthDiff = Math.abs(width - lastContainerSizeRef.current.width);
              const heightDiff = Math.abs(height - lastContainerSizeRef.current.height);
              if (widthDiff < 5 && heightDiff < 5) {
                return;
              }
            }
          }
          handleResize();
        });
        resizeObserver.observe(containerRef.current);
      }

      window.addEventListener('resize', handleResize);

      return () => {
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
        window.removeEventListener('resize', handleResize);
        clearTimeout(debounceTimer);
      };
    }
  }, [objectiveText, calculateFontSize, isManualAdjustment, calculateMaxFittingSizeLocal]);

  if (!objectiveText) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="mb-2">No objective found for this lesson.</div>
          <div className="text-xs text-muted-foreground">
            Debug: objective={objective ? 'found' : 'null'}, step={objectiveStep ? 'found' : 'null'}
          </div>
        </div>
      </div>
    );
  }

  // Always show expanded view directly - no list view, no close button, no navigation
  return (
    <div className="h-full flex flex-col">
      <div
        ref={containerRef}
        className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 lg:p-16 min-h-0 bg-muted rounded-lg m-4"
        style={{ touchAction: 'pan-x pan-y' }}
        onWheel={handleWheel}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <h3 className="text-lg md:text-xl font-semibold text-center text-muted-foreground mb-6">
          Student Goal
        </h3>
        <div
          ref={textRef}
          className="text-center leading-relaxed whitespace-pre-wrap font-medium w-full"
          style={{
            fontSize: `${fontSize}px`,
            lineHeight: '1.5',
            wordWrap: 'normal',
            overflowWrap: 'normal',
            wordBreak: 'normal',
            hyphens: 'none',
          }}
        >
          {parseMarkdown(objectiveText)}
        </div>
      </div>
    </div>
  );
}
