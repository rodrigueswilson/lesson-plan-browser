import React, { useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, FolderOpen, HardDrive, Tablet } from 'lucide-react';
import { useStore } from '@lesson-browser';
import { tabletApi, type TabletExportDbResponse } from '@lesson-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { isDesktop } from '../lib/platform';

export const TabletSync: React.FC = () => {
  const { currentUser } = useStore();
  const [exporting, setExporting] = useState(false);
  const [pushing, setPushing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TabletExportDbResponse | null>(null);
  const [pushStatus, setPushStatus] = useState<string | null>(null);

  const expectedRelativePath = useMemo(() => {
    if (!currentUser) return null;
    return `data/tablet_db_exports/${currentUser.id}/lesson_planner.db`;
  }, [currentUser]);

  const handleShowInFolder = async (filepath: string) => {
    if (!isDesktop) {
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
    } catch (e) {
      console.error('Failed to show in folder:', e);
      alert(`Failed to open folder: ${e}`);
    }
  };

  const handleExport = async () => {
    if (!currentUser) return;
    setExporting(true);
    setError(null);

    try {
      const response = await tabletApi.exportDb(currentUser.id, currentUser.id);
      setResult(response.data);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setExporting(false);
    }
  };

  const ensureExport = async (): Promise<TabletExportDbResponse> => {
    if (result?.output_path) return result;
    const response = await tabletApi.exportDb(currentUser!.id, currentUser!.id);
    setResult(response.data);
    return response.data;
  };

  const handlePushToTablet = async () => {
    if (!currentUser) return;
    if (!isDesktop) {
      setError('This action requires the desktop app (Tauri). Run it with `npm run tauri:dev`.');
      setPushStatus(null);
      return;
    }
    setPushing(true);
    setError(null);
    setPushStatus('Exporting database...');

    try {
      const exported = await ensureExport();
      setPushStatus('Pushing database to tablet (ADB)...');

      const { invoke } = await import('@tauri-apps/api/core');
      // Rust expects snake_case param; Tauri JS uses camelCase
      await invoke('push_tablet_db', { dbPath: exported.output_path });

      setPushStatus('Push complete. Tablet app restarted.');
    } catch (e: any) {
      setError(e?.message || String(e));
      setPushStatus(null);
    } finally {
      setPushing(false);
    }
  };

  const handleInstallApk = async () => {
    if (!isDesktop) {
      setError('This action requires the desktop app (Tauri). Run it with `npm run tauri:dev`.');
      setPushStatus(null);
      return;
    }
    setError(null);
    setPushStatus('Installing latest APK (ADB)...');
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('install_tablet_apk_latest');
      setPushStatus('APK installed. You can now push the DB.');
    } catch (e: any) {
      setError(e?.message || String(e));
      setPushStatus(null);
    }
  };

  const handleBuildApk = async () => {
    if (!currentUser) return;
    if (!isDesktop) {
      setError('This action requires the desktop app (Tauri). Run it with `npm run tauri:dev`.');
      setPushStatus(null);
      return;
    }
    setError(null);
    setPushStatus('Exporting database for build...');
    try {
      const exported = await ensureExport();
      setPushStatus(
        'Building APK (this may take several minutes). The message will only update when the build finishes or fails. For live output, run .\\build-apk.ps1 in a terminal from the project root.'
      );
      const { invoke } = await import('@tauri-apps/api/core');
      const res: any = await invoke('build_tablet_apk', {
        dbPath: exported.output_path,
        target: 'arm64',
        release: false,
      });
      // Show tail end in status; full output is in logs/terminal usually, but keep something visible.
      const out = (res?.output || '').toString();
      const tail = out.length > 1200 ? out.slice(-1200) : out;
      setPushStatus('Build complete.\n' + tail);
    } catch (e: any) {
      setError(e?.message || String(e));
      setPushStatus(null);
    }
  };
  if (!currentUser) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Please select a user to export a tablet database
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Tablet className="w-6 h-6" />
          Tablet Database Export
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Creates a <strong>single-user</strong> SQLite database for bundling into the tablet APK.
        </p>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
          <div>
            <p className="text-destructive font-medium">Operation failed</p>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{error}</p>
          </div>
        </div>
      )}

      {pushStatus && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">{pushStatus}</p>
        </div>
      )}

      {result && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
          <div className="min-w-0">
            <p className="text-green-700 dark:text-green-300 font-medium">Export complete</p>
            <p className="text-sm text-muted-foreground">
              Wrote <strong>{(result.output_bytes / (1024 * 1024)).toFixed(2)} MB</strong> at:
            </p>
            <p className="text-sm font-mono break-all mt-1">{result.output_path}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleShowInFolder(result.output_path)}
              >
                <FolderOpen className="w-4 h-4 mr-2" />
                Show in folder
              </Button>
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Export for {currentUser.name}</CardTitle>
          <CardDescription>
            Output (relative): <span className="font-mono">{expectedRelativePath}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            This export copies only <strong>{currentUser.name}</strong>’s data from the shared database into a new
            SQLite file.
          </div>

          <Button type="button" onClick={handleExport} disabled={exporting}>
            <HardDrive className="w-4 h-4 mr-2" />
            {exporting ? 'Exporting…' : 'Export user-only tablet DB'}
          </Button>

          <Button type="button" variant="outline" onClick={handleInstallApk} disabled={!isDesktop}>
            Install latest APK (ADB)
          </Button>

          <Button type="button" variant="outline" onClick={handleBuildApk} disabled={!isDesktop}>
            Build APK (arm64 debug)
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={handlePushToTablet}
            disabled={!isDesktop || pushing}
          >
            {pushing ? 'Pushing…' : 'Push to tablet (ADB)'}
          </Button>

          {result && (
            <div className="text-sm text-muted-foreground">
              Rows copied: users={result.counts.users}, slots={result.counts.class_slots}, plans=
              {result.counts.weekly_plans}, schedules={result.counts.schedules}, steps={result.counts.lesson_steps}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

