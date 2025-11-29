import React, { useState, useEffect } from 'react';
import { Play, Download, FileText, AlertCircle, CheckCircle2, Loader2, CheckSquare, Square, X } from 'lucide-react';
import { useStore } from '@lesson-browser';
import { planApi, createProgressStream, userApi } from '@lesson-api';
import { Button } from './ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Label } from './ui/Label';
import { Progress } from './ui/Progress';
import { Alert, AlertDescription, AlertTitle } from './ui/Alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/Dialog';

export const BatchProcessor: React.FC = () => {
  const { 
    currentUser, 
    slots, 
    isProcessing, 
    setIsProcessing, 
    progress, 
    setProgress,
    selectedSlots,
    toggleSlot,
    selectAllSlots,
    deselectAllSlots
  } = useStore();
  const [weekOf, setWeekOf] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentWeeks, setRecentWeeks] = useState<Array<{week_of: string; display: string; folder_name: string}>>([]);
  
  type ButtonState = 'idle' | 'processing' | 'success' | 'error';
  const [buttonState, setButtonState] = useState<ButtonState>('idle');
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  
  // Auto-select all slots when they change
  useEffect(() => {
    if (slots.length > 0 && selectedSlots.size === 0) {
      selectAllSlots();
    }
  }, [slots.length]);
  
  // Load recent weeks when user changes
  useEffect(() => {
    if (currentUser?.id) {
      loadRecentWeeks();
    }
  }, [currentUser?.id]); // Only depend on user ID, not the whole object
  
  const loadRecentWeeks = async () => {
    if (!currentUser) {
      console.log('[BatchProcessor] No current user, skipping recent weeks load');
      return;
    }
    
    console.log('[BatchProcessor] Loading recent weeks for user:', currentUser.id);
    console.log('[BatchProcessor] User base_path_override:', currentUser.base_path_override);
    
    try {
      const response = await userApi.getRecentWeeks(currentUser.id, 5);
      console.log('[BatchProcessor] Recent weeks response:', response.data);
      setRecentWeeks(response.data);
      
      // Only warn if base_path_override is set but no weeks found (suggests a problem)
      // If base_path_override is not set, empty array is expected behavior
      if (response.data.length === 0 && currentUser.base_path_override) {
        console.warn('[BatchProcessor] No recent weeks found in configured folder. Check if folders exist at:', currentUser.base_path_override);
      } else if (response.data.length === 0) {
        console.log('[BatchProcessor] No base_path_override configured. User needs to set lesson plan folder path in settings.');
      }
    } catch (err) {
      console.error('[BatchProcessor] Failed to load recent weeks:', err);
      setRecentWeeks([]);
    }
  };
  
  // Auto-reset button state after success/error
  useEffect(() => {
    if (buttonState === 'success' || buttonState === 'error') {
      const timer = setTimeout(() => setButtonState('idle'), 3000);
      return () => clearTimeout(timer);
    }
  }, [buttonState]);

  const handleProcessClick = () => {
    if (!currentUser || !weekOf || selectedSlots.size === 0) return;
    setShowConfirmDialog(true);
  };

  const handleConfirmProcess = async () => {
    setShowConfirmDialog(false);
    if (!currentUser || !weekOf || selectedSlots.size === 0) return;
    
    setButtonState('processing');
    setIsProcessing(true);
    setError(null);
    setResult(null);
    setProgress({ current: 0, total: selectedSlots.size, message: 'Starting...' });
    
    try {
      // Start processing with selected slots
      const selectedSlotIds = Array.from(selectedSlots);
      const response = await planApi.process(currentUser.id, weekOf, 'openai', selectedSlotIds);
      
      // Set up SSE for progress updates
      if (response.data.plan_id) {
        const eventSource = createProgressStream(response.data.plan_id, (data) => {
          setProgress({
            current: data.current || 0,
            total: data.total || selectedSlots.size,
            message: data.message || 'Processing...',
          });
          
          // Close stream when complete - check for both 'complete' and 'completed'
          if (data.status === 'completed' || data.status === 'complete' || data.status === 'failed' || data.status === 'error') {
            eventSource.close();
            setIsProcessing(false);
            
            if (data.status === 'completed' || data.status === 'complete') {
              // Use result data from progress stream if available, otherwise use initial response
              const finalResult = {
                ...response.data,
                processed_slots: data.processed_slots ?? response.data.processed_slots ?? 0,
                failed_slots: data.failed_slots ?? response.data.failed_slots ?? 0,
                output_file: data.output_file ?? response.data.output_file,
                errors: data.errors ?? response.data.errors,
              };
              setResult(finalResult);
              setButtonState('success');
              // Ensure progress is at 100%
              setProgress({
                current: data.total || selectedSlots.size,
                total: data.total || selectedSlots.size,
                message: 'Completed successfully',
              });
            } else {
              // Extract error message from progress data
              const errorMessage = data.message || data.error || 'Processing failed';
              setError(errorMessage);
              setButtonState('error');
              
              // Use result data from progress stream if available
              const finalResult = {
                ...response.data,
                processed_slots: data.processed_slots ?? 0,
                failed_slots: data.failed_slots ?? 0,
                errors: data.errors ?? (data.errors && Array.isArray(data.errors) ? data.errors : []),
              };
              setResult(finalResult);
            }
          }
        });
        
      } else {
        // No progress stream, just show result
        setIsProcessing(false);
        if (response.data.success) {
          setResult(response.data);
          setButtonState('success');
        } else {
          setError('Processing failed');
          setButtonState('error');
        }
      }
    } catch (err: any) {
      setIsProcessing(false);
      setError(err.response?.data?.detail || err.message || 'Processing failed');
      setButtonState('error');
    }
  };

  const handleDownload = () => {
    if (!result?.output_file) return;
    
    // Open download URL
    const downloadUrl = `http://localhost:8000/api/render/${result.output_file.split('/').pop()}`;
    window.open(downloadUrl, '_blank');
  };

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

  const progressPercentage = progress.total > 0 
    ? (progress.current / progress.total) * 100 
    : 0;

  // Sort slots by display_order (same as SlotConfigurator)
  const sortedSlots = [...slots].sort((a, b) => {
    const orderA = a.display_order ?? a.slot_number;
    const orderB = b.display_order ?? b.slot_number;
    return orderA - orderB;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Weekly Plan</CardTitle>
        <CardDescription>
          Process {selectedSlots.size} of {slots.length} selected slots for the week
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="week">Week Of (MM-DD-MM-DD)</Label>
          
          {recentWeeks.length > 0 && (
            <div className="mb-2">
              <Label className="text-xs text-muted-foreground">Recent Weeks:</Label>
              <div className="flex gap-2 mt-1">
                {recentWeeks.map((week) => (
                  <Button
                    key={week.week_of}
                    variant="outline"
                    size="sm"
                    onClick={() => setWeekOf(week.week_of)}
                    disabled={isProcessing}
                    className="text-xs"
                  >
                    {week.display}
                  </Button>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex gap-2">
            <Input
              id="week"
              placeholder="e.g., 10-06-10-10"
              value={weekOf}
              onChange={(e) => setWeekOf(e.target.value)}
              disabled={isProcessing}
              className="flex-1"
            />
            <Button
              onClick={handleProcessClick}
              disabled={(buttonState === 'processing' || isProcessing) || !weekOf || selectedSlots.size === 0}
              className={`min-w-[140px] ${
                buttonState === 'success' ? 'bg-green-600 hover:bg-green-700 text-white' : 
                buttonState === 'error' ? 'bg-red-600 hover:bg-red-700 text-white' : ''
              }`}
            >
              {buttonState === 'processing' && (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              )}
              {buttonState === 'success' && (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Done!
                </>
              )}
              {buttonState === 'error' && (
                <>
                  <X className="w-4 h-4 mr-2" />
                  Failed
                </>
              )}
              {buttonState === 'idle' && (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Generate
                </>
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Format: Month-Day-Month-Day (e.g., 10-06-10-10 for Oct 6 - Oct 10)
          </p>
        </div>

        {isProcessing && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{progress.message}</span>
              <span className="font-medium">
                {progress.current} / {progress.total}
              </span>
            </div>
            <Progress value={progressPercentage} max={100} />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              <div className="space-y-2">
                <p>{error}</p>
                {error.includes('Slot') && error.includes('available') && (
                  <div className="mt-2 p-2 bg-destructive/10 rounded text-xs">
                    <p className="font-semibold mb-1">Tip:</p>
                    <p>This document doesn't have enough slots. Please:</p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>Check which slots are actually in the document</li>
                      <li>Select only the available slots (usually slot 1)</li>
                      <li>Or verify the document structure matches your configuration</li>
                    </ul>
                  </div>
                )}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {result && result.success && (
          <Alert variant="success">
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>Success!</AlertTitle>
            <AlertDescription>
              <div className="space-y-2">
                <p>
                  Processed {result.processed_slots} slot(s) successfully
                  {result.failed_slots > 0 && ` (${result.failed_slots} failed)`}
                </p>
                {result.output_file && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    className="mt-2"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Lesson Plan
                  </Button>
                )}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {result && result.errors && result.errors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Partial Failure</AlertTitle>
            <AlertDescription>
              <div className="space-y-1">
                {result.errors.map((err: any, idx: number) => (
                  <div key={idx} className="text-sm">
                    Slot {err.slot} ({err.subject}): {err.error}
                  </div>
                ))}
              </div>
            </AlertDescription>
          </Alert>
        )}

        <div className="pt-4 border-t">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium">Select Slots to Process:</h4>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={selectAllSlots}
                disabled={isProcessing}
              >
                <CheckSquare className="w-4 h-4 mr-1" />
                Select All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={deselectAllSlots}
                disabled={isProcessing}
              >
                <Square className="w-4 h-4 mr-1" />
                Deselect All
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            {sortedSlots.map((slot) => {
              const isSelected = selectedSlots.has(slot.id);
              return (
                <div
                  key={slot.id}
                  className={`flex items-center gap-3 text-sm p-2 rounded cursor-pointer transition-colors ${
                    isSelected ? 'bg-primary/10 border border-primary/20' : 'bg-muted/50 hover:bg-muted'
                  }`}
                  onClick={() => !isProcessing && toggleSlot(slot.id)}
                >
                  <input
                    type="checkbox"
                    id={`slot-checkbox-${slot.id}`}
                    name={`slot-${slot.id}`}
                    checked={isSelected}
                    onChange={() => toggleSlot(slot.id)}
                    disabled={isProcessing}
                    className="w-4 h-4 cursor-pointer"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <div className="flex-1">
                    <span className="font-medium">{slot.subject}</span>
                    {' - '}
                    <span className="text-muted-foreground">
                      {slot.primary_teacher_name || 'No teacher'}, Grade {slot.grade}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm Processing</DialogTitle>
              <DialogDescription>
                Please verify the details before generating the weekly plan.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-3 py-4">
              <div>
                <p className="text-sm font-medium">Source Folder:</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {currentUser?.base_path_override || 'Default path'}
                </p>
              </div>
              
              <div>
                <p className="text-sm font-medium">Week:</p>
                <p className="text-sm text-muted-foreground mt-1">{weekOf}</p>
              </div>
              
              <div>
                <p className="text-sm font-medium">Slots to Process:</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedSlots.size} of {slots.length} slots selected
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowConfirmDialog(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleConfirmProcess}>
                Proceed
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};
