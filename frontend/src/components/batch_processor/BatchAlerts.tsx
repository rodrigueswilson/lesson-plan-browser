import { AlertCircle, CheckCircle2, Download } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '../ui/Alert';
import { Button } from '../ui/Button';
import type { ProcessResult } from './useBatchProcessor';

interface BatchAlertsProps {
  error: string | null;
  result: ProcessResult | null;
  onDownload: () => void;
}

export function BatchAlerts({ error, result, onDownload }: BatchAlertsProps) {
  return (
    <>
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
                  <p>This document doesn&apos;t have enough slots. Please:</p>
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
                {result.failed_slots && result.failed_slots > 0 ? ` (${result.failed_slots} failed)` : ''}
              </p>
              {result.output_file && (
                <Button variant="outline" size="sm" onClick={onDownload} className="mt-2">
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
              {result.errors.map((err, idx) => (
                <div key={idx} className="text-sm">
                  Slot {err.slot} ({err.subject}): {err.error}
                </div>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </>
  );
}
