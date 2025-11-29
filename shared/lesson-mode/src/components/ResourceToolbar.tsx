import { Button } from '@lesson-ui/Button';
import { FileText, BookOpen, Book, MessageSquare, ClipboardList, Scroll } from 'lucide-react';

type ResourceType = 'instructions' | 'objective' | 'vocabulary' | 'sentence_frames' | 'lesson_card' | 'lesson_plan';

interface AvailableResources {
  objective?: boolean;
  vocabulary?: boolean;
  sentenceFrames?: boolean;
  lessonCard?: boolean;
  lessonPlan?: boolean;
}

interface ResourceToolbarProps {
  activeResource: ResourceType;
  onResourceSelect: (resource: ResourceType) => void;
  availableResources: AvailableResources;
}

const resourceButtons: Array<{
  type: ResourceType;
  label: string;
  icon: React.ReactNode;
  key: keyof AvailableResources;
}> = [
  {
    type: 'objective',
    label: 'Objective',
    icon: <Scroll className="w-4 h-4" />,
    key: 'objective',
  },
  {
    type: 'vocabulary',
    label: 'Vocabulary',
    icon: <BookOpen className="w-4 h-4" />,
    key: 'vocabulary',
  },
  {
    type: 'sentence_frames',
    label: 'Sentence Frames',
    icon: <MessageSquare className="w-4 h-4" />,
    key: 'sentenceFrames',
  },
  {
    type: 'lesson_card',
    label: 'Lesson Card',
    icon: <ClipboardList className="w-4 h-4" />,
    key: 'lessonCard',
  },
  {
    type: 'lesson_plan',
    label: 'Full Plan',
    icon: <FileText className="w-4 h-4" />,
    key: 'lessonPlan',
  },
];

export function ResourceToolbar({
  activeResource,
  onResourceSelect,
  availableResources,
}: ResourceToolbarProps) {
  return (
    <div className="flex gap-2 p-2 bg-muted/50 border-b overflow-x-auto">
      {resourceButtons.map((button) => {
        const isAvailable = availableResources[button.key] !== false;
        const isActive = activeResource === button.type;

        return (
          <Button
            key={button.type}
            variant={isActive ? 'default' : 'outline'}
            size="sm"
            onClick={() => onResourceSelect(button.type)}
            disabled={!isAvailable}
            className="flex items-center gap-2 whitespace-nowrap"
            title={!isAvailable ? `${button.label} not available` : button.label}
          >
            {button.icon}
            <span>{button.label}</span>
          </Button>
        );
      })}
    </div>
  );
}

