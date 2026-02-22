import { Alert } from '../ui/Alert';
import { useScheduleInput } from './useScheduleInput';
import { ScheduleInputHeader } from './ScheduleInputHeader';
import { ScheduleInputTable } from './ScheduleInputTable';
import { ScheduleColorLegend } from './ScheduleColorLegend';
import { NoUserSchedule } from './NoUserSchedule';

export function ScheduleInputView() {
  const {
    currentUser,
    scheduleData,
    isLoading,
    isSaving,
    error,
    success,
    existingGroups,
    conflictLookup,
    conflictDetails,
    loadExistingSchedule,
    handleCellChange,
    handleSave,
    handleClear,
  } = useScheduleInput();

  if (!currentUser) {
    return <NoUserSchedule conflictDetails={conflictDetails} />;
  }

  return (
    <div className="space-y-4">
      <ScheduleInputHeader
        isLoading={isLoading}
        isSaving={isSaving}
        onLoadExisting={loadExistingSchedule}
        onClear={handleClear}
        onSave={handleSave}
      />

      {error && (
        <Alert variant="destructive">
          {error}
        </Alert>
      )}

      {success && <Alert variant="success">{success}</Alert>}

      <ScheduleInputTable
        scheduleData={scheduleData}
        existingGroups={existingGroups}
        conflictLookup={conflictLookup}
        onCellChange={handleCellChange}
      />

      <ScheduleColorLegend />
    </div>
  );
}
