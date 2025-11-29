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
  };

  // Calculate optimal font size based on text length and container width
  const calculateFontSize = useCallback(() => {
    if (selectedItemIndex !== null && items[selectedItemIndex] && textRef.current && containerRef.current) {
      const item = items[selectedItemIndex];
      const text = item.primaryText;
      const container = containerRef.current;
      const textElement = textRef.current;
      
      // Get container dimensions (accounting for padding)
      const containerWidth = container.offsetWidth - 128; // Subtract padding (64px on each side)
      const containerHeight = container.offsetHeight - 200; // Subtract space for badges/counter
      
      if (containerWidth <= 0 || containerHeight <= 0) return;
      
      // Create a temporary element to measure text
      const measureElement = document.createElement('div');
      measureElement.style.position = 'absolute';
      measureElement.style.visibility = 'hidden';
      measureElement.style.whiteSpace = 'normal';
      measureElement.style.wordWrap = 'break-word';
      measureElement.style.overflowWrap = 'break-word';
      measureElement.style.width = `${containerWidth}px`;
      measureElement.style.fontWeight = 'bold';
      measureElement.style.fontFamily = getComputedStyle(textElement).fontFamily;
      measureElement.style.lineHeight = '1.2';
      document.body.appendChild(measureElement);
      
      // Binary search for optimal font size
      let minSize = 24;
      let maxSize = 256;
      let optimalSize = 64;
      
      while (minSize <= maxSize) {
        const testSize = Math.floor((minSize + maxSize) / 2);
        measureElement.style.fontSize = `${testSize}px`;
        measureElement.textContent = text;
        
        const textHeight = measureElement.scrollHeight;
        const textWidth = measureElement.scrollWidth;
        
        // Check if text fits (with some margin)
        if (textHeight <= containerHeight * 0.9 && textWidth <= containerWidth * 0.98) {
          optimalSize = testSize;
          minSize = testSize + 1;
        } else {
          maxSize = testSize - 1;
        }
      }
      
      document.body.removeChild(measureElement);
      
      // Set the optimal font size
      setFontSize(optimalSize);
      if (textElement) {
        textElement.style.fontSize = `${optimalSize}px`;
      }
    }
  }, [selectedItemIndex, items]);

  useEffect(() => {
    if (selectedItemIndex !== null) {
      // Small delay to ensure DOM is ready
      const timeoutId = setTimeout(() => {
        calculateFontSize();
      }, 100);
      
      return () => clearTimeout(timeoutId);
    }
  }, [selectedItemIndex, calculateFontSize]);

  // Recalculate on window resize
  useEffect(() => {
    if (selectedItemIndex !== null) {
      const handleResize = () => {
        calculateFontSize();
      };
      
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
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
              className="flex items-center justify-center flex-shrink-0 w-16 h-16 md:w-12 md:h-12 bg-background border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed shadow-md rounded-md transition-colors"
              style={{ minWidth: '64px', minHeight: '64px' }}
              aria-label="Previous"
            >
              <ChevronLeft className="w-10 h-10 md:w-8 md:h-8 text-gray-900 dark:text-gray-100" strokeWidth={3} />
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
                    className="font-bold text-center mb-6 w-full break-words"
                    style={{
                      fontSize: `${fontSize}px`,
                      lineHeight: '1.2',
                      wordWrap: 'break-word',
                      overflowWrap: 'break-word',
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
              className="flex items-center justify-center flex-shrink-0 w-16 h-16 md:w-12 md:h-12 bg-background border-2 border-gray-400 hover:bg-gray-100 hover:border-gray-600 disabled:opacity-30 disabled:cursor-not-allowed shadow-md rounded-md transition-colors"
              style={{ minWidth: '64px', minHeight: '64px' }}
              aria-label="Next"
            >
              <ChevronRight className="w-10 h-10 md:w-8 md:h-8 text-gray-900 dark:text-gray-100" strokeWidth={3} />
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

