import type { LessonStep } from '@lesson-api';
import { extractLessonPlanContext, LessonPlanContext } from './lessonPlanContext';

const CONTENT_TYPES: LessonStep['content_type'][] = [
  'objective',
  'sentence_frames',
  'materials',
  'instruction',
  'assessment',
];

interface BuildStepsFromPhasePlanOptions {
  planId: string;
  day: string;
  slot: number;
  lessonJson?: any;
  context?: LessonPlanContext | null;
}

const generateLocalId = (parts: Array<string | number>) => {
  const base = parts.map((part) => String(part ?? '').replace(/\s+/g, '-')).join('-');
  const randomSuffix = Math.random().toString(36).slice(2, 8);
  return `offline-${base}-${randomSuffix}`;
};

const safeContentType = (rawType: unknown): LessonStep['content_type'] => {
  if (typeof rawType !== 'string') {
    return 'instruction';
  }

  const normalized = rawType.trim().toLowerCase();
  const match = CONTENT_TYPES.find((type) => type === normalized);
  return match ?? 'instruction';
};

const buildPhaseDisplayContent = (phase: Record<string, any>): string => {
  const parts: string[] = [];
  if (phase?.bilingual_teacher_role) {
    parts.push(`Bilingual Teacher: ${phase.bilingual_teacher_role}`);
  }
  if (phase?.primary_teacher_role) {
    parts.push(`Primary Teacher: ${phase.primary_teacher_role}`);
  }
  if (phase?.details) {
    parts.push(phase.details);
  }
  return parts.join('\n\n');
};

const findStrategyText = (ellSupport: any, predicate: (strategyId: string, strategyName: string) => boolean): string => {
  if (!Array.isArray(ellSupport)) {
    return '';
  }

  for (const strategy of ellSupport) {
    if (!strategy || typeof strategy !== 'object') {
      continue;
    }

    const strategyId = String(strategy.strategy_id ?? '').toLowerCase();
    const strategyName = String(strategy.strategy_name ?? '').toLowerCase();

    if (!predicate(strategyId, strategyName)) {
      continue;
    }

    const implementation =
      strategy.implementation ??
      strategy.implementation_steps ??
      strategy.details;

    if (Array.isArray(implementation)) {
      return implementation.join('\n');
    }

    if (typeof implementation === 'string') {
      return implementation;
    }
  }

  return '';
};

const buildVocabularyDisplay = (
  vocabulary: Array<Record<string, any>>,
  strategyText: string
): string => {
  const lines = vocabulary
    .map((pair) => {
      if (!pair || typeof pair !== 'object') {
        return null;
      }
      const english = String(pair.english ?? '').trim();
      const portuguese = String(pair.portuguese ?? '').trim();
      if (!english || !portuguese) {
        return null;
      }
      return `- ${english} -> ${portuguese}`;
    })
    .filter((line): line is string => Boolean(line));

  const parts = [];
  if (strategyText) {
    parts.push(strategyText);
  }
  if (lines.length) {
    parts.push(lines.join('\n'));
  }
  return parts.join('\n\n');
};

const buildSentenceFramesDisplay = (
  frames: Array<Record<string, any>>,
  strategyText: string
): string => {
  const parts = [];
  if (strategyText) {
    parts.push(strategyText);
  }

  if (frames.length) {
    parts.push('\nReference Frames:');
    for (const frame of frames) {
      if (frame && typeof frame === 'object' && frame.english) {
        parts.push(`- ${frame.english}`);
      }
    }
  }

  return parts.join('\n').trim();
};

const pickVocabularyList = (context: LessonPlanContext | null): Array<Record<string, any>> => {
  if (!context) {
    return [];
  }
  const slotVocab = context.slotData?.vocabulary_cognates;
  const dayVocab = context.dayData?.vocabulary_cognates;
  if (Array.isArray(slotVocab) && slotVocab.length > 0) {
    return slotVocab;
  }
  if (Array.isArray(dayVocab) && dayVocab.length > 0) {
    return dayVocab;
  }
  return [];
};

const pickSentenceFrames = (context: LessonPlanContext | null): Array<Record<string, any>> => {
  if (!context) {
    return [];
  }
  const slotFrames = context.slotData?.sentence_frames;
  const dayFrames = context.dayData?.sentence_frames;
  if (Array.isArray(slotFrames) && slotFrames.length > 0) {
    return slotFrames;
  }
  if (Array.isArray(dayFrames) && dayFrames.length > 0) {
    return dayFrames;
  }
  return [];
};

export function buildLessonStepsFromPhasePlan({
  planId,
  day,
  slot,
  lessonJson,
  context,
}: BuildStepsFromPhasePlanOptions): LessonStep[] | null {
  const normalizedDay = typeof day === 'string' ? day.toLowerCase() : '';
  const slotNumber = Number(slot);
  if (!normalizedDay || Number.isNaN(slotNumber)) {
    return null;
  }

  const resolvedContext =
    context ?? extractLessonPlanContext(lessonJson, normalizedDay, slotNumber);

  if (!resolvedContext) {
    return null;
  }

  const slotData = resolvedContext.slotData || resolvedContext.dayData;
  if (!slotData || typeof slotData !== 'object') {
    return null;
  }

  const dayData = resolvedContext.dayData || resolvedContext.slotData || {};
  const tailoredInstruction =
    slotData.tailored_instruction ||
    dayData.tailored_instruction ||
    {};
  const coTeachingModel =
    tailoredInstruction.co_teaching_model ||
    dayData.tailored_instruction?.co_teaching_model ||
    {};

  const phasePlan = Array.isArray(coTeachingModel.phase_plan)
    ? coTeachingModel.phase_plan
    : [];

  if (!phasePlan.length) {
    return null;
  }

  const ellSupport = tailoredInstruction.ell_support || [];
  const createdAt = new Date().toISOString();
  const steps: LessonStep[] = [];
  let startTimeOffset = 0;
  let stepNumber = 1;

  for (const phase of phasePlan) {
    if (!phase || typeof phase !== 'object') {
      continue;
    }

    const duration = Math.max(
      1,
      Number(phase.minutes ?? phase.duration_minutes ?? 5)
    );

    const step: LessonStep = {
      id: generateLocalId([planId, normalizedDay, slotNumber, stepNumber]),
      lesson_plan_id: planId,
      day_of_week: normalizedDay,
      slot_number: slotNumber,
      step_number: stepNumber,
      step_name: String(phase.phase_name || `Step ${stepNumber}`),
      duration_minutes: duration,
      start_time_offset: startTimeOffset,
      content_type: safeContentType(phase.content_type),
      display_content: buildPhaseDisplayContent(phase),
      hidden_content: [],
      sentence_frames: Array.isArray(phase.sentence_frames)
        ? phase.sentence_frames
        : [],
      materials_needed: Array.isArray(phase.materials)
        ? phase.materials
        : [],
      vocabulary_cognates: [],
      created_at: createdAt,
      updated_at: createdAt,
    };

    steps.push(step);
    startTimeOffset += duration;
    stepNumber += 1;
  }

  const vocabulary = pickVocabularyList(resolvedContext);
  if (vocabulary.length) {
    const strategyText = findStrategyText(
      ellSupport,
      (strategyId, strategyName) =>
        strategyId === 'cognate_awareness' || strategyName.includes('cognate')
    );
    const vocabStep: LessonStep = {
      id: generateLocalId([planId, normalizedDay, slotNumber, 'vocab']),
      lesson_plan_id: planId,
      day_of_week: normalizedDay,
      slot_number: slotNumber,
      step_number: stepNumber,
      step_name: 'Vocabulary / Cognate Awareness',
      duration_minutes: 5,
      start_time_offset: startTimeOffset,
      content_type: 'instruction',
      display_content: buildVocabularyDisplay(vocabulary, strategyText),
      hidden_content: [],
      sentence_frames: [],
      materials_needed: [],
      vocabulary_cognates: vocabulary,
      created_at: createdAt,
      updated_at: createdAt,
    };
    steps.push(vocabStep);
    startTimeOffset += 5;
    stepNumber += 1;
  }

  const sentenceFrames = pickSentenceFrames(resolvedContext);
  if (sentenceFrames.length) {
    const framesStrategy = findStrategyText(
      ellSupport,
      (strategyId, strategyName) =>
        strategyId === 'sentence_frames' || strategyName.includes('sentence frame')
    );
    const framesStep: LessonStep = {
      id: generateLocalId([planId, normalizedDay, slotNumber, 'frames']),
      lesson_plan_id: planId,
      day_of_week: normalizedDay,
      slot_number: slotNumber,
      step_number: stepNumber,
      step_name: 'Sentence Frames / Stems / Questions',
      duration_minutes: 5,
      start_time_offset: startTimeOffset,
      content_type: 'sentence_frames',
      display_content: buildSentenceFramesDisplay(sentenceFrames, framesStrategy),
      hidden_content: [],
      sentence_frames: sentenceFrames,
      materials_needed: [],
      vocabulary_cognates: [],
      created_at: createdAt,
      updated_at: createdAt,
    };
    steps.push(framesStep);
  }

  return steps.length ? steps : null;
}

