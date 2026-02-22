import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../ui/Dialog';
import { Button } from '../ui/Button';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentUser: { base_path_override?: string } | null;
  weekOf: string;
  partial: boolean;
  setPartial: (value: boolean) => void;
  missingOnly: boolean;
  setMissingOnly: (value: boolean) => void;
  selectedCount: number;
  totalSlots: number;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  currentUser,
  weekOf,
  partial,
  setPartial,
  missingOnly,
  setMissingOnly,
  selectedCount,
  totalSlots,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Processing</DialogTitle>
          <DialogDescription>
            Please verify the details before generating the weekly plan.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium">Source Folder:</p>
              <p className="text-sm text-muted-foreground mt-1 truncate">
                {currentUser?.base_path_override || 'Default path'}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Week:</p>
              <p className="text-sm text-muted-foreground mt-1">{weekOf}</p>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium">Processing Mode:</p>
            <div className="flex gap-4 mt-2">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={partial}
                  onChange={(e) => setPartial(e.target.checked)}
                  className="w-4 h-4"
                />
                Partial/Merge
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={missingOnly}
                  onChange={(e) => setMissingOnly(e.target.checked)}
                  className="w-4 h-4"
                />
                Missing Only
              </label>
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">
              {missingOnly ? 'Will only process slots not yet in the plan.' : partial ? 'Will merge new slots into the existing plan.' : 'Will create a fresh plan (overwriting existing).'}
            </p>
          </div>

          <div>
            <p className="text-sm font-medium">Slots to Process:</p>
            <p className="text-sm text-muted-foreground mt-1">
              {selectedCount} of {totalSlots} slots selected
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onConfirm}>Proceed</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
