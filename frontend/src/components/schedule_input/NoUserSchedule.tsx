import { Alert, AlertTitle, AlertDescription } from '../ui/Alert';
import { DAY_LABELS } from './useScheduleInput';
import type { ConflictDetail } from './useScheduleInput';

interface NoUserScheduleProps {
  conflictDetails: ConflictDetail[];
}

export function NoUserSchedule({ conflictDetails }: NoUserScheduleProps) {
  return (
    <>
      <div className="text-center py-8 text-muted-foreground">
        <p>Please select a user to manage schedules</p>
      </div>

      {conflictDetails.length > 0 && (
        <Alert variant="destructive" className="mt-4">
          <AlertTitle>Linked lesson conflicts detected</AlertTitle>
          <AlertDescription>
            <p className="mb-2">
              All periods in the same linked group must share the same subject, grade, and homeroom.
            </p>
            <ul className="list-disc pl-5 space-y-1">
              {conflictDetails.map((conflict) => (
                <li key={conflict.id}>
                  <span className="font-semibold">{conflict.id}</span>:&nbsp;
                  {conflict.entries
                    .map(
                      (entry) =>
                        `${DAY_LABELS[entry.day]} ${entry.time} (${entry.subject || 'No subject'})`
                    )
                    .join('; ')}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </>
  );
}
