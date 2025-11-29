import { useState, useMemo } from 'react';
import type { LessonStep, WeeklyPlan } from '@lesson-api';
import { ResourceToolbar } from './ResourceToolbar';
import { ObjectiveDisplay } from './resources/ObjectiveDisplay';
import { VocabularyDisplay } from './resources/VocabularyDisplay';
import { SentenceFramesDisplay } from './resources/SentenceFramesDisplay';
import { LessonCardDisplay } from './resources/LessonCardDisplay';
import { LessonPlanDisplay } from './resources/LessonPlanDisplay';
import { extractVocabularyWords } from '../utils/vocabularyHighlight';

type ResourceType = 'instructions' | 'objective' | 'vocabulary' | 'sentence_frames' | 'lesson_card' | 'lesson_plan';

interface ResourceDisplayAreaProps {
  currentStep: LessonStep;
  steps: LessonStep[];
  lessonPlanData: (WeeklyPlan & { lesson_json?: any }) | null;
  day: string;
  slot: number;
}

export function ResourceDisplayArea({
  currentStep,
  steps,
  lessonPlanData,
  day,
  slot,
}: ResourceDisplayAreaProps) {
  const [activeResource, setActiveResource] = useState<ResourceType>('objective');

  // Extract objective/student goal from lesson plan data
  const objective = useMemo(() => {
    console.log('[Objective] Extraction starting...');
    console.log('[Objective] lessonPlanData:', lessonPlanData);
    console.log('[Objective] day:', day, 'slot:', slot);
    
    if (!lessonPlanData) {
      console.log('[Objective] No lessonPlanData');
      return null;
    }
    
    if (!lessonPlanData.lesson_json) {
      console.log('[Objective] No lesson_json in lessonPlanData');
      return null;
    }
    
    try {
      const lessonJson = typeof lessonPlanData.lesson_json === 'string'
        ? JSON.parse(lessonPlanData.lesson_json)
        : lessonPlanData.lesson_json;
      
      if (!lessonJson || typeof lessonJson !== 'object') {
        console.log('[Objective] Invalid lessonJson structure');
        return null;
      }
      
      const days = lessonJson.days || {};
      if (!days || typeof days !== 'object') {
        console.log('[Objective] No days in lessonJson');
        return null;
      }
      
      const dayKey = day?.toLowerCase() || '';
      console.log('[Objective] Looking for day:', dayKey, 'Available days:', Object.keys(days));
      
      const dayData = days[dayKey];
      if (!dayData || typeof dayData !== 'object') {
        console.log('[Objective] Day data not found for:', dayKey);
        return null;
      }
      
      console.log('[Objective] Day data keys:', Object.keys(dayData));
      console.log('[Objective] Slot number:', slot);
      
      // Check if slots structure exists
      const slots = dayData.slots || [];
      if (Array.isArray(slots) && slots.length > 0) {
        console.log('[Objective] Found slots array with', slots.length, 'slots');
        console.log('[Objective] Looking for slot number:', slot, 'Type:', typeof slot);
        
        // Try to find exact match first
        let slotData = slots.find((s: any) => {
          if (!s) return false;
          const sSlot = s.slot_number;
          console.log('[Objective] Comparing slot:', sSlot, 'Type:', typeof sSlot, 'with target:', slot);
          return sSlot === slot || String(sSlot) === String(slot) || Number(sSlot) === Number(slot);
        });
        
        // If no exact match, try first slot
        if (!slotData) {
          console.log('[Objective] No exact slot match, using first slot');
          slotData = slots[0];
        }
        
        if (slotData) {
          console.log('[Objective] Using slot data with slot_number:', slotData.slot_number);
          console.log('[Objective] Slot data keys:', Object.keys(slotData));
          console.log('[Objective] Slot data objective:', slotData.objective);
          console.log('[Objective] Slot data objective type:', typeof slotData.objective);
          
          // Check if objective is an object with student_goal field
          if (slotData.objective && typeof slotData.objective === 'object') {
            console.log('[Objective] Objective is an object, keys:', Object.keys(slotData.objective));
            const studentGoal = slotData.objective.student_goal || 
                               slotData.objective.content_objective ||
                               slotData.objective.wida_objective;
            if (studentGoal) {
              console.log('[Objective] Found student goal in objective object:', studentGoal);
              return studentGoal;
            }
          }
          // Try multiple field names: objective, student_goal, student goal, learning_objective, etc.
          const directObjective = slotData.objective || 
                                 slotData.student_goal || 
                                 slotData['student goal'] ||
                                 slotData.learning_objective;
          if (directObjective && typeof directObjective !== 'object') {
            console.log('[Objective] Found direct objective:', directObjective);
            return directObjective;
          }
        }
      }
      
      // Check if objective is an object with student_goal field at day level
      if (dayData.objective && typeof dayData.objective === 'object') {
        console.log('[Objective] Day level objective object:', dayData.objective);
        const studentGoal = dayData.objective.student_goal || 
                           dayData.objective.content_objective ||
                           dayData.objective.wida_objective;
        if (studentGoal) {
          console.log('[Objective] Found student goal at day level:', studentGoal);
          return studentGoal;
        }
      }
      
      // Try multiple field names at day level too
      const dayLevelObjective = dayData.objective || 
                                dayData.student_goal ||
                                dayData['student goal'] ||
                                dayData.learning_objective;
      if (dayLevelObjective) {
        console.log('[Objective] Found day level objective:', dayLevelObjective);
        return dayLevelObjective;
      }
      
      console.log('[Objective] No objective found in any location');
      return null;
    } catch (err) {
      console.error('[Objective] Error extracting objective:', err);
      return null;
    }
  }, [lessonPlanData, day, slot]);

  // Extract vocabulary words from steps for highlighting
  const vocabularyWords = useMemo(() => {
    const vocabStep = steps.find(
      (step) =>
        step.step_name?.toLowerCase().includes('vocabulary') ||
        step.step_name?.toLowerCase().includes('cognate')
    );
    return extractVocabularyWords(vocabStep?.vocabulary_cognates);
  }, [steps]);

  // Determine which resources are available
  const availableResources = useMemo(() => {
    // Always make these available - let the display components handle empty states
    // This ensures buttons are always clickable, and components show appropriate messages
    return {
      objective: true, // Always available
      vocabulary: true, // Always available - VocabularyDisplay will show "No vocabulary found" if empty
      sentenceFrames: true, // Always available - SentenceFramesDisplay will show "No sentence frames found" if empty
      lessonCard: true, // Always available
      lessonPlan: true, // Always available
    };
  }, []);

  const renderResource = () => {
    switch (activeResource) {
      case 'objective':
        return <ObjectiveDisplay steps={steps} objective={objective} />;
      case 'vocabulary':
        return <VocabularyDisplay steps={steps} />;
      case 'sentence_frames':
        return <SentenceFramesDisplay steps={steps} />;
      case 'lesson_card':
        return <LessonCardDisplay step={currentStep} vocabularyWords={vocabularyWords} />;
      case 'lesson_plan':
        return <LessonPlanDisplay lessonPlanData={lessonPlanData} day={day} slot={slot} />;
      default:
        return <LessonCardDisplay step={currentStep} vocabularyWords={vocabularyWords} />;
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <ResourceToolbar
        activeResource={activeResource}
        onResourceSelect={setActiveResource}
        availableResources={availableResources}
      />
      <div className="flex-1 overflow-y-auto p-4">
        {renderResource()}
      </div>
    </div>
  );
}

