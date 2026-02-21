import { useMemo } from 'react';
import { Card } from '@lesson-ui/Card';
import type { WeeklyPlan } from '@lesson-api';
import { highlightVocabularyWords, extractVocabularyWords, getCognateBadgeClasses, getCognateBadgeLabel } from '../../utils/vocabularyHighlight';
import { parseMarkdown } from '../../utils/markdownUtils';

interface LessonPlanDisplayProps {
  lessonPlanData: (WeeklyPlan & { lesson_json?: any }) | null;
  day: string;
  slot: number;
}

// Helper function to render paragraphs from text
function renderParagraphs(text: string) {
  if (!text) return null;
  const paragraphs = text.split('\n').filter((p) => p.trim());
  return paragraphs.map((para, idx) => (
    <div key={idx} className="mb-2 last:mb-0">
      {parseMarkdown(para)}
    </div>
  ));
}

export function LessonPlanDisplay({ lessonPlanData, day, slot }: LessonPlanDisplayProps) {
  const slotData = useMemo(() => {
    if (!lessonPlanData) return null;

    try {
      const lessonJson = typeof lessonPlanData.lesson_json === 'string'
        ? JSON.parse(lessonPlanData.lesson_json)
        : lessonPlanData.lesson_json;

      if (!lessonJson || typeof lessonJson !== 'object') {
        return null;
      }

      const days = lessonJson.days || {};
      const dayKey = day?.toLowerCase() || '';
      const dayData = days[dayKey];

      if (!dayData || typeof dayData !== 'object') {
        return null;
      }

      const slots = dayData.slots || [];
      if (Array.isArray(slots) && slots.length > 0) {
        // Try to find exact match first
        let foundSlot = slots.find((s: any) => {
          if (!s) return false;
          const sSlot = s.slot_number;
          return sSlot === slot || String(sSlot) === String(slot) || Number(sSlot) === Number(slot);
        });

        // If no exact match, try first slot
        if (!foundSlot) {
          foundSlot = slots[0];
        }

        return foundSlot;
      }

      return null;
    } catch (err) {
      console.error('[LessonPlanDisplay] Error extracting slot data:', err);
      return null;
    }
  }, [lessonPlanData, day, slot]);

  if (!slotData) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p>Lesson plan data not available</p>
        <p className="text-sm mt-2">Generate a lesson plan for this week to view details</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="space-y-6">
        {/* Unit/Lesson */}
        <Card className="p-4">
          <h3 className="font-semibold mb-2">Unit/Lesson</h3>
          <div>{parseMarkdown(slotData.unit_lesson) || 'N/A'}</div>
        </Card>

        {/* Objectives */}
        <Card className="p-4">
          <h3 className="font-semibold mb-3">Objectives</h3>
          <div className="space-y-3">
            {slotData.objective?.content_objective && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1">
                  Content Objective
                </div>
                <div>{parseMarkdown(slotData.objective.content_objective)}</div>
              </div>
            )}
            {slotData.objective?.student_goal && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1">
                  Student Goal
                </div>
                <div>{parseMarkdown(slotData.objective.student_goal)}</div>
              </div>
            )}
            {slotData.objective?.wida_objective && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-1">
                  WIDA Objective
                </div>
                <div>{parseMarkdown(slotData.objective.wida_objective)}</div>
              </div>
            )}
          </div>
        </Card>

        {/* Anticipatory Set */}
        <Card className="p-4">
          <h3 className="font-semibold mb-2">Anticipatory Set</h3>
          {slotData.anticipatory_set?.original_content && (
            <div className="mb-3">
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Original
              </div>
              <div>{parseMarkdown(slotData.anticipatory_set.original_content)}</div>
            </div>
          )}
          {slotData.anticipatory_set?.bilingual_bridge && (
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Bilingual Bridge
              </div>
              <div>{parseMarkdown(slotData.anticipatory_set.bilingual_bridge)}</div>
            </div>
          )}
        </Card>

        {/* Vocabulary / Cognates */}
        {Array.isArray(slotData.vocabulary_cognates) && slotData.vocabulary_cognates.length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold mb-3">Vocabulary / Cognates</h3>
            <div className="space-y-2">
              {slotData.vocabulary_cognates.map((vocab: any, idx: number) => (
                <div key={idx} className="flex items-baseline justify-between border-b border-border/40 pb-2 last:border-0">
                  <div>
                    <span className="font-medium">{vocab.english}</span>
                    <span className="mx-2 text-muted-foreground">→</span>
                    <span className="italic text-muted-foreground">{vocab.portuguese}</span>
                  </div>
                  <span
                    className={getCognateBadgeClasses(vocab.is_cognate, 'sm')}
                    style={{
                      color: vocab.is_cognate ? '#15803d' : '#dc2626' // green-700 : red-700
                    }}
                  >
                    {getCognateBadgeLabel(vocab.is_cognate)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Assessment */}
        <Card className="p-4">
          <h3 className="font-semibold mb-2">Assessment</h3>
          {slotData.assessment?.primary_assessment && (
            <div className="mb-3">
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Primary Assessment
              </div>
              <div>{parseMarkdown(slotData.assessment.primary_assessment)}</div>
            </div>
          )}
          {slotData.assessment?.bilingual_check && (
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Bilingual Check
              </div>
              <div>{parseMarkdown(slotData.assessment.bilingual_check)}</div>
            </div>
          )}
        </Card>

        {/* Tailored Instruction */}
        <Card className="p-4">
          <h3 className="font-semibold mb-3">Tailored Instruction</h3>
          {slotData.tailored_instruction ? (
            <div className="space-y-4">
              {slotData.tailored_instruction.original_content && (
                <div>
                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                    Original Content
                  </div>
                  <div className="space-y-2">
                    {renderParagraphs(slotData.tailored_instruction.original_content)}
                  </div>
                </div>
              )}

              {slotData.tailored_instruction.co_teaching_model && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-muted-foreground">
                    Co-Teaching Model
                  </div>
                  <div className="font-medium">
                    {slotData.tailored_instruction.co_teaching_model.model_name || 'N/A'}
                  </div>
                  {slotData.tailored_instruction.co_teaching_model.rationale && (
                    <div className="text-sm text-muted-foreground">
                      {parseMarkdown(slotData.tailored_instruction.co_teaching_model.rationale)}
                    </div>
                  )}
                  {slotData.tailored_instruction.co_teaching_model.wida_context && (
                    <div className="text-xs text-muted-foreground">
                      {parseMarkdown(slotData.tailored_instruction.co_teaching_model.wida_context)}
                    </div>
                  )}
                  {Array.isArray(slotData.tailored_instruction.co_teaching_model.implementation_notes) &&
                    slotData.tailored_instruction.co_teaching_model.implementation_notes.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground mb-1">
                          Implementation Notes
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {slotData.tailored_instruction.co_teaching_model.implementation_notes.map(
                            (note: string, idx: number) => (
                              <li key={`implementation-note-${idx}`}>{parseMarkdown(note)}</li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                  {Array.isArray(slotData.tailored_instruction.co_teaching_model.phase_plan) &&
                    slotData.tailored_instruction.co_teaching_model.phase_plan.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground mb-1">
                          Phase Plan
                        </div>
                        <ol className="space-y-2">
                          {slotData.tailored_instruction.co_teaching_model.phase_plan.map(
                            (phase: any, idx: number) => (
                              <li
                                key={`phase-${phase?.phase_name || idx}`}
                                className="rounded-md border border-border/60 bg-muted/40 p-3"
                              >
                                <div className="font-semibold text-sm">
                                  {phase?.phase_name || `Phase ${idx + 1}`}
                                  {phase?.minutes ? ` (${phase.minutes} min)` : ''}
                                </div>
                                <div className="space-y-1 text-xs text-muted-foreground mt-1">
                                  {phase?.bilingual_teacher_role && (
                                    <div>
                                      <span className="font-semibold text-foreground">Bilingual:</span>{' '}
                                      {parseMarkdown(phase.bilingual_teacher_role)}
                                    </div>
                                  )}
                                  {phase?.primary_teacher_role && (
                                    <div>
                                      <span className="font-semibold text-foreground">Primary:</span>{' '}
                                      {parseMarkdown(phase.primary_teacher_role)}
                                    </div>
                                  )}
                                  {phase?.details && (
                                    <div>
                                      <span className="font-semibold text-foreground">Details:</span>{' '}
                                      {parseMarkdown(phase.details)}
                                    </div>
                                  )}
                                </div>
                              </li>
                            )
                          )}
                        </ol>
                      </div>
                    )}
                </div>
              )}

              {Array.isArray(slotData.tailored_instruction.ell_support) &&
                slotData.tailored_instruction.ell_support.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">ELL Support</div>
                    <div className="space-y-3">
                      {slotData.tailored_instruction.ell_support.map((support: any, idx: number) => {
                        if (typeof support === 'string') {
                          return (
                            <div key={`ell-support-${idx}`} className="text-sm">
                              {parseMarkdown(support)}
                            </div>
                          );
                        }
                        return (
                          <div key={`ell-support-${support?.strategy_id || idx}`} className="rounded-md border border-border/60 p-3">
                            <div className="text-sm font-semibold">
                              {parseMarkdown(support?.strategy_name || support?.description || 'ELL Support')}
                            </div>
                            {support?.proficiency_levels && (
                              <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
                                {support.proficiency_levels}
                              </div>
                            )}
                            {support?.implementation && (
                              <div className="text-sm text-muted-foreground">{parseMarkdown(support.implementation)}</div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

              {Array.isArray(slotData.tailored_instruction.special_needs_support) &&
                slotData.tailored_instruction.special_needs_support.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">
                      Special Needs Support
                    </div>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {slotData.tailored_instruction.special_needs_support.map(
                        (support: string, idx: number) => (
                          <li key={`special-support-${idx}`}>{parseMarkdown(support)}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}

              {Array.isArray(slotData.tailored_instruction.materials) &&
                slotData.tailored_instruction.materials.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Materials</div>
                    <ul className="list-disc list-inside space-y-1 text-sm">
                      {slotData.tailored_instruction.materials.map((material: string, idx: number) => (
                        <li key={`material-${idx}`}>{parseMarkdown(material)}</li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground italic">
              No tailored instruction provided for this slot.
            </div>
          )}
        </Card>

        {/* Sentence Frames */}
        {Array.isArray(slotData.sentence_frames) && slotData.sentence_frames.length > 0 && (
          <Card className="p-4">
            <h3 className="font-semibold mb-3">Sentence Frames</h3>
            <div className="space-y-6">
              {([
                { key: 'levels_1_2', label: 'Levels 1-2' },
                { key: 'levels_3_4', label: 'Levels 3-4' },
                { key: 'levels_5_6', label: 'Levels 5-6' },
              ] as const).map((group) => {
                const frames = slotData.sentence_frames.filter(
                  (f: any) => f.proficiency_level === group.key
                );
                if (frames.length === 0) return null;

                return (
                  <div key={group.key} className="space-y-2">
                    <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground border-b pb-1">
                      {group.label}
                    </div>
                    <div className="space-y-3">
                      {frames.map((frame: any, idx: number) => {
                        // Extract vocabulary words for highlighting
                        const vocabWords = extractVocabularyWords(slotData.vocabulary_cognates);

                        return (
                          <div key={idx} className="text-sm">
                            <div className="font-medium">
                              {highlightVocabularyWords(frame.english, vocabWords)}
                            </div>
                            <div className="text-muted-foreground italic">{frame.portuguese}</div>
                            {frame.language_function && (
                              <div className="mt-1 inline-block text-[10px] uppercase tracking-wide text-muted-foreground bg-muted px-1.5 rounded">
                                {frame.language_function.replace(/_/g, ' ')}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Misconceptions */}
        <Card className="p-4">
          <h3 className="font-semibold mb-2">Misconceptions</h3>
          {slotData.misconceptions?.original_content && (
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Original Content
              </div>
              <div>{slotData.misconceptions.original_content}</div>
            </div>
          )}
          {slotData.misconceptions?.linguistic_note && (
            <div className="mt-3">
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Linguistic Note
              </div>
              <div className="space-y-2">
                {typeof slotData.misconceptions.linguistic_note === 'string' ? (
                  <div>{parseMarkdown(slotData.misconceptions.linguistic_note)}</div>
                ) : (
                  <>
                    {slotData.misconceptions.linguistic_note.pattern_id && (
                      <div>
                        <span className="font-semibold">Pattern: </span>
                        {slotData.misconceptions.linguistic_note.pattern_id.replace(/_/g, ' ')}
                      </div>
                    )}
                    {slotData.misconceptions.linguistic_note.note && (
                      <div>
                        <span className="font-semibold">Note: </span>
                        {parseMarkdown(slotData.misconceptions.linguistic_note.note)}
                      </div>
                    )}
                    {slotData.misconceptions.linguistic_note.prevention_tip && (
                      <div>
                        <span className="font-semibold">Prevention Tip: </span>
                        {parseMarkdown(slotData.misconceptions.linguistic_note.prevention_tip)}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
          {/* Fallback for old structure */}
          {slotData.misconceptions?.linguistic_misconceptions && (
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Linguistic Misconceptions
              </div>
              <div>{slotData.misconceptions.linguistic_misconceptions}</div>
            </div>
          )}
          {slotData.misconceptions?.content_misconceptions && (
            <div className="mt-3">
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Content Misconceptions
              </div>
              <div>{slotData.misconceptions.content_misconceptions}</div>
            </div>
          )}
          {/* Show if misconceptions is a string instead of object */}
          {typeof slotData.misconceptions === 'string' && slotData.misconceptions && (
            <div>{slotData.misconceptions}</div>
          )}
          {/* Show message if no misconceptions data */}
          {!slotData.misconceptions && (
            <div className="text-sm text-muted-foreground italic">
              No misconceptions identified
            </div>
          )}
        </Card>

        {/* Homework */}
        <Card className="p-4">
          <h3 className="font-semibold mb-2">Homework</h3>
          {slotData.homework?.original_content && (
            <div className="mb-3">
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Original
              </div>
              <div>{parseMarkdown(slotData.homework.original_content)}</div>
            </div>
          )}
          {slotData.homework?.family_connection && (
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-1">
                Family Connection
              </div>
              <div>{parseMarkdown(slotData.homework.family_connection)}</div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

