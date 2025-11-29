import { useMemo } from 'react';
import type React from 'react';
import type { LessonStep } from '@lesson-api';
import { ExpandableItemView, ExpandableItem } from './ExpandableItemView';
import { getCognateBadgeClasses } from '../../utils/vocabularyHighlight';
import type { LessonPlanContext } from '../../utils/lessonPlanContext';

interface VocabularyDisplayProps {
  steps: LessonStep[];
  planContext?: LessonPlanContext | null;
}

export function VocabularyDisplay({ steps, planContext }: VocabularyDisplayProps) {
  // Debug logging - show all step names and vocabulary_cognates
  console.log('[VocabularyDisplay] Total steps:', steps.length);
  console.log('[VocabularyDisplay] Step names:', steps.map(s => s.step_name));
  console.log('[VocabularyDisplay] Step content types:', steps.map(s => s.content_type));
  console.log('[VocabularyDisplay] Steps with vocabulary_cognates:', steps.map(s => ({
    name: s.step_name,
    has_vocab: !!s.vocabulary_cognates,
    vocab_type: typeof s.vocabulary_cognates,
    vocab_length: Array.isArray(s.vocabulary_cognates) ? s.vocabulary_cognates.length : 'N/A',
  })));
  
  // Find the vocabulary step
  const vocabStep = steps.find(
    (step) =>
      step.step_name?.toLowerCase().includes('vocabulary') ||
      step.step_name?.toLowerCase().includes('cognate')
  );

  // Debug logging
  console.log('[VocabularyDisplay] Vocab step found:', !!vocabStep);
  if (vocabStep) {
    console.log('[VocabularyDisplay] Vocab step name:', vocabStep.step_name);
    console.log('[VocabularyDisplay] Vocab step ID:', vocabStep.id);
    console.log('[VocabularyDisplay] Has vocabulary_cognates:', !!vocabStep.vocabulary_cognates);
    console.log('[VocabularyDisplay] vocabulary_cognates type:', typeof vocabStep.vocabulary_cognates);
    console.log('[VocabularyDisplay] vocabulary_cognates value:', vocabStep.vocabulary_cognates);
    console.log('[VocabularyDisplay] vocabulary_cognates is array:', Array.isArray(vocabStep.vocabulary_cognates));
    if (Array.isArray(vocabStep.vocabulary_cognates)) {
      console.log('[VocabularyDisplay] vocabulary_cognates length:', vocabStep.vocabulary_cognates.length);
      console.log('[VocabularyDisplay] First item:', vocabStep.vocabulary_cognates[0]);
    }
    console.log('[VocabularyDisplay] Has display_content:', !!vocabStep.display_content);
    console.log('[VocabularyDisplay] Display content length:', vocabStep.display_content?.length || 0);
  } else {
    console.log('[VocabularyDisplay] No vocab step found. Searching for steps with:', 
      steps.map(s => ({ 
        name: s.step_name, 
        includes_vocab: s.step_name.toLowerCase().includes('vocabulary'), 
        includes_cognate: s.step_name.toLowerCase().includes('cognate'),
        has_vocab_field: 'vocabulary_cognates' in s,
      }))
    );
  }

  const fallbackVocabulary = useMemo(() => {
    if (!planContext) return [];
    const slotVocab = planContext.slotData?.vocabulary_cognates;
    const dayVocab = planContext.dayData?.vocabulary_cognates;
    const vocabSource = Array.isArray(slotVocab) ? slotVocab : Array.isArray(dayVocab) ? dayVocab : null;
    return Array.isArray(vocabSource) ? vocabSource : [];
  }, [planContext]);

  // Parse vocabulary from display_content or use structured data
  const vocabularyItems: ExpandableItem[] = useMemo(() => {
    const mapVocabArray = (items: any[]) =>
      items.map((vocab: any, idx: number) => ({
        id: idx,
        primaryText: vocab.english || '',
        secondaryText: vocab.portuguese || '',
        badge: vocab.is_cognate ? 'Cognate' : vocab.is_non_cognate ? 'Non-Cognate' : undefined,
        metadata: vocab.relevance_note || undefined,
      }));

    if (!vocabStep) {
      if (fallbackVocabulary.length > 0) {
        console.log('[VocabularyDisplay] Using fallback vocabulary from lesson plan context:', fallbackVocabulary.length);
        return mapVocabArray(fallbackVocabulary);
      }
      console.log('[VocabularyDisplay] No vocab step found and no fallback data');
      return [];
    }

    // Try to use structured vocabulary_cognates if available
    if (vocabStep.vocabulary_cognates && Array.isArray(vocabStep.vocabulary_cognates)) {
      console.log('[VocabularyDisplay] Using structured vocabulary_cognates:', vocabStep.vocabulary_cognates.length, 'items');
      return mapVocabArray(vocabStep.vocabulary_cognates);
    }

    if (fallbackVocabulary.length > 0) {
      console.log('[VocabularyDisplay] Structured vocab missing, using fallback array');
      return mapVocabArray(fallbackVocabulary);
    }

    // Fallback: Parse from display_content
    // Format: "- english -> portuguese"
    console.log('[VocabularyDisplay] Parsing from display_content');
    const lines = (vocabStep.display_content || '')
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.startsWith('-') || line.startsWith('•'));
    
    console.log('[VocabularyDisplay] Found', lines.length, 'vocabulary lines');

    return lines.map((line, idx) => {
      const content = line.replace(/^[-•]\s*/, '');
      const parts = content.split('->').map((part) => part.trim());
      const english = parts[0] || '';
      const portuguese = parts[1] || '';

      return {
        id: idx,
        primaryText: english || content,
        secondaryText: portuguese || undefined,
      };
    });
  }, [vocabStep]);

  // Custom render function for vocabulary items
  const renderVocabulary = (item: ExpandableItem, isExpanded: boolean, textRef?: React.RefObject<HTMLDivElement>, fontSize?: number) => {
    if (isExpanded) {
      return (
        <>
          <div 
            ref={textRef}
            className="font-bold text-center mb-6 w-full"
            style={{
              fontSize: fontSize ? `${fontSize}px` : undefined,
              lineHeight: '1.2',
              wordWrap: 'normal',
              overflowWrap: 'normal',
              wordBreak: 'normal',
              hyphens: 'none',
            }}
          >
            {item.primaryText}
          </div>
          {item.secondaryText && (
            <div className="text-3xl md:text-4xl text-center text-muted-foreground italic mb-4">
              {item.secondaryText}
            </div>
          )}
          {item.badge && (
            <div className={`mt-6 ${getCognateBadgeClasses(item.badge === 'Cognate', 'md')}`}>
              {item.badge}
            </div>
          )}
          {item.metadata && (
            <div className="mt-4 text-sm md:text-base text-muted-foreground text-center max-w-2xl mx-auto">
              {item.metadata}
            </div>
          )}
        </>
      );
    }

    return (
      <div className="p-4 bg-muted rounded-lg">
        <div className="text-xl font-medium">{item.primaryText}</div>
        {item.secondaryText && (
          <div className="text-muted-foreground italic mt-2">
            {item.secondaryText}
          </div>
        )}
        {item.badge && (
          <div className={`mt-2 ${getCognateBadgeClasses(item.badge === 'Cognate', 'sm')}`}>
            {item.badge}
          </div>
        )}
      </div>
    );
  };

  if (vocabularyItems.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          No vocabulary found for this lesson.
        </div>
      </div>
    );
  }

  return (
    <ExpandableItemView
      items={vocabularyItems}
      renderItem={renderVocabulary}
      title="Vocabulary / Cognate Awareness"
    />
  );
}

