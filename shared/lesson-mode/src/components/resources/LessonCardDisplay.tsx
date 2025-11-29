import type { LessonStep } from '@lesson-api';
import { StepContentDisplay } from '../StepContentDisplay';

interface LessonCardDisplayProps {
  step: LessonStep;
  vocabularyWords?: string[]; // Optional vocabulary words for highlighting in sentence frames
}

export function LessonCardDisplay({ step, vocabularyWords }: LessonCardDisplayProps) {
  // Reuse the existing StepContentDisplay component
  return <StepContentDisplay step={step} vocabularyWords={vocabularyWords} />;
}

