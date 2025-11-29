import { useMemo } from 'react';
import type React from 'react';
import type { LessonStep } from '@lesson-api';
import { ExpandableItemView, ExpandableItem } from './ExpandableItemView';
import { Card } from '@lesson-ui/Card';
import { highlightVocabularyWords, extractVocabularyWords } from '../../utils/vocabularyHighlight';

interface SentenceFramesDisplayProps {
  steps: LessonStep[];
  onFrameSelect?: (frameIndex: number) => void;
}


export function SentenceFramesDisplay({
  steps,
  onFrameSelect,
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

  // Find the vocabulary step to extract vocabulary words
  const vocabStep = steps.find(
    (step) =>
      step.step_name?.toLowerCase().includes('vocabulary') ||
      step.step_name?.toLowerCase().includes('cognate')
  );

  // Extract vocabulary words (English) from vocabulary step
  const vocabularyWords = useMemo(() => {
    if (!vocabStep) return [];
    return extractVocabularyWords(vocabStep.vocabulary_cognates);
  }, [vocabStep]);

  // Find the sentence frames step
  const framesStep = steps.find(
    (step) => step.content_type === 'sentence_frames'
  );

  console.log('[SentenceFramesDisplay] Frames step found:', !!framesStep);
  if (framesStep) {
    console.log('[SentenceFramesDisplay] Frames step name:', framesStep.step_name);
    console.log('[SentenceFramesDisplay] Frames step ID:', framesStep.id);
    console.log('[SentenceFramesDisplay] Has sentence_frames:', !!framesStep.sentence_frames);
    console.log('[SentenceFramesDisplay] sentence_frames type:', typeof framesStep.sentence_frames);
    console.log('[SentenceFramesDisplay] sentence_frames value:', framesStep.sentence_frames);
    console.log('[SentenceFramesDisplay] sentence_frames is array:', Array.isArray(framesStep.sentence_frames));
    if (Array.isArray(framesStep.sentence_frames)) {
      console.log('[SentenceFramesDisplay] sentence_frames length:', framesStep.sentence_frames.length);
      console.log('[SentenceFramesDisplay] First frame:', framesStep.sentence_frames[0]);
    }
  } else {
    console.log('[SentenceFramesDisplay] No frames step found. Content types:', 
      steps.map(s => s.content_type)
    );
  }

  // Get all frames in their original order for navigation
  const allFrames = useMemo(() => {
    if (!framesStep || !framesStep.sentence_frames) {
      console.log('[SentenceFramesDisplay] No frames step or sentence_frames is empty');
      return [];
    }
    console.log('[SentenceFramesDisplay] Returning', framesStep.sentence_frames.length, 'frames');
    return framesStep.sentence_frames;
  }, [framesStep]);

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
  }, [allFrames, levelGroups]);

  if (!framesStep) {
    return (
      <Card className="p-8 min-h-[400px]">
        <div className="text-center text-muted-foreground">
          No sentence frames found for this lesson.
        </div>
      </Card>
    );
  }

  const frames = framesStep.sentence_frames || [];

  if (frames.length === 0) {
    return (
      <Card className="p-8 min-h-[400px]">
        <div className="space-y-4">
          <h3 className="text-2xl font-bold text-center">Sentence Frames</h3>
          <div className="text-center text-muted-foreground">
            {framesStep.display_content || 'No sentence frames available.'}
          </div>
        </div>
      </Card>
    );
  }


  // Custom render function for sentence frames
  const renderFrame = (item: ExpandableItem, isExpanded: boolean, textRef?: React.RefObject<HTMLDivElement>, fontSize?: number) => {
    const frame = allFrames[typeof item.id === 'number' ? item.id : 0];
    if (!frame) return null;

    if (isExpanded) {
      return (
        <>
          <div 
            ref={textRef}
            className="font-bold text-center mb-8 md:mb-6 w-full break-words"
            style={{
              fontSize: fontSize ? `${fontSize}px` : '48px',
              lineHeight: '1.3',
              wordWrap: 'break-word',
              overflowWrap: 'break-word',
            }}
          >
            {highlightVocabularyWords(frame.english, vocabularyWords)}
          </div>
          {frame.language_function && (
            <div className="mt-8 md:mt-6 inline-flex items-center rounded-full border-2 px-6 py-3 md:px-4 md:py-2 text-lg md:text-base uppercase tracking-wide text-muted-foreground bg-background">
              {frame.language_function
                .replace(/_/g, ' ')
                .replace(/^\w/, (c: string) => c.toUpperCase())}
            </div>
          )}
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
        <div className="text-2xl md:text-xl font-medium leading-relaxed">{highlightVocabularyWords(frame.english, vocabularyWords)}</div>
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
      onItemSelect={onFrameSelect}
      renderItem={renderFrame}
      title="Sentence Frames / Stems / Questions"
    />
  );
}

