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
          isProcessing={isProcessing}
          buttonState={buttonState}
          selectedSlotsSize={selectedSlots.size}
          onProcessClick={handleProcessClick}
        />

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
