/**
 * Shared font size calculation utilities following SSO and DRY principles
 */

export interface FontSizeCalculationParams {
  text: string;
  textElement: HTMLElement;
  container: HTMLElement;
  otherElementsHeight?: number;
  headingHeight?: number;
  minSize?: number;
  maxSize?: number;
  fontWeight?: string;
  lineHeight?: string;
  textAlign?: 'center' | 'left' | 'right';
}

/**
 * Calculate the maximum font size that fits within the container
 */
export function calculateMaxFittingSize(params: FontSizeCalculationParams): number {
  const {
    text,
    textElement,
    container,
    otherElementsHeight = 0,
    headingHeight = 0,
    minSize = 20,
    maxSize = 200,
    fontWeight,
    lineHeight,
    textAlign = 'center',
  } = params;

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
    return maxSize;
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
  let max = maxSize;
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
  return Math.min(maxFitting, maxSize);
}

/**
 * Calculate optimal font size for auto-calculation (up to maxAutoSize)
 * Returns the optimal size and also calculates the true maximum that fits
 */
export function calculateOptimalFontSize(params: FontSizeCalculationParams & { maxAutoSize?: number }): {
  optimalSize: number;
  maxFittingSize: number;
} {
  const {
    text,
    textElement,
    container,
    otherElementsHeight = 0,
    headingHeight = 0,
    minSize = 20,
    maxAutoSize = 80,
    fontWeight,
    lineHeight,
    textAlign = 'center',
  } = params;

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
    return { optimalSize: minSize, maxFittingSize: 200 };
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
  
  // Calculate true maximum that fits (up to 200px)
  const maxFittingSize = calculateMaxFittingSize({
    text,
    textElement,
    container,
    otherElementsHeight,
    headingHeight,
    minSize,
    maxSize: 200,
    fontWeight,
    lineHeight,
    textAlign,
  });
  
  return { optimalSize, maxFittingSize };
}

