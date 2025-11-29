import { useEffect, useState } from 'react';
import { Clock, BookOpen, Play } from 'lucide-react';
import { scheduleApi, ScheduleEntry } from '@lesson-api';
import { useStore } from '@lesson-browser';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

interface CurrentLessonCardProps {
  onEnterLessonMode?: (scheduleEntry: ScheduleEntry) => void;
  onViewPlan?: (scheduleEntry: ScheduleEntry) => void;
  compact?: boolean;
}

export function CurrentLessonCard({ onEnterLessonMode, onViewPlan, compact = false }: CurrentLessonCardProps = {}) {
  const { currentUser } = useStore();
  const [currentLesson, setCurrentLesson] = useState<ScheduleEntry | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentUser) {
      setCurrentLesson(null);
      setLoading(false);
      return;
    }

    const fetchCurrentLesson = async () => {
      try {
        const response = await scheduleApi.getCurrentLesson(currentUser.id);
        setCurrentLesson(response.data);
      } catch (error) {
        console.error('Failed to fetch current lesson:', error);
        setCurrentLesson(null);
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentLesson();
    
    // Update every minute
    const interval = setInterval(() => {
      fetchCurrentLesson();
    }, 60000);

    return () => clearInterval(interval);
  }, [currentUser]);

  useEffect(() => {
    if (!currentLesson) {
      setTimeRemaining('');
      return;
    }

    const updateTimeRemaining = () => {
      const now = new Date();
      const [hours, minutes] = currentLesson.end_time.split(':').map(Number);
      const endTime = new Date(now);
      endTime.setHours(hours, minutes, 0, 0);
      
      // If end time is earlier today, assume it's tomorrow
      if (endTime < now) {
        endTime.setDate(endTime.getDate() + 1);
      }

      const diff = endTime.getTime() - now.getTime();
      if (diff < 0) {
        setTimeRemaining('0:00');
        return;
      }
      
      const mins = Math.floor(diff / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      
      setTimeRemaining(`${mins}:${secs.toString().padStart(2, '0')}`);
    };

    updateTimeRemaining();
    const interval = setInterval(updateTimeRemaining, 1000);

    return () => clearInterval(interval);
  }, [currentLesson]);

  if (loading) {
    return <Card className="p-6">Loading...</Card>;
  }

  if (!currentLesson) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          <p>No current lesson</p>
          <p className="text-sm mt-2">Check your schedule</p>
        </div>
      </Card>
    );
  }

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  // Compact version for Browser mode header
  if (compact) {
    return (
      <div className="flex items-center gap-4 px-4 py-2 bg-primary/10 border border-primary rounded-lg">
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Current Lesson</div>
            <div className="font-bold text-lg">{currentLesson.subject}</div>
            <div className="text-xs text-muted-foreground">
              {formatTime(currentLesson.start_time)} - {formatTime(currentLesson.end_time)}
            </div>
          </div>
          {timeRemaining && (
            <div className="px-3 py-1 bg-primary text-primary-foreground rounded">
              <div className="text-xs">Remaining</div>
              <div className="text-lg font-bold">{timeRemaining}</div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onViewPlan?.(currentLesson)}
          >
            <BookOpen className="w-4 h-4" />
          </Button>
          <Button 
            variant="default" 
            size="sm"
            onClick={() => onEnterLessonMode?.(currentLesson)}
          >
            <Play className="w-4 h-4" />
          </Button>
        </div>
      </div>
    );
  }

  // Full version (for other contexts)
  return (
    <Card className="p-6 border-2 border-primary">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">CURRENT LESSON</h3>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>{formatTime(currentLesson.start_time)} - {formatTime(currentLesson.end_time)}</span>
          </div>
        </div>
        {timeRemaining && (
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Time Remaining</div>
            <div className="text-2xl font-bold text-primary">{timeRemaining}</div>
          </div>
        )}
      </div>

      <div className="mb-4">
        <div className="text-2xl font-bold mb-1">
          {currentLesson.subject}
        </div>
        {currentLesson.grade && (
          <div className="text-muted-foreground">
            {currentLesson.grade} Grade
            {currentLesson.homeroom && ` • ${currentLesson.homeroom}`}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => onViewPlan?.(currentLesson)}
        >
          <BookOpen className="w-4 h-4 mr-2" />
          View Plan
        </Button>
        <Button 
          variant="default" 
          size="sm"
          onClick={() => onEnterLessonMode?.(currentLesson)}
        >
          <Play className="w-4 h-4 mr-2" />
          Enter Lesson Mode
        </Button>
      </div>
    </Card>
  );
}

