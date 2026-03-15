import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { useBatchProcessor } from './useBatchProcessor';
import { WeekSection } from './WeekSection';
import { ProgressSection } from './ProgressSection';
import { BatchAlerts } from './BatchAlerts';
import { SlotSection } from './SlotSection';
import { ConfirmDialog } from './ConfirmDialog';

export function BatchProcessorView() {
  const {
    currentUser,
    slots,
    isProcessing,
    selectedSlots,
    weekOf,
    setWeekOf,
    result,
    error,
    recentWeeks,
    availableWeeks,
    buttonState,
    showConfirmDialog,
    setShowConfirmDialog,
    partial,
    setPartial,
    missingOnly,
    setMissingOnly,
    forceSlots,
    weekStatus,
    isLoadingStatus,
    progress,
    progressPercentage,
    sortedSlots,
    toggleSlot,
    selectAllSlots,
    deselectAllSlots,
    toggleForceSlot,
    handleProcessClick,
    handleConfirmProcess,
    handleDownload,
  } = useBatchProcessor();

  if (!currentUser) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please select a user to process lesson plans
        </CardContent>
      </Card>
    );
  }

  if (slots.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please configure at least one class slot before processing
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Weekly Plan</CardTitle>
        <CardDescription>
          Process {selectedSlots.size} of {slots.length} selected slots for the week
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <WeekSection
          weekOf={weekOf}
          setWeekOf={setWeekOf}
          recentWeeks={recentWeeks}
          availableWeeks={availableWeeks}
          isProcessing={isProcessing}
          buttonState={buttonState}
          selectedSlotsSize={selectedSlots.size}
          onProcessClick={handleProcessClick}
        />

        {weekStatus?.plan_id && (
          <div className="rounded-lg border border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/30 px-4 py-3">
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              A plan exists for this week. You can skip re-calling the LLM:
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-2">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={partial}
                  onChange={(e) => setPartial(e.target.checked)}
                  className="w-4 h-4"
                  disabled={isProcessing}
                />
                Partial/Merge (merge into existing plan)
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={missingOnly}
                  onChange={(e) => setMissingOnly(e.target.checked)}
                  className="w-4 h-4"
                  disabled={isProcessing}
                />
                Missing only (process just slots not yet in the plan)
              </label>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Then click Generate. These options are also in the confirmation dialog.
            </p>
          </div>
        )}

        <ProgressSection
          isProcessing={isProcessing}
          progress={progress}
          progressPercentage={progressPercentage}
        />

        <BatchAlerts error={error} result={result} onDownload={handleDownload} />

        <SlotSection
          sortedSlots={sortedSlots}
          selectedSlots={selectedSlots}
          weekStatus={weekStatus}
          forceSlots={forceSlots}
          isLoadingStatus={isLoadingStatus}
          isProcessing={isProcessing}
          toggleSlot={toggleSlot}
          selectAllSlots={selectAllSlots}
          deselectAllSlots={deselectAllSlots}
          toggleForceSlot={toggleForceSlot}
        />

        <ConfirmDialog
          open={showConfirmDialog}
          onOpenChange={setShowConfirmDialog}
          currentUser={currentUser}
          weekOf={weekOf}
          partial={partial}
          setPartial={setPartial}
          missingOnly={missingOnly}
          setMissingOnly={setMissingOnly}
          selectedCount={selectedSlots.size}
          totalSlots={slots.length}
          onConfirm={handleConfirmProcess}
        />
      </CardContent>
    </Card>
  );
}
