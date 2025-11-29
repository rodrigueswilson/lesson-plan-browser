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
  // First try to use objective from lesson plan data
  // If not available, try to find objective step
  const objectiveStep = steps.find(
    (step) => step.content_type === 'objective'
  );

  const objectiveText = objective || objectiveStep?.display_content || null;

  console.log('[ObjectiveDisplay] Objective prop:', objective);
  console.log('[ObjectiveDisplay] Objective step:', objectiveStep);
  console.log('[ObjectiveDisplay] Final objective text:', objectiveText);

  // Calculate optimal font size based on text length and container width
  const calculateFontSize = useCallback(() => {
    if (objectiveText && textRef.current && containerRef.current) {
      const container = containerRef.current;
      const textElement = textRef.current;
      
      // Get container dimensions (accounting for padding)
      const containerWidth = container.offsetWidth - 128; // Subtract padding (64px on each side)
      const containerHeight = container.offsetHeight - 150; // Subtract space for heading
      
      if (containerWidth <= 0 || containerHeight <= 0) return;
      
      // Create a temporary element to measure text
      const measureElement = document.createElement('div');
      measureElement.style.position = 'absolute';
      measureElement.style.visibility = 'hidden';
      measureElement.style.whiteSpace = 'normal';
      measureElement.style.wordWrap = 'break-word';
      measureElement.style.overflowWrap = 'break-word';
      measureElement.style.width = `${containerWidth}px`;
      measureElement.style.fontWeight = 'medium';
      measureElement.style.fontFamily = getComputedStyle(textElement).fontFamily;
      measureElement.style.lineHeight = '1.5';
      document.body.appendChild(measureElement);
      
      // Binary search for optimal font size
      let minSize = 24;
      let maxSize = 256;
      let optimalSize = 64;
      
      while (minSize <= maxSize) {
        const testSize = Math.floor((minSize + maxSize) / 2);
        measureElement.style.fontSize = `${testSize}px`;
        measureElement.textContent = objectiveText;
        
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
  }, [objectiveText]);

  useEffect(() => {
    if (objectiveText) {
      // Small delay to ensure DOM is ready
      const timeoutId = setTimeout(() => {
        calculateFontSize();
      }, 100);
      
      return () => clearTimeout(timeoutId);
    }
  }, [objectiveText, calculateFontSize]);

  // Recalculate on window resize
  useEffect(() => {
    if (objectiveText) {
      const handleResize = () => {
        calculateFontSize();
      };
      
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
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
          className="text-center leading-relaxed whitespace-pre-wrap font-medium w-full break-words"
          style={{
            fontSize: `${fontSize}px`,
            lineHeight: '1.5',
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
          }}
        >
          {objectiveText}
        </div>
      </div>
    </div>
  );
}

