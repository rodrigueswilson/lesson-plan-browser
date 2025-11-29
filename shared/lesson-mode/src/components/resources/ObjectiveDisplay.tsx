import { useState, useEffect, useRef, useCallback } from 'react';
import type { LessonStep } from '@lesson-api';

interface ObjectiveDisplayProps {
  steps: LessonStep[];
  objective?: string | null;
}

export function ObjectiveDisplay({ steps, objective }: ObjectiveDisplayProps) {
  const [fontSize, setFontSize] = useState<number>(64);
  const textRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isCalculatingRef = useRef<boolean>(false);
  const lastContainerSizeRef = useRef<{ width: number; height: number } | null>(null);
  const lastFontSizeRef = useRef<number | null>(null);
  // First try to use objective from lesson plan data
  // If not available, try to find objective step
  const objectiveStep = steps.find(
    (step) => step.content_type === 'objective'
  );

  const objectiveText = objective || objectiveStep?.display_content || null;

  console.log('[ObjectiveDisplay] Objective prop:', objective);
  console.log('[ObjectiveDisplay] Objective step:', objectiveStep);
  console.log('[ObjectiveDisplay] Final objective text:', objectiveText);

  // Calculate optimal font size based on text length and container dimensions
  // Improved version with better accuracy and overflow handling
  const calculateFontSize = useCallback(() => {
    // Prevent recursive calls
    if (isCalculatingRef.current) {
      console.log('[ObjectiveDisplay] Calculation already in progress, skipping...');
      return;
    }
    
    if (!objectiveText || !textRef.current || !containerRef.current) {
      return;
    }
    
    // Check if container size actually changed significantly
    const container = containerRef.current;
    const currentWidth = container.offsetWidth;
    const currentHeight = container.offsetHeight;
    
    if (lastContainerSizeRef.current) {
      const widthDiff = Math.abs(currentWidth - lastContainerSizeRef.current.width);
      const heightDiff = Math.abs(currentHeight - lastContainerSizeRef.current.height);
      const threshold = 5; // Only recalculate if size changed by more than 5px
      
      if (widthDiff < threshold && heightDiff < threshold && lastFontSizeRef.current === fontSize) {
        console.log('[ObjectiveDisplay] Container size unchanged, skipping recalculation');
        return;
      }
    }
    
    // Set flag to prevent recursive calls
    isCalculatingRef.current = true;

    // container is already declared above (line 42)
    const textElement = textRef.current;
    
    // Get actual computed styles
    const computedStyle = window.getComputedStyle(textElement);
    const containerComputedStyle = window.getComputedStyle(container);
    
    // Get container dimensions more accurately using getBoundingClientRect
    const containerRect = container.getBoundingClientRect();
    const containerPadding = {
      top: parseFloat(containerComputedStyle.paddingTop) || 0,
      right: parseFloat(containerComputedStyle.paddingRight) || 0,
      bottom: parseFloat(containerComputedStyle.paddingBottom) || 0,
      left: parseFloat(containerComputedStyle.paddingLeft) || 0,
    };
    
    // Account for heading and other elements
    const headingHeight = container.querySelector('h3')?.getBoundingClientRect().height || 0;
    
    // Calculate available space more accurately
    // Use more of the space - reduce safety margins for larger fonts
    const availableWidth = containerRect.width - containerPadding.left - containerPadding.right;
    const availableHeight = containerRect.height - containerPadding.top - containerPadding.bottom - headingHeight - 20; // Reduced margin (was 60)
    
    if (availableWidth <= 0 || availableHeight <= 0) {
      console.warn('[ObjectiveDisplay] Invalid container dimensions:', { availableWidth, availableHeight });
      return;
    }
    
    // Create a temporary element to measure text with exact same styles
    const measureElement = document.createElement('div');
    measureElement.style.position = 'absolute';
    measureElement.style.visibility = 'hidden';
    measureElement.style.whiteSpace = 'normal';
    measureElement.style.wordWrap = 'normal'; // Changed from 'break-word' - prevents word breaking
    measureElement.style.overflowWrap = 'normal'; // Changed from 'break-word' - prevents word breaking
    measureElement.style.wordBreak = 'normal'; // Explicitly prevent word breaking
    measureElement.style.hyphens = 'none'; // Changed from 'auto' - prevents hyphenation
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
    
    // Use full available space - maximize font size
    // Text can wrap to multiple lines (1-4 lines), but words should never break
    // overflow: hidden will catch any edge cases
    const maxHeight = availableHeight; // Use 100% of height - allow up to 4 lines
    const maxWidth = availableWidth; // Use 100% of width
    
    // Calculate initial font size estimate based on area
    // Rough estimate: assume text takes up some area, calculate based on container area
    const textLength = objectiveText.length || 100;
    const areaRatio = (availableWidth * availableHeight) / (textLength * 100); // Rough area per character
    const estimatedSize = Math.min(Math.max(Math.sqrt(areaRatio) * 20, 32), 512); // Estimate between 32-512px
    
    // Font size must be in range 20-80px
    // Start from a large size and decrease until it fits (ensures maximum size)
    let optimalSize = Math.min(estimatedSize * 1.5, 80); // Start larger than estimate, but cap at 80px
    let minSize = 20; // Minimum font size
    let maxSize = 80; // Maximum font size - never exceed this
    
    // First, find the maximum size that fits using binary search
    let iterations = 0;
    const maxIterations = 40;
    
    // Binary search to find maximum fitting size
    while (minSize <= maxSize && iterations < maxIterations) {
      iterations++;
      const testSize = Math.floor((minSize + maxSize) / 2);
      measureElement.style.fontSize = `${testSize}px`;
      
      // Force a reflow to get accurate measurements
      void measureElement.offsetHeight;
      
      const textHeight = measureElement.scrollHeight;
      const textWidth = measureElement.scrollWidth;
      
      // Also check that the longest word fits on one line
      // Split text into words and check each word's width
      const words = objectiveText.split(/\s+/);
      let longestWordWidth = 0;
      if (words.length > 0) {
        // Create a temporary span to measure the longest word
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
      
      // Check if text fits - we want to maximize the size
      // For multi-line text: height is more important (can wrap to multiple lines)
      // Each word must fit on one line (no word breaking)
      const fitsHeight = textHeight <= maxHeight;
      const fitsWidth = textWidth <= maxWidth;
      const longestWordFits = longestWordWidth <= maxWidth;
      
      // Allow text to wrap to multiple lines, but ensure it fits in height
      // and each word fits on one line
      if (fitsHeight && longestWordFits) {
        // This size fits, try to go larger
        optimalSize = testSize;
        minSize = testSize + 1;
      } else {
        // Too large, reduce
        maxSize = testSize - 1;
      }
    }
    
    // Fine-tune: ensure it fits exactly without overflow
    // Cap optimalSize to 80px maximum
    optimalSize = Math.min(optimalSize, 80);
    measureElement.style.fontSize = `${optimalSize}px`;
    void measureElement.offsetHeight;
    
    // Verify longest word still fits
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
    
    // If it doesn't fit, reduce pixel by pixel until it does
    // Priority: height (multi-line is OK) and longest word must fit
    // Never go below 20px or above 80px
    while ((measureElement.scrollHeight > maxHeight || 
            longestWordWidth > maxWidth) && 
           optimalSize > minSize) {
      optimalSize -= 1;
      measureElement.style.fontSize = `${optimalSize}px`;
      void measureElement.offsetHeight;
    }
    
    // Now try to maximize: increase by 1px at a time until it doesn't fit
    // This ensures we get the absolute maximum size within the 20-80px range
    let testLarger = optimalSize + 1;
    let maxAttempts = 20; // Safety limit for fine-tuning
    // Cap at 80px maximum
    while (testLarger <= 80 && maxAttempts > 0) {
      measureElement.style.fontSize = `${testLarger}px`;
      void measureElement.offsetHeight;
      
      // Check longest word for this size
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
      
      // Check if it fits - height and longest word are the constraints
      if (measureElement.scrollHeight <= maxHeight && 
          longestWordWidth <= maxWidth) {
        optimalSize = testLarger;
        testLarger += 1;
        maxAttempts -= 1;
      } else {
        break; // Found the maximum
      }
    }
    
    document.body.removeChild(measureElement);
    
    // Set the optimal font size
    setFontSize(optimalSize);
    lastFontSizeRef.current = optimalSize;
    lastContainerSizeRef.current = { width: currentWidth, height: currentHeight };
    
    if (textElement) {
      textElement.style.fontSize = `${optimalSize}px`;
      textElement.style.maxWidth = `${availableWidth}px`;
      // Use overflow hidden to prevent text from going outside, but no ellipsis
      // The font size calculation ensures everything fits, so no truncation needed
      textElement.style.overflow = 'hidden';
      // Prevent word breaking - words should never be split
      textElement.style.wordWrap = 'normal';
      textElement.style.overflowWrap = 'normal';
      textElement.style.wordBreak = 'normal';
      textElement.style.hyphens = 'none';
      
      // Re-enable calculation after a delay to allow layout to settle
      setTimeout(() => {
        isCalculatingRef.current = false;
      }, 200);
    } else {
      // Re-enable calculation if no text element
      setTimeout(() => {
        isCalculatingRef.current = false;
      }, 200);
    }
    
    console.log('[ObjectiveDisplay] Font size calculated:', {
      optimalSize,
      availableWidth,
      availableHeight,
      textLength: objectiveText.length,
      iterations,
    });
  }, [objectiveText, fontSize]);

  useEffect(() => {
    if (objectiveText) {
      // Use requestAnimationFrame for better timing - ensures layout is complete
      let rafId: number;
      const timeoutId = setTimeout(() => {
        rafId = requestAnimationFrame(() => {
          // Double RAF to ensure all styles are applied
          requestAnimationFrame(() => {
            calculateFontSize();
          });
        });
      }, 150);
      
      return () => {
        clearTimeout(timeoutId);
        if (rafId) cancelAnimationFrame(rafId);
      };
    }
  }, [objectiveText, calculateFontSize]);

  // Use ResizeObserver for more accurate container size changes
  useEffect(() => {
    if (objectiveText && containerRef.current) {
      let resizeObserver: ResizeObserver | null = null;
      let debounceTimer: NodeJS.Timeout;
      
      const handleResize = () => {
        // Don't recalculate if we're already calculating
        if (isCalculatingRef.current) {
          return;
        }
        
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          // Double-check we're not calculating before proceeding
          if (!isCalculatingRef.current) {
            requestAnimationFrame(() => {
              if (!isCalculatingRef.current) {
                calculateFontSize();
              }
            });
          }
        }, 300); // Increased debounce time to prevent rapid recalculations
      };
      
      // Use ResizeObserver for container changes
      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver((entries) => {
          // Only trigger if the size actually changed significantly
          for (const entry of entries) {
            const { width, height } = entry.contentRect;
            if (lastContainerSizeRef.current) {
              const widthDiff = Math.abs(width - lastContainerSizeRef.current.width);
              const heightDiff = Math.abs(height - lastContainerSizeRef.current.height);
              if (widthDiff < 5 && heightDiff < 5) {
                // Size change is too small, ignore
                return;
              }
            }
          }
          handleResize();
        });
        resizeObserver.observe(containerRef.current);
      }
      
      // Also listen to window resize as fallback
      window.addEventListener('resize', handleResize);
      
      return () => {
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
        window.removeEventListener('resize', handleResize);
        clearTimeout(debounceTimer);
      };
    }
  }, [objectiveText, calculateFontSize]);

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

  return (
    <div className="h-full flex flex-col">
      <div 
        ref={containerRef}
        className="flex-1 flex flex-col items-center justify-center p-8 md:p-12 lg:p-16 min-h-0 bg-muted rounded-lg m-4"
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
          {objectiveText}
        </div>
      </div>
    </div>
  );
}

