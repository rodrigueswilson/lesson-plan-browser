import { Card } from '@lesson-ui/Card';
import type { LessonStep } from '@lesson-api';
import { getCognateBadgeClasses, getCognateBadgeLabel } from '../utils/vocabularyHighlight';
import { parseMarkdown } from '../utils/markdownUtils';

interface StepContentDisplayProps {
  step: LessonStep;
  vocabularyWords?: string[]; // Optional vocabulary words for highlighting in sentence frames
}

export function StepContentDisplay({ step, vocabularyWords = [] }: StepContentDisplayProps) {
  const renderContent = () => {
    switch (step.content_type) {
      case 'objective':
        return (
          <div className="space-y-4">
            <h3 className="text-2xl font-bold text-center">Objective</h3>
            <div className="text-lg text-center leading-relaxed">
              {parseMarkdown(step.display_content, vocabularyWords)}
            </div>
          </div>
        );

      case 'sentence_frames':
        return (
          <div className="space-y-6">
            <div className="space-y-2 mb-6">
              <h3 className="text-2xl font-bold text-center">Sentence Frames</h3>
              <p className="text-sm text-muted-foreground text-center">
                Sentence Frames / Stems / Questions
              </p>
            </div>
            {step.sentence_frames && step.sentence_frames.length > 0 ? (
              <div className="space-y-8">
                {([
                  { key: 'levels_1_2', label: 'Levels 1-2' },
                  { key: 'levels_3_4', label: 'Levels 3-4' },
                  { key: 'levels_5_6', label: 'Levels 5-6' },
                ] as const).map((group) => {
                  const framesForLevel = step.sentence_frames!.filter(
                    (frame) => frame.proficiency_level === group.key
                  );

                  if (framesForLevel.length === 0) {
                    return null;
                  }

                  return (
                    <div key={group.key} className="space-y-4">
                      <h4 className="text-xl font-semibold text-center">{group.label}</h4>
                      <div className="space-y-6">
                        {framesForLevel.map((frame, idx) => (
                          <div key={idx} className="space-y-3">
                            <div className="p-4 bg-muted rounded-lg">
                              <div className="text-sm text-muted-foreground mb-2">PT:</div>
                              <div className="text-xl font-medium">{frame.portuguese}</div>
                            </div>
                            <div className="p-4 bg-muted rounded-lg">
                              <div className="text-sm text-muted-foreground mb-2">EN:</div>
                              <div className="text-xl font-medium">{parseMarkdown(frame.english, vocabularyWords)}</div>
                              {frame.language_function && (
                                <div className="mt-2 inline-flex items-center rounded-full border px-2 py-0.5 text-xs uppercase tracking-wide text-muted-foreground">
                                  {frame.language_function
                                    .replace(/_/g, ' ')
                                    .replace(/^\w/, (c) => c.toUpperCase())}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-muted-foreground">
                {parseMarkdown(step.display_content, vocabularyWords)}
              </div>
            )}
          </div>
        );

      case 'materials':
        return (
          <div className="space-y-4">
            <h3 className="text-2xl font-bold">Materials Needed</h3>
            {step.materials_needed && step.materials_needed.length > 0 ? (
              <ul className="list-disc list-inside space-y-2 text-lg">
                {step.materials_needed.map((material, idx) => (
                  <li key={idx}>{material}</li>
                ))}
              </ul>
            ) : (
              <div className="text-muted-foreground">
                {parseMarkdown(step.display_content, vocabularyWords)}
              </div>
            )}
          </div>
        );

      case 'instruction':
        if (step.step_name === 'Vocabulary / Cognate Awareness') {
          // Try to use structured vocabulary_cognates if available
          if (step.vocabulary_cognates && Array.isArray(step.vocabulary_cognates) && step.vocabulary_cognates.length > 0) {
            return (
              <div className="space-y-4">
                <h3 className="text-2xl font-bold">Vocabulary / Cognate Awareness</h3>
                <ul className="list-disc list-inside space-y-2 text-lg">
                  {step.vocabulary_cognates.map((vocab: any, idx: number) => (
                    <li key={idx}>
                      <strong>{vocab.english || ''}</strong>
                      {' -> '}
                      <em>{vocab.portuguese || ''}</em>
                      <span
                        className={`ml-2 ${getCognateBadgeClasses(vocab.is_cognate, 'sm')}`}
                        style={{
                          color: vocab.is_cognate ? '#15803d' : '#dc2626' // green-700 : red-700
                        }}
                      >
                        {getCognateBadgeLabel(vocab.is_cognate)}
                      </span>
                      {vocab.relevance_note && (
                        <span className="block text-sm text-muted-foreground mt-1">
                          {vocab.relevance_note}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            );
          }

          // Fallback: Parse from display_content
          const lines = (step.display_content || '')
            .split('\n')
            .map((line) => line.trim())
            .filter((line) => line.startsWith('-'));

          return (
            <div className="space-y-4">
              <h3 className="text-2xl font-bold">Vocabulary / Cognate Awareness</h3>
              {lines.length > 0 ? (
                <ul className="list-disc list-inside space-y-2 text-lg">
                  {lines.map((line, idx) => {
                    const content = line.replace(/^[-•]\s*/, '');
                    const parts = content.split('->').map((part) => part.trim());
                    const english = parts[0] || '';
                    const portuguese = parts[1] || '';

                    if (english && portuguese) {
                      return (
                        <li key={idx}>
                          <strong>{english}</strong>{' -> '}<em>{portuguese}</em>
                        </li>
                      );
                    }

                    return <li key={idx}>{content}</li>;
                  })}
                </ul>
              ) : (
                <div className="text-lg leading-relaxed whitespace-pre-wrap">
                  {parseMarkdown(step.display_content, vocabularyWords)}
                </div>
              )}
            </div>
          );
        }

        return (
          <div className="space-y-4">
            <h3 className="text-2xl font-bold">{step.step_name}</h3>
            <div className="text-lg leading-relaxed whitespace-pre-wrap">
              {parseMarkdown(step.display_content, vocabularyWords)}
            </div>
          </div>
        );

      case 'assessment':
        return (
          <div className="space-y-4">
            <h3 className="text-2xl font-bold text-center">Assessment</h3>
            <div className="text-lg leading-relaxed">
              {parseMarkdown(step.display_content, vocabularyWords)}
            </div>
          </div>
        );

      default:
        return (
          <div className="space-y-4">
            <h3 className="text-2xl font-bold">{step.step_name}</h3>
            <div className="text-lg">
              {parseMarkdown(step.display_content, vocabularyWords)}
            </div>
          </div>
        );
    }
  };

  return (
    <Card className="p-8 min-h-[400px]">
      {renderContent()}
    </Card>
  );
}

