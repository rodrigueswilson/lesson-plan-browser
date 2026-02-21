import { useMemo, useState } from 'react';
import type React from 'react';
import type { LessonStep } from '@lesson-api';
import { ExpandableItemView, ExpandableItem } from './ExpandableItemView';
import { Card } from '@lesson-ui/Card';
import { extractVocabularyWords } from '../../utils/vocabularyHighlight';
import { parseMarkdown } from '../../utils/markdownUtils';
import type { LessonPlanContext } from '../../utils/lessonPlanContext';

interface SentenceFramesDisplayProps {
  steps: LessonStep[];
  onFrameSelect?: (frameIndex: number) => void;
  planContext?: LessonPlanContext | null;
}


export function SentenceFramesDisplay({
  steps,
  onFrameSelect,
  planContext,
}: SentenceFramesDisplayProps) {

  // Debug logging
  console.log('[SentenceFramesDisplay] Total steps:', steps.length);
  console.log('[SentenceFramesDisplay] Step names:', steps.map(s => s.step_name));
  console.log('[SentenceFramesDisplay] Step content types:', steps.map(s => s.content_type));
  console.log('[SentenceFramesDisplay] Steps with sentence_frames:', steps.map(s => ({
    name: s.step_name,
    content_type: s.content_type,
    has_frames: !!s.sentence_frames,
    frames_type: typeof s.sentence_frames,
    frames_length: Array.isArray(s.sentence_frames) ? s.sentence_frames.length : 'N/A',
  })));

  // Get fallback frames from lesson plan context (Master Plan)
  const masterPlanFrames = useMemo(() => {
    if (!planContext) return [];
    const slotFrames = planContext.slotData?.sentence_frames;
    const dayFrames = planContext.dayData?.sentence_frames;
    const source = Array.isArray(slotFrames) ? slotFrames : Array.isArray(dayFrames) ? dayFrames : null;
    return Array.isArray(source) ? source : [];
  }, [planContext]);

  // Find the vocabulary step to extract vocabulary words
  const vocabStep = steps.find(
    (step) =>
      step.step_name?.toLowerCase().includes('vocabulary') ||
      step.step_name?.toLowerCase().includes('cognate')
  );

  // Extract vocabulary words (English) from master plan or vocabulary step
  const vocabularyWords = useMemo(() => {
    // Priority 1: Master Plan (Live JSON)
    if (planContext?.slotData?.vocabulary_cognates && Array.isArray(planContext.slotData.vocabulary_cognates)) {
      console.log('[SentenceFramesDisplay] Using vocabulary from Master Plan (Live JSON)');
      return extractVocabularyWords(planContext.slotData.vocabulary_cognates);
    }

    // Priority 2: Cache (Steps)
    if (vocabStep) {
      console.log('[SentenceFramesDisplay] Using vocabulary from Cache (Steps)');
      return extractVocabularyWords(vocabStep.vocabulary_cognates);
    }

    return [];
  }, [planContext, vocabStep]);

  // Find the sentence frames step
  const framesStep = steps.find(
    (step) => step.content_type === 'sentence_frames'
  );

  // Logic to determine which frames to use
  const allFrames = useMemo(() => {
    let frames = [];

    // Priority 1: Master Plan (Live JSON) - This ensures we show the latest prompt results
    if (masterPlanFrames.length > 0) {
      console.log('[SentenceFramesDisplay] Using frames from Master Plan (Live JSON):', masterPlanFrames.length);
      frames = masterPlanFrames;
    }
    // Priority 2: Cache (Steps) - Fallback for backward compatibility
    else if (framesStep?.sentence_frames && Array.isArray(framesStep.sentence_frames) && framesStep.sentence_frames.length > 0) {
      console.log('[SentenceFramesDisplay] Using frames from Cache (Steps):', framesStep.sentence_frames.length);
      frames = framesStep.sentence_frames;
    }

    if (frames.length === 0) return [];

    // Explicitly sort by proficiency level: 1-2, then 3-4, then 5-6
    const levelOrder: Record<string, number> = {
      'levels_1_2': 1,
      'levels_3_4': 2,
      'levels_5_6': 3
    };

    return [...frames].sort((a: any, b: any) => {
      const orderA = levelOrder[a.proficiency_level] || 99;
      const orderB = levelOrder[b.proficiency_level] || 99;
      return orderA - orderB;
    });
  }, [framesStep, masterPlanFrames]);

  // Group frames by proficiency level for the list view
  const levelGroups = [
    { key: 'levels_1_2', label: 'Levels 1-2' },
    { key: 'levels_3_4', label: 'Levels 3-4' },
    { key: 'levels_5_6', label: 'Levels 5-6' },
  ] as const;

  // Convert frames to ExpandableItem format
  const expandableItems: ExpandableItem[] = useMemo(() => {
    return allFrames.map((frame: any, idx: number) => ({
      id: idx,
      primaryText: frame.english || '',
      badge: frame.language_function
        ? frame.language_function.replace(/_/g, ' ').replace(/^\w/, (c: string) => c.toUpperCase())
        : undefined,
      metadata: levelGroups.find(g => g.key === frame.proficiency_level)?.label,
    }));
  }, [allFrames]);

  if (allFrames.length === 0) {
    return (
      <Card className="p-8 min-h-[400px]">
        <div className="text-center text-muted-foreground">
          No sentence frames found for this lesson.
        </div>
      </Card>
    );
  }


  // State to track if the current expanded card is showing Portuguese
  const [showPortuguese, setShowPortuguese] = useState(false);

  // Reset flip state when the selected item changes
  const handleFrameSelect = (idx: number) => {
    setShowPortuguese(false);
    onFrameSelect?.(idx);
  };

  // Custom render function for sentence frames
  const renderFrame = (item: ExpandableItem, isExpanded: boolean, textRef?: React.RefObject<HTMLDivElement>, fontSize?: number) => {
    const frame = allFrames[typeof item.id === 'number' ? item.id : 0];
    if (!frame) return null;

    if (isExpanded) {
      return (
        <>
          {/* Flag Toggle Button in top-right corner */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowPortuguese(!showPortuguese);
            }}
            className="absolute top-4 right-4 z-10 p-2 bg-background/80 hover:bg-background border shadow-sm rounded-lg transition-all active:scale-95 flex items-center justify-center"
            title={showPortuguese ? "Switch to English" : "Switch to Portuguese"}
          >
            {/Android|Capacitor/i.test(navigator.userAgent) ? (
              <span className="text-2xl md:text-xl">
                {showPortuguese ? "🇺🇸" : "🇵🇹🇧🇷"}
              </span>
            ) : (
              showPortuguese ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" className="w-8 h-8 md:w-6 md:h-6">
                  <g fillRule="evenodd">
                    <path fill="#bd3d44" d="M0 0h640v480H0" />
                    <path stroke="#fff" strokeWidth="37" d="M0 55.3h640M0 129h640M0 203h640M0 277h640M0 351h640M0 425h640" />
                    <path fill="#192f5d" d="M0 0h247v221H0" />
                    <path fill="#fff" d="M16 16h11v11H16zm27 0h11v11H43zm27 0h11v11H70zm27 0h11v11H97zM29 34h11v11H29zm27 0h11v11H56zm27 0h11v11H83zm-54 18h11v11H29zm27 0h11v11H56zm27 0h11v11H83zm-54 18h11v11H29zm27 0h11v11H56zm27 0h11v11H83zm-54 18h11v11H29zm27 0h11v11H56zm27 0h11v11H83zm-54 18h11v11H29zm27 0h11v11H56zm27 0h11v11H83z" />
                  </g>
                </svg>
              ) : (
                <div className="flex gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" className="w-8 h-8 md:w-6 md:h-6">
                    <path fill="#f00" d="M0 0h240v480h400V0H0z" />
                    <path fill="#006600" d="M0 0h240v480H0z" />
                    <path fill="#ff0" d="M240 135c58 0 105 47 105 105s-47 105-105 105-105-47-105-105 47-105 105-105z" stroke="#000" strokeWidth="0" />
                    <path fill="#fff" d="M240 180c40 0 40 40 40 40v40c0 40-18 56-40 56s-40-16-40-56v-40c0-40 0-40 40-40" stroke="#f00" strokeWidth="8" />
                    <path fill="#fff" d="M220 220h40v40h-40z" stroke="#000" strokeWidth="0" />
                    <path fill="#0000ff" d="M225 220h10v10h-10zm20 0h10v10h-10zm-20 20h10v10h-10zm20 0h10v10h-10z" />
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" className="w-8 h-8 md:w-6 md:h-6">
                    <path fill="#009c3b" d="M0 0h640v480H0z" />
                    <path fill="#ffdf00" d="m320 38.4 272.9 201.6L320 441.6 47.1 240z" />
                    <circle cx="320" cy="240" r="111.4" fill="#002776" />
                    <path fill="#fff" d="M320 240h.1" stroke="#fff" strokeWidth="8" />
                  </svg>
                </div>
              ))}
          </button>

          <div
            ref={textRef}
            className="font-bold text-center mb-8 md:mb-6 w-full"
            style={{
              fontSize: fontSize ? `${fontSize}px` : '48px',
              lineHeight: '1.3',
              wordWrap: 'normal',
              overflowWrap: 'normal',
              wordBreak: 'normal',
              hyphens: 'none',
              // Add a slight fade transition when flipping
              transition: 'opacity 0.2s ease-in-out',
            }}
          >
            {showPortuguese ? (
              // No vocabulary highlighting for Portuguese frames currently
              frame.portuguese || ''
            ) : (
              parseMarkdown(frame.english, vocabularyWords)
            )}
          </div>

          <div className="flex flex-wrap justify-center gap-3 mt-8 md:mt-6">
            {frame.language_function && (
              <div className="inline-flex items-center rounded-full border-2 px-6 py-3 md:px-4 md:py-2 text-lg md:text-base uppercase tracking-wide text-muted-foreground bg-background">
                {frame.language_function
                  .replace(/_/g, ' ')
                  .replace(/^\w/, (c: string) => c.toUpperCase())}
              </div>
            )}

            {/* Show an indicator that this is the Portuguese version when flipped */}
            {showPortuguese && (
              <div className="inline-flex items-center rounded-full border-2 border-green-200 px-6 py-3 md:px-4 md:py-2 text-lg md:text-base uppercase tracking-wide text-green-700 bg-green-50 dark:bg-green-900/30 dark:text-green-300">
                Tradução (PT)
              </div>
            )}
          </div>

          {item.metadata && (
            <div className="mt-6 md:mt-4 text-xl md:text-base text-muted-foreground font-medium">
              {item.metadata}
            </div>
          )}
        </>
      );
    }

    return (
      <div className="p-6 md:p-4 bg-muted rounded-lg">
        <div className="text-2xl md:text-xl font-medium leading-relaxed">{parseMarkdown(frame.english, vocabularyWords)}</div>
        {frame.portuguese && (
          <div className="text-base md:text-sm text-muted-foreground italic mt-2 opacity-80">
            {frame.portuguese}
          </div>
        )}
        {frame.language_function && (
          <div className="mt-3 md:mt-2 inline-flex items-center rounded-full border px-3 py-1 md:px-2 md:py-0.5 text-sm md:text-xs uppercase tracking-wide text-muted-foreground">
            {frame.language_function
              .replace(/_/g, ' ')
              .replace(/^\w/, (c: string) => c.toUpperCase())}
          </div>
        )}
      </div>
    );
  };

  if (expandableItems.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          No sentence frames found for this lesson.
        </div>
      </div>
    );
  }

  return (
    <ExpandableItemView
      items={expandableItems}
      onItemSelect={handleFrameSelect}
      renderItem={renderFrame}
      title="Sentence Frames / Stems / Questions"
    />
  );
}

