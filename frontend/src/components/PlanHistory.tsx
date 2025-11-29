import React, { useState, useMemo } from 'react';
import { Download, Clock, CheckCircle2, XCircle, Loader2, FolderOpen, ExternalLink } from 'lucide-react';
import { useStore } from '@lesson-browser';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { formatDate, formatWeekOf } from '../lib/utils';
import { isDesktop } from '../lib/platform';
import { getNetworkApiBaseUrl } from '@lesson-api';

export const PlanHistory: React.FC = () => {
  const { currentUser, plans } = useStore();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'week' | 'status'>('date');
  const networkApiBaseUrl = getNetworkApiBaseUrl();
  const apiRoot = networkApiBaseUrl.replace(/\/api$/, '');

  const handleDownload = async (filepath: string, planId?: string) => {
    try {
      if (isDesktop) {
        // Use Tauri file dialog in desktop app
        const { invoke } = await import('@tauri-apps/api/core');
        const destination = await invoke<string>('save_file_dialog', { sourcePath: filepath });
        alert(`File saved successfully to:\n${destination}`);
      } else {
        // Browser: Download via API endpoint
        if (planId) {
          // Use plan ID endpoint (safer, handles full paths)
          const filename = filepath.split('/').pop() || filepath.split('\\').pop() || 'plan.docx';
          const downloadUrl = `${networkApiBaseUrl}/plans/${planId}/download`;

          // Fetch file as blob and download
          const response = await fetch(downloadUrl, {
            headers: currentUser ? { 'X-Current-User-Id': currentUser.id } : {},
          });

          if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
          }

          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } else {
          // Fallback: Try direct filename approach
          const filename = filepath.split('/').pop() || filepath.split('\\').pop() || 'plan.docx';
          const downloadUrl = `${apiRoot}/api/render/${filename}`;

          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    } catch (error: any) {
      // Don't show alert if user cancelled (Tauri)
      if (error !== 'Save cancelled by user') {
        console.error('Failed to download file:', error);
        alert(`Failed to download file: ${error.message || error}`);
      }
    }
  };

  const handleShowInFolder = async (filepath: string) => {
    if (!isDesktop) {
      // Web fallback: Copy path to clipboard
      try {
        await navigator.clipboard.writeText(filepath);
        alert('File path copied to clipboard:\n' + filepath);
      } catch (err) {
        console.error('Failed to copy path:', err);
        alert('File path:\n' + filepath);
      }
      return;
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('show_in_folder', { path: filepath });
    } catch (error) {
      console.error('Failed to show in folder:', error);
      alert(`Failed to open folder: ${error}`);
    }
  };

  const handleOpenFile = async (filepath: string, planId?: string) => {
    if (!isDesktop) {
      // Browser: Open file in new tab using plan ID endpoint
      if (planId) {
        const downloadUrl = `${networkApiBaseUrl}/plans/${planId}/download`;
        window.open(downloadUrl, '_blank');
      } else {
        // Fallback: Try direct filename approach (may not work with full paths)
        const filename = filepath.split('/').pop() || filepath.split('\\').pop() || 'plan.docx';
        const downloadUrl = `${apiRoot}/api/render/${filename}`;
        window.open(downloadUrl, '_blank');
      }
      return;
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('open_file', { path: filepath });
    } catch (error) {
      console.error('Failed to open file:', error);
      alert(`Failed to open file: ${error}`);
    }
  };

  if (!currentUser) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please select a user to view plan history
        </CardContent>
      </Card>
    );
  }

  // Filter and sort plans
  const filteredAndSortedPlans = useMemo(() => {
    let filtered = [...plans];

    // Filter out stuck "processing" plans (older than 1 hour)
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    filtered = filtered.filter(p => {
      if (p.status === 'processing') {
        const generatedTime = new Date(p.generated_at).getTime();
        return generatedTime > oneHourAgo; // Only show recent processing
      }
      return true; // Show all other statuses
    });

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(p => p.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
        case 'week':
          return b.week_of.localeCompare(a.week_of);
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

    return filtered;
  }, [plans, statusFilter, sortBy]);

  const statusCounts = useMemo(() => {
    return {
      all: plans.length,
      completed: plans.filter(p => p.status === 'completed').length,
      failed: plans.filter(p => p.status === 'failed').length,
      processing: plans.filter(p => p.status === 'processing').length,
    };
  }, [plans]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Plan History</CardTitle>
            <CardDescription>
              {statusCounts.all} total plans ({statusCounts.completed} completed, {statusCounts.failed} failed)
            </CardDescription>
          </div>
        </div>

        {/* Filters and Sorting */}
        <div className="flex gap-4 mt-4 flex-wrap">
          <div className="flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
            >
              All ({statusCounts.all})
            </Button>
            <Button
              variant={statusFilter === 'completed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('completed')}
            >
              Completed ({statusCounts.completed})
            </Button>
            <Button
              variant={statusFilter === 'failed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('failed')}
            >
              Failed ({statusCounts.failed})
            </Button>
          </div>

          <div className="flex gap-2 items-center ml-auto">
            <span className="text-sm text-muted-foreground">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-sm border rounded px-2 py-1 bg-background"
            >
              <option value="date">Date</option>
              <option value="week">Week</option>
              <option value="status">Status</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {filteredAndSortedPlans.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No plans generated yet
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAndSortedPlans.map((plan) => (
              <div
                key={plan.id}
                className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-shrink-0">
                  {plan.status === 'completed' && (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  )}
                  {plan.status === 'failed' && (
                    <XCircle className="w-5 h-5 text-destructive" />
                  )}
                  {plan.status === 'processing' && (
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  )}
                  {plan.status === 'pending' && (
                    <Clock className="w-5 h-5 text-muted-foreground" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">
                    {formatWeekOf(plan.week_of)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Generated {formatDate(plan.generated_at)}
                  </div>
                  {plan.error_message && (
                    <div className="text-sm text-destructive mt-1">
                      {plan.error_message}
                    </div>
                  )}
                </div>

                {plan.status === 'completed' && plan.output_file && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(plan.output_file!, plan.id)}
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    {isDesktop && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleShowInFolder(plan.output_file!)}
                        title="Show in folder"
                      >
                        <FolderOpen className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenFile(plan.output_file!, plan.id)}
                      title="Open file"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
