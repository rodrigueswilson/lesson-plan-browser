import { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@lesson-ui/Button';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';

export interface ExpandableItem {
  id: string | number;
  primaryText: string;
  secondaryText?: string;
  badge?: string;
  metadata?: string;
}

interface ExpandableItemViewProps {
  items: ExpandableItem[];
  onItemSelect?: (itemIndex: number) => void;
  renderItem?: (item: ExpandableItem, isExpanded: boolean, textRef?: React.RefObject<HTMLDivElement>, fontSize?: number) => React.ReactNode;
  title?: string;
}

export function ExpandableItemView({
  items,
  onItemSelect,
  renderItem,
  title,
}: ExpandableItemViewProps) {
  const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);
  const [fontSize, setFontSize] = useState<number>(64);
  const textRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isCalculatingRef = useRef<boolean>(false);
  const lastContainerSizeRef = useRef<{ width: number; height: number } | null>(null);
  const lastFontSizeRef = useRef<number | null>(null);

  const handleItemClick = (itemIndex: number) => {
    setSelectedItemIndex(itemIndex);
    onItemSelect?.(itemIndex);
  };

  const handlePrevious = () => {
    if (selectedItemIndex !== null && selectedItemIndex > 0) {
      setSelectedItemIndex(selectedItemIndex - 1);
    }
  };

  const handleNext = () => {
    if (selectedItemIndex !== null && selectedItemIndex < items.length - 1) {
      setSelectedItemIndex(selectedItemIndex + 1);
    }
  };

  const handleClose = () => {
    setSelectedItemIndex(null);
    // Reset calculation state when closing
    isCalculatingRef.current = false;
    lastContainerSizeRef.current = null;
    lastFontSizeRef.current = null;
  };

  // Calculate optimal font size based on text length and container dimensions
  // Improved version with better accuracy and overflow handling
  const calculateFontSize = useCallback(() => {
    // Prevent recursive calls
    if (isCalculatingRef.current) {
      console.log('[ExpandableItemView] Calculation already in progress, skipping...');
      return;
    }
    
    if (selectedItemIndex === null || !items[selectedItemIndex] || !textRef.current || !containerRef.current) {
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
        console.log('[ExpandableItemView] Container size unchanged, skipping recalculation');
        return;
      }
    }
    
    // Set flag to prevent recursive calls
    isCalculatingRef.current = true;

    const item = items[selectedItemIndex];
    const text = item.primaryText;
    // container is already declared above (line 73)
    const textElement = textRef.current;
    
    // Get actual computed styles from the text element
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
    
    // Account for other elements in the container (badges, metadata, etc.)
    // Find all child elements except the text element to calculate their height
    const otherElementsHeight = Array.from(container.children)
      .filter(child => child !== textElement && !child.contains(textElement))
      .reduce((sum, child) => {
        const rect = child.getBoundingClientRect();
        return sum + rect.height;
      }, 0);
    
    // Calculate available space more accurately
    // Use more of the space - reduce safety margins for larger fonts
    const availableWidth = containerRect.width - containerPadding.left - containerPadding.right;
    const availableHeight = containerRect.height - containerPadding.top - containerPadding.bottom - otherElementsHeight - 20; // Reduced margin (was 40)
    
    if (availableWidth <= 0 || availableHeight <= 0) {
      console.warn('[ExpandableItemView] Invalid container dimensions:', { availableWidth, availableHeight });
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
    measureElement.style.fontWeight = computedStyle.fontWeight || 'bold';
    measureElement.style.fontFamily = computedStyle.fontFamily;
    measureElement.style.fontStyle = computedStyle.fontStyle;
    measureElement.style.letterSpacing = computedStyle.letterSpacing;
    measureElement.style.textAlign = 'center';
    measureElement.style.lineHeight = computedStyle.lineHeight || '1.2';
    measureElement.style.boxSizing = 'border-box';
    measureElement.style.padding = '0';
    measureElement.style.margin = '0';
    
    // Copy text content (including HTML if present)
    // Clone the element structure to preserve all HTML content and styles
    if (textElement.innerHTML && textElement.innerHTML.trim().length > 0) {
      // Clone the element to preserve HTML structure (for highlighted vocabulary, etc.)
      const clone = textElement.cloneNode(true) as HTMLElement;
      // Remove any inline fontSize that might interfere
      clone.style.fontSize = '';
      // Copy all child nodes
      measureElement.innerHTML = clone.innerHTML;
    } else if (textElement.textContent) {
      measureElement.textContent = textElement.textContent;
    } else {
      measureElement.textContent = text;
    }
    
    // Also copy any computed styles that affect layout
    const textElementStyles = window.getComputedStyle(textElement);
    measureElement.style.color = textElementStyles.color;
    measureElement.style.textDecoration = textElementStyles.textDecoration;
    
    document.body.appendChild(measureElement);
    
    // Use full available space - maximize font size
    // Text can wrap to multiple lines (1-4 lines), but words should never break
    // overflow: hidden will catch any edge cases
    const maxHeight = availableHeight; // Use 100% of height - allow up to 4 lines
    const maxWidth = availableWidth; // Use 100% of width
    
    // Calculate initial font size estimate based on area
    // Rough estimate: assume text takes up some area, calculate based on container area
    const textLength = text.length || textElement.textContent?.length || 100;
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
      const words = text.split(/\s+/);
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
    const words = text.split(/\s+/);
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
      
      // Final verification: check if the actual rendered element fits
      // Use requestAnimationFrame to ensure the style has been applied
      requestAnimationFrame(() => {
        // Re-enable calculation after a delay to allow layout to settle
        setTimeout(() => {
          isCalculatingRef.current = false;
        }, 200);
        
        const actualHeight = textElement.scrollHeight;
        const actualWidth = textElement.scrollWidth;
        const containerHeight = containerRect.height - containerPadding.top - containerPadding.bottom - otherElementsHeight;
        
        // If it still doesn't fit, reduce further
        const maxHeight = containerHeight; // Use 100%
        const maxWidth = availableWidth; // Use 100%
        if ((actualHeight > maxHeight || actualWidth > maxWidth) && optimalSize > 16) {
          let adjustedSize = optimalSize;
          while ((actualHeight > containerHeight * 0.95 || actualWidth > availableWidth * 0.98) && adjustedSize > 12) {
            adjustedSize -= 1;
            textElement.style.fontSize = `${adjustedSize}px`;
            // Force reflow
            void textElement.offsetHeight;
            const newHeight = textElement.scrollHeight;
            const newWidth = textElement.scrollWidth;
            if (newHeight <= maxHeight && newWidth <= maxWidth) {
              setFontSize(adjustedSize);
              lastFontSizeRef.current = adjustedSize;
              console.log('[ExpandableItemView] Font size adjusted after verification:', adjustedSize);
              break;
            }
          }
        }
      });
    } else {
      // Re-enable calculation if no text element
      setTimeout(() => {
        isCalculatingRef.current = false;
      }, 200);
    }
    
    console.log('[ExpandableItemView] Font size calculated:', {
      optimalSize,
      availableWidth,
      availableHeight,
      textLength: text.length,
      iterations,
    });
  }, [selectedItemIndex, items, fontSize]);

  useEffect(() => {
    if (selectedItemIndex !== null) {
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
  }, [selectedItemIndex, calculateFontSize]);

  // Use ResizeObserver for more accurate container size changes
  useEffect(() => {
    if (selectedItemIndex !== null && containerRef.current) {
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
  }, [selectedItemIndex, calculateFontSize]);

  // Show expanded view if an item is selected
  if (selectedItemIndex !== null && items[selectedItemIndex]) {
    const selectedItem = items[selectedItemIndex];
    const currentIndex = selectedItemIndex + 1;
    const totalItems = items.length;

    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between p-6 md:p-4 border-b bg-card">
          <Button
            variant="outline"
            size="sm"
            onClick={handleClose}
            className="flex items-center gap-2 h-12 md:h-9 px-6 md:px-4 text-base md:text-sm"
          >
            <X className="w-5 h-5 md:w-4 md:h-4" />
            Close
          </Button>
          <div className="text-lg md:text-sm text-muted-foreground font-medium">
            {currentIndex} of {totalItems}
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center p-4 min-h-0">
          <div className="w-full h-full flex items-center justify-between gap-4 max-w-[95vw]">
            {/* Navigation buttons - Larger for tablet */}
            <button
              onClick={handlePrevious}
              disabled={selectedItemIndex === 0}
              className="flex items-center justify-center flex-shrink-0 w-16 h-16 md:w-12 md:h-12 bg-background border-2 border-gray-400 hover:bg-muted hover:border-gray-600 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:border-gray-300 disabled:hover:scale-100 disabled:hover:bg-gray-100 shadow-md rounded-md transition-all duration-200"
              style={{ minWidth: '64px', minHeight: '64px' }}
              aria-label="Previous"
            >
              <ChevronLeft 
                className={`w-10 h-10 md:w-8 md:h-8 ${
                  selectedItemIndex === 0 
                    ? 'text-gray-400 dark:text-gray-500' 
                    : 'text-gray-900 dark:text-gray-100'
                }`} 
                strokeWidth={3} 
              />
            </button>

            <div 
              ref={containerRef}
              className="flex-1 flex flex-col items-center justify-center h-full w-full p-8 md:p-12 lg:p-16 bg-muted rounded-lg overflow-hidden"
            >
              {renderItem ? (
                <div className="w-full flex flex-col items-center">
                  {renderItem(selectedItem, true, textRef, fontSize)}
                </div>
              ) : (
                <>
                  <div 
                    ref={textRef}
                    className="font-bold text-center mb-6 w-full"
                    style={{
                      fontSize: `${fontSize}px`,
                      lineHeight: '1.2',
                      wordWrap: 'normal',
                      overflowWrap: 'normal',
                      wordBreak: 'normal',
                      hyphens: 'none',
                    }}
                  >
                    {selectedItem.primaryText}
                  </div>
                  {selectedItem.secondaryText && (
                    <div className="text-2xl md:text-3xl text-center text-muted-foreground italic mb-4">
                      {selectedItem.secondaryText}
                    </div>
                  )}
                  {selectedItem.badge && (
                    <div className="mt-6 inline-flex items-center rounded-full border-2 px-4 py-2 text-sm md:text-base uppercase tracking-wide text-muted-foreground bg-background">
                      {selectedItem.badge}
                    </div>
                  )}
                  {selectedItem.metadata && (
                    <div className="mt-4 text-sm md:text-base text-muted-foreground">
                      {selectedItem.metadata}
                    </div>
                  )}
                </>
              )}
            </div>

            <button
              onClick={handleNext}
              disabled={selectedItemIndex === items.length - 1}
              className="flex items-center justify-center flex-shrink-0 w-16 h-16 md:w-12 md:h-12 bg-background border-2 border-gray-400 hover:bg-muted hover:border-gray-600 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:border-gray-300 disabled:hover:scale-100 disabled:hover:bg-gray-100 shadow-md rounded-md transition-all duration-200"
              style={{ minWidth: '64px', minHeight: '64px' }}
              aria-label="Next"
            >
              <ChevronRight 
                className={`w-10 h-10 md:w-8 md:h-8 ${
                  selectedItemIndex === items.length - 1 
                    ? 'text-gray-400 dark:text-gray-500' 
                    : 'text-gray-900 dark:text-gray-100'
                }`} 
                strokeWidth={3} 
              />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show list view
  return (
    <div className="h-full flex flex-col">
      {title && (
        <div className="p-4 border-b bg-card">
          <h3 className="text-2xl font-bold text-center">{title}</h3>
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="space-y-6">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className="cursor-pointer hover:bg-muted/50 p-4 rounded-lg transition-colors"
              onClick={() => handleItemClick(idx)}
            >
              {renderItem ? (
                renderItem(item, false)
              ) : (
                <div className="p-4 bg-muted rounded-lg">
                  <div className="text-xl font-medium">{item.primaryText}</div>
                  {item.secondaryText && (
                    <div className="text-muted-foreground italic mt-2">{item.secondaryText}</div>
                  )}
                  {item.badge && (
                    <div className="mt-2 inline-flex items-center rounded-full border px-2 py-0.5 text-xs uppercase tracking-wide text-muted-foreground">
                      {item.badge}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

