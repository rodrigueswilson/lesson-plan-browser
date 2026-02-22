import { ScheduleCell as ScheduleCellComponent } from '../ScheduleCell';
import type { ScheduleRow, Weekday } from './useScheduleInput';

const DAY_KEYS: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];

interface ScheduleInputTableProps {
  scheduleData: ScheduleRow[];
  existingGroups: string[];
  conflictLookup: Record<string, boolean>;
  onCellChange: (
    rowIndex: number,
    dayOfWeek: Weekday,
    cell: { subject: string; grade: string | null; homeroom: string | null; plan_slot_group_id?: string | null } | null
  ) => void;
}

export function ScheduleInputTable({
  scheduleData,
  existingGroups,
  conflictLookup,
  onCellChange,
}: ScheduleInputTableProps) {
  return (
    <div className="border rounded-lg overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-muted">
            <th className="border p-3 text-left font-semibold min-w-[120px]">Time</th>
            <th className="border p-3 text-center font-semibold min-w-[150px]">Monday</th>
            <th className="border p-3 text-center font-semibold min-w-[150px]">Tuesday</th>
            <th className="border p-3 text-center font-semibold min-w-[150px]">Wednesday</th>
            <th className="border p-3 text-center font-semibold min-w-[150px]">Thursday</th>
            <th className="border p-3 text-center font-semibold min-w-[150px]">Friday</th>
          </tr>
        </thead>
        <tbody>
          {scheduleData.map((row, index) => (
            <tr key={index}>
              <td className="border p-3 font-mono text-sm bg-muted/50">
                {row.start_time} - {row.end_time}
              </td>
              {DAY_KEYS.map((day) => (
                <ScheduleCellComponent
                  key={day}
                  cell={row[day]}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek={day}
                  onChange={(cellValue) => onCellChange(index, day, cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(
                    row[day]?.plan_slot_group_id && conflictLookup[row[day]!.plan_slot_group_id!]
                  )}
                />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
