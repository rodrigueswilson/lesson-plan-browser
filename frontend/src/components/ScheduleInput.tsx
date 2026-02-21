import { useState, useEffect, useMemo } from 'react';
import { Save, Trash2, Upload } from 'lucide-react';
import { Button } from './ui/Button';
import { ScheduleCell } from './ScheduleCell';
import { scheduleApi, ScheduleEntryCreate } from '@lesson-api';
import { useStore } from '@lesson-browser';
import { Alert, AlertTitle, AlertDescription } from './ui/Alert';

interface ScheduleCell {
  subject: string;
  grade: string | null;
  homeroom: string | null;
  plan_slot_group_id?: string | null;
}

interface ScheduleRow {
  start_time: string;
  end_time: string;
  monday: ScheduleCell | null;
  tuesday: ScheduleCell | null;
  wednesday: ScheduleCell | null;
  thursday: ScheduleCell | null;
  friday: ScheduleCell | null;
}

type Weekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';

const DAY_KEYS: Weekday[] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
const DAY_LABELS: Record<Weekday, string> = {
  monday: 'Monday',
  tuesday: 'Tuesday',
  wednesday: 'Wednesday',
  thursday: 'Thursday',
  friday: 'Friday',
};

const DEFAULT_TIME_SLOTS = [
  { start: '08:15', end: '08:30' },
  { start: '08:30', end: '09:15' },
  { start: '09:18', end: '10:03' },
  { start: '10:06', end: '10:51' },
  { start: '10:54', end: '11:39' },
  { start: '11:42', end: '12:27' },
  { start: '12:30', end: '13:15' },
  { start: '13:18', end: '14:03' },
  { start: '14:06', end: '15:00' },
  { start: '15:00', end: '15:05' },
];

export function ScheduleInput() {
  const { currentUser } = useStore();
  const [scheduleData, setScheduleData] = useState<ScheduleRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  useEffect(() => {
    if (currentUser) {
      // Automatically load existing schedule when user changes
      loadExistingSchedule();
    } else {
      // Only initialize empty schedule if no user is selected
      initializeSchedule();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser?.id]); // Only depend on user ID to avoid unnecessary reloads
  
  const initializeSchedule = () => {
    const rows: ScheduleRow[] = DEFAULT_TIME_SLOTS.map(slot => ({
      start_time: slot.start,
      end_time: slot.end,
      monday: null,
      tuesday: null,
      wednesday: null,
      thursday: null,
      friday: null,
    }));
    setScheduleData(rows);
  };

  const { existingGroups, conflictLookup, conflictDetails } = useMemo(() => {
    const groupSet = new Set<string>();
    const metadata: Record<
      string,
      {
        subject: string | null | undefined;
        grade: string | null | undefined;
        homeroom: string | null | undefined;
        conflict: boolean;
        entries: Array<{ day: Weekday; time: string; subject: string | null }>;
      }
    > = {};

    scheduleData.forEach((row) => {
      DAY_KEYS.forEach((day) => {
        const cell = row[day];
        if (!cell?.plan_slot_group_id) return;

        const id = cell.plan_slot_group_id.trim();
        if (!id) return;

        groupSet.add(id);
        if (!metadata[id]) {
          metadata[id] = {
            subject: cell.subject,
            grade: cell.grade,
            homeroom: cell.homeroom,
            conflict: false,
            entries: [],
          };
        } else {
          const meta = metadata[id];
          if (cell.subject && meta.subject && cell.subject !== meta.subject) {
            meta.conflict = true;
          } else if (!meta.subject && cell.subject) {
            meta.subject = cell.subject;
          }

          if (cell.grade && meta.grade && cell.grade !== meta.grade) {
            meta.conflict = true;
          } else if (!meta.grade && cell.grade) {
            meta.grade = cell.grade;
          }

          if (cell.homeroom && meta.homeroom && cell.homeroom !== meta.homeroom) {
            meta.conflict = true;
          } else if (!meta.homeroom && cell.homeroom) {
            meta.homeroom = cell.homeroom;
          }
        }

        metadata[id].entries.push({
          day,
          time: `${row.start_time}-${row.end_time}`,
          subject: cell.subject,
        });
      });
    });

    const existingGroups = Array.from(groupSet).sort((a, b) =>
      a.localeCompare(b, undefined, { sensitivity: 'base' })
    );

    const conflictDetails = Object.entries(metadata)
      .filter(([, meta]) => meta.conflict)
      .map(([id, meta]) => ({
        id,
        entries: meta.entries,
      }));

    const conflictLookup = conflictDetails.reduce<Record<string, boolean>>((acc, { id }) => {
      acc[id] = true;
      return acc;
    }, {});

    return { existingGroups, conflictLookup, conflictDetails };
  }, [scheduleData]);
  
  const loadExistingSchedule = async () => {
    if (!currentUser) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const entries = await scheduleApi.getSchedule(currentUser.id);
      
      // Ensure entries is an array
      const entriesArray = Array.isArray(entries) ? entries : [];
      
      const rows: ScheduleRow[] = DEFAULT_TIME_SLOTS.map(slot => ({
        start_time: slot.start,
        end_time: slot.end,
        monday: null,
        tuesday: null,
        wednesday: null,
        thursday: null,
        friday: null,
      }));
      
      console.log('[ScheduleInput] Loading entries:', entriesArray.length);
      entriesArray.forEach(entry => {
        const rowIndex = DEFAULT_TIME_SLOTS.findIndex(
          slot => slot.start === entry.start_time && slot.end === entry.end_time
        );
        
        if (rowIndex >= 0) {
          const cell: ScheduleCell = {
            subject: entry.subject,
            grade: entry.grade,
              homeroom: entry.homeroom,
              plan_slot_group_id: entry.plan_slot_group_id || null,
          };
          
          const dayKey = entry.day_of_week as keyof ScheduleRow;
          if (dayKey !== 'start_time' && dayKey !== 'end_time') {
            rows[rowIndex][dayKey] = cell;
            console.log(`[ScheduleInput] Loaded: ${entry.day_of_week} ${entry.start_time}-${entry.end_time} = ${entry.subject}`);
          }
        } else {
          console.warn(`[ScheduleInput] No match found for ${entry.start_time}-${entry.end_time}`);
        }
      });
      
      console.log('[ScheduleInput] Final rows:', rows);
      
      setScheduleData(rows);
      setSuccess('Schedule loaded successfully');
      setTimeout(() => setSuccess((s) => (s === 'Schedule loaded successfully' ? null : s)), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to load schedule');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCellChange = (
    rowIndex: number,
    dayOfWeek: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday',
    cell: ScheduleCell | null
  ) => {
    setScheduleData(prev => {
      const updated = [...prev];
      updated[rowIndex] = {
        ...updated[rowIndex],
        [dayOfWeek]: cell
      };
      return updated;
    });
    setError(null);
    setSuccess(null);
  };
  
  const handleSave = async () => {
    if (!currentUser) {
      setError('Please select a user first');
      return;
    }
    
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      const entries: ScheduleEntryCreate[] = [];
      
      scheduleData.forEach((row, rowIndex) => {
        DAY_KEYS.forEach(day => {
          const cell = row[day];
          if (cell && cell.subject) {
            entries.push({
              user_id: currentUser.id,
              day_of_week: day,
              start_time: row.start_time,
              end_time: row.end_time,
              subject: cell.subject,
              homeroom: cell.homeroom || null,
              grade: cell.grade || null,
              slot_number: rowIndex + 1,
              is_active: true,
              plan_slot_group_id: cell.plan_slot_group_id || null,
            });
          }
        });
      });
      
      if (entries.length === 0) {
        setError('No schedule entries to save');
        setIsSaving(false);
        return;
      }
      
      const result = await scheduleApi.bulkCreate(currentUser.id, entries);
      
      if (result.success) {
        setSuccess(`Schedule saved successfully! ${result.created_count} entries created.`);
      } else {
        const errorMessages = result.errors && result.errors.length > 0 
          ? result.errors.join(', ') 
          : 'Unknown error occurred';
        setError(`Some entries failed to save. ${errorMessages}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save schedule');
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleClear = () => {
    if (confirm('Are you sure you want to clear all schedule entries?')) {
      initializeSchedule();
      setError(null);
      setSuccess(null);
    }
  };
  
  if (!currentUser) {
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
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Schedule Input</h2>
          <p className="text-sm text-muted-foreground">
            Click on any cell to add subject, grade, and homeroom
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadExistingSchedule}
            disabled={isLoading}
          >
            <Upload className="w-4 h-4 mr-2" />
            Load Existing
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear All
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Schedule'}
          </Button>
        </div>
      </div>
      
      {error && (
        <Alert variant="destructive">
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert variant="success">
          {success}
        </Alert>
      )}
      
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
                <ScheduleCell
                  cell={row.monday}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek="monday"
                  onChange={(cellValue) => handleCellChange(index, 'monday', cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(row.monday?.plan_slot_group_id && conflictLookup[row.monday.plan_slot_group_id])}
                />
                <ScheduleCell
                  cell={row.tuesday}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek="tuesday"
                  onChange={(cellValue) => handleCellChange(index, 'tuesday', cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(row.tuesday?.plan_slot_group_id && conflictLookup[row.tuesday.plan_slot_group_id])}
                />
                <ScheduleCell
                  cell={row.wednesday}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek="wednesday"
                  onChange={(cellValue) => handleCellChange(index, 'wednesday', cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(row.wednesday?.plan_slot_group_id && conflictLookup[row.wednesday.plan_slot_group_id])}
                />
                <ScheduleCell
                  cell={row.thursday}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek="thursday"
                  onChange={(cellValue) => handleCellChange(index, 'thursday', cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(row.thursday?.plan_slot_group_id && conflictLookup[row.thursday.plan_slot_group_id])}
                />
                <ScheduleCell
                  cell={row.friday}
                  timeSlot={`${row.start_time} - ${row.end_time}`}
                  dayOfWeek="friday"
                  onChange={(cellValue) => handleCellChange(index, 'friday', cellValue)}
                  existingGroups={existingGroups}
                  hasGroupConflict={Boolean(row.friday?.plan_slot_group_id && conflictLookup[row.friday.plan_slot_group_id])}
                />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="space-y-3">
        <div className="text-sm text-muted-foreground">
          <p><strong>Note:</strong> For non-class periods (PREP, Lunch, A.M. Routine, Dismissal, PLC, GLM), 
          grade and homeroom will be automatically cleared.</p>
        </div>
        
        <div className="border rounded-lg p-4 bg-card">
          <h3 className="text-sm font-semibold mb-3">Color Legend</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-gray-300 bg-gray-100"></div>
              <span>PREP</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-blue-200 bg-blue-50"></div>
              <span>A.M. Routine</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-orange-200 bg-orange-50"></div>
              <span>Lunch</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-purple-200 bg-purple-50"></div>
              <span>Dismissal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-amber-300 bg-amber-50"></div>
              <span>PLC / GLM (meetings)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-green-300 bg-green-50"></div>
              <span>ELA</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-blue-300 bg-blue-50"></div>
              <span>MATH</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-yellow-300 bg-yellow-50"></div>
              <span>Science</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border border-red-300 bg-red-50"></div>
              <span>Social Studies</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

