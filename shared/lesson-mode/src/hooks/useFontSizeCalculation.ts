import { useState, useRef, useCallback, useEffect } from 'react';

interface UseFontSizeCalculationOptions {
  text: string;
  textRef: React.RefObject<HTMLDivElement>;
  containerRef: React.RefObject<HTMLDivElement>;
  otherElementsHeight?: number; // Height of other elements in container (badges, metadata, etc.)
  headingHeight?: number; // Height of heading element (for objective)
  minSize?: number; // Minimum font size (default: 20)
  maxAutoSize?: number; // Maximum for auto-calculation (default: 80)
  maxManualSize?: number; // Maximum for manual adjustment (default: 200)
  fontWeight?: string; // Font weight override
  lineHeight?: string; // Line height override
  textAlign?: 'center' | 'left' | 'right'; // Text alignment
}

export function useFontSizeCalculation({
  text,
  textRef,
  containerRef,
  otherElementsHeight = 0,
  headingHeight = 0,
  minSize = 20,
  maxAutoSize = 80,
  maxManualSize = 200,
  fontWeight,
  lineHeight,
  textAlign = 'center',
}: UseFontSizeCalculationOptions) {
  const [fontSize, setFontSize] = useState<number>(64);
  const [isManualAdjustment, setIsManualAdjustment] = useState<boolean>(false);
  const [maxFittingSize, setMaxFittingSize] = useState<number>(maxManualSize);
  const isCalculatingRef = useRef<boolean>(false);
  const lastContainerSizeRef = useRef<{ width: number; height: number } | null>(null);
  const lastFontSizeRef = useRef<number | null>(null);
  
  // Touch gesture tracking for pinch-to-zoom
  const touchStartDistanceRef = useRef<number | null>(null);
  const touchStartFontSizeRef = useRef<number | null>(null);

  // Calculate maximum font size that fits in container
  const calculateMaxFittingSize = useCallback((): number => {
    if (!text || !textRef.current || !containerRef.current) {
      return maxManualSize;
    }

    const textElement = textRef.current;
    const container = containerRef.current;
    const computedStyle = window.getComputedStyle(textElement);
    const containerComputedStyle = window.getComputedStyle(container);
    const containerRect = container.getBoundingClientRect();
    const containerPadding = {
      top: parseFloat(containerComputedStyle.paddingTop) || 0,
      right: parseFloat(containerComputedStyle.paddingRight) || 0,
      bottom: parseFloat(containerComputedStyle.paddingBottom) || 0,
      left: parseFloat(containerComputedStyle.paddingLeft) || 0,
    };
    
    const availableWidth = containerRect.width - containerPadding.left - containerPadding.right;
    const availableHeight = containerRect.height - containerPadding.top - containerPadding.bottom - otherElementsHeight - headingHeight - 20;
    
    if (availableWidth <= 0 || availableHeight <= 0) {
      return maxManualSize;
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
    measureElement.style.fontWeight = fontWeight || computedStyle.fontWeight || 'bold';
    measureElement.style.fontFamily = computedStyle.fontFamily;
    measureElement.style.fontStyle = computedStyle.fontStyle;
    measureElement.style.letterSpacing = computedStyle.letterSpacing;
    measureElement.style.textAlign = textAlign;
    measureElement.style.lineHeight = lineHeight || computedStyle.lineHeight || '1.2';
    
    if (textElement.innerHTML && textElement.innerHTML.trim().length > 0) {
      const clone = textElement.cloneNode(true) as HTMLElement;
      clone.style.fontSize = '';
      measureElement.innerHTML = clone.innerHTML;
    } else {
      measureElement.textContent = text;
    }
    
    document.body.appendChild(measureElement);
    
    const maxHeight = availableHeight;
    const maxWidth = availableWidth;
    const words = text.split(/\s+/);
    
    // Binary search for maximum fitting size
    let min = minSize;
    let max = maxManualSize;
    let maxFitting = minSize;
    
    for (let i = 0; i < 20; i++) {
      const testSize = Math.floor((min + max) / 2);
      measureElement.style.fontSize = `${testSize}px`;
      void measureElement.offsetHeight;
      
      const textHeight = measureElement.scrollHeight;
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
      
      if (textHeight <= maxHeight && longestWordWidth <= maxWidth) {
        maxFitting = testSize;
        min = testSize + 1;
      } else {
        max = testSize - 1;
      }
    }
    
    document.body.removeChild(measureElement);
    return Math.min(maxFitting, maxManualSize);
  }, [text, textRef, containerRef, otherElementsHeight, headingHeight, minSize, maxManualSize, fontWeight, lineHeight, textAlign]);

  // Calculate optimal font size for auto-calculation (up to maxAutoSize)
  const calculateFontSize = useCallback(() => {
    if (isCalculatingRef.current) {
      return;
    }
    
    if (!text || !textRef.current || !containerRef.current) {
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
    
    const availableWidth = containerRect.width - containerPadding.left - containerPadding.right;
    const availableHeight = containerRect.height - containerPadding.top - containerPadding.bottom - otherElementsHeight - headingHeight - 20;
    
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
    measureElement.style.fontWeight = fontWeight || computedStyle.fontWeight || 'bold';
    measureElement.style.fontFamily = computedStyle.fontFamily;
    measureElement.style.fontStyle = computedStyle.fontStyle;
    measureElement.style.letterSpacing = computedStyle.letterSpacing;
    measureElement.style.textAlign = textAlign;
    measureElement.style.lineHeight = lineHeight || computedStyle.lineHeight || '1.2';
    measureElement.style.boxSizing = 'border-box';
    measureElement.style.padding = '0';
    measureElement.style.margin = '0';
    
    if (textElement.innerHTML && textElement.innerHTML.trim().length > 0) {
      const clone = textElement.cloneNode(true) as HTMLElement;
      clone.style.fontSize = '';
      measureElement.innerHTML = clone.innerHTML;
    } else if (textElement.textContent) {
      measureElement.textContent = textElement.textContent;
    } else {
      measureElement.textContent = text;
    }
    
    document.body.appendChild(measureElement);
    
    const maxHeight = availableHeight;
    const maxWidth = availableWidth;
    const textLength = text.length || textElement.textContent?.length || 100;
    const areaRatio = (availableWidth * availableHeight) / (textLength * 100);
    const estimatedSize = Math.min(Math.max(Math.sqrt(areaRatio) * 20, 32), 512);
    
    let optimalSize = Math.min(estimatedSize * 1.5, maxAutoSize);
    let min = minSize;
    let max = maxAutoSize;
    let iterations = 0;
    const maxIterations = 40;
    
    while (min <= max && iterations < maxIterations) {
      iterations++;
      const testSize = Math.floor((min + max) / 2);
      measureElement.style.fontSize = `${testSize}px`;
      void measureElement.offsetHeight;
      
      const textHeight = measureElement.scrollHeight;
      const words = text.split(/\s+/);
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
        min = testSize + 1;
      } else {
        max = testSize - 1;
      }
    }
    
    optimalSize = Math.min(optimalSize, maxAutoSize);
    measureElement.style.fontSize = `${optimalSize}px`;
    void measureElement.offsetHeight;
    
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
    
    while ((measureElement.scrollHeight > maxHeight || 
            longestWordWidth > maxWidth) && 
           optimalSize > minSize) {
      optimalSize -= 1;
      measureElement.style.fontSize = `${optimalSize}px`;
      void measureElement.offsetHeight;
    }
    
    let testLarger = optimalSize + 1;
    let maxAttempts = 20;
    while (testLarger <= maxAutoSize && maxAttempts > 0) {
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
    
    setFontSize(optimalSize);
    // Set maxFittingSize to optimalSize initially (as requested)
    setMaxFittingSize(optimalSize);
    lastFontSizeRef.current = optimalSize;
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
        // Calculate and update to true maximum after a delay to ensure layout is ready
        requestAnimationFrame(() => {
          const trueMax = calculateMaxFittingSize();
          setMaxFittingSize(trueMax);
        });
      }, 200);
    } else {
      setTimeout(() => {
        isCalculatingRef.current = false;
        requestAnimationFrame(() => {
          const trueMax = calculateMaxFittingSize();
          setMaxFittingSize(trueMax);
        });
      }, 200);
    }
  }, [text, textRef, containerRef, otherElementsHeight, headingHeight, minSize, maxAutoSize, fontSize, fontWeight, lineHeight, textAlign, calculateMaxFittingSize]);

  // Adjust font size with constraints
  const adjustFontSize = useCallback((delta: number) => {
    setFontSize((prevSize) => {
      const newSize = Math.max(minSize, Math.min(maxFittingSize, prevSize + delta));
      setIsManualAdjustment(true);
      lastFontSizeRef.current = newSize;
      return newSize;
    });
  }, [maxFittingSize, minSize]);

  // Calculate distance between two touch points
  const getTouchDistance = (touch1: Touch, touch2: Touch): number => {
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
      e.preventDefault();
      const currentDistance = getTouchDistance(e.touches[0], e.touches[1]);
      const scale = currentDistance / touchStartDistanceRef.current;
      const newSize = Math.max(minSize, Math.min(maxFittingSize, touchStartFontSizeRef.current * scale));
      setFontSize(newSize);
      lastFontSizeRef.current = newSize;
    }
  }, [maxFittingSize, minSize]);

  // Handle touch end
  const handleTouchEnd = useCallback(() => {
    touchStartDistanceRef.current = null;
    touchStartFontSizeRef.current = null;
  }, []);

  // Handle mouse wheel scroll to adjust font size
  const handleWheel = useCallback((e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -2 : 2;
    adjustFontSize(delta);
  }, [adjustFontSize]);

  // Reset font size calculation state
  const resetCalculation = useCallback(() => {
    isCalculatingRef.current = false;
    lastContainerSizeRef.current = null;
    lastFontSizeRef.current = null;
    setIsManualAdjustment(false);
    setFontSize(64);
  }, []);

  return {
    fontSize,
    isManualAdjustment,
    maxFittingSize,
    calculateFontSize,
    calculateMaxFittingSize,
    adjustFontSize,
    handleWheel,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    resetCalculation,
    setFontSize,
    setIsManualAdjustment,
    setMaxFittingSize,
  };
}

