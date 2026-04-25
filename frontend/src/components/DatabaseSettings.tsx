import { useState, useEffect, type ChangeEvent } from 'react';
import { Database, RefreshCw, Trash2, AlertCircle, CheckCircle, Shield, HardDrive, Clock, Copy, CheckSquare, Download, Upload } from 'lucide-react';
import { useStore } from '@lesson-browser';

const API_BASE = 'http://localhost:8000/api';

interface MaintenanceStats {
    db_size_kb: number;
    total_users: number;
    total_plans: number;
    completed_plans: number;
    last_backup: string | null;
}

interface PlanVersionRow {
    id: string;
    generated_at: string | null;
    status: string;
    output_file?: string | null;
    auto_backup_file?: string | null;
}

interface WeekPlanGroup {
    week_of: string;
    plans: PlanVersionRow[];
}

type WeekSortMode = 'school' | 'recent';

/** Parsed plan-backup JSON (matches API export / restore body minus replace_existing). */
interface PlanBackupPayload {
    id: string;
    user_id: string;
    week_of: string;
    status?: string;
    output_file?: string | null;
    week_folder_path?: string | null;
    consolidated?: number;
    total_slots?: number;
    generated_at?: string | null;
    processing_time_ms?: number | null;
    total_tokens?: number | null;
    total_cost_usd?: number | null;
    llm_model?: string | null;
    error_message?: string | null;
    lesson_json?: unknown;
    replace_existing?: boolean;
}

function sanitizeFilenamePart(s: string): string {
    return s.replace(/[/\\:*?"<>|]/g, '_').replace(/\s+/g, '_');
}

type PlanJsonBackupKind = 'manual' | 'pre-delete';

/** Fetches export JSON and triggers a browser download. Throws if the export fails. */
async function downloadWeeklyPlanJsonBackup(
    userId: string,
    planId: string,
    weekOf: string,
    kind: PlanJsonBackupKind
): Promise<void> {
    const res = await fetch(
        `${API_BASE}/users/${userId}/plans/${encodeURIComponent(planId)}/export`
    );
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const safeWeek = sanitizeFilenamePart(weekOf);
    const shortId = planId.replace(/^plan_/, '').slice(0, 12);
    const stem = kind === 'pre-delete' ? 'plan-backup_pre-delete' : 'plan-backup';
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stem}_${safeWeek}_${shortId}_${ts}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

export function DatabaseSettings() {
    const { currentUser } = useStore();
    const [stats, setStats] = useState<MaintenanceStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfirm, setShowConfirm] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'info', text: string } | null>(null);

    const [weekGroups, setWeekGroups] = useState<WeekPlanGroup[]>([]);
    const [loadingWeeks, setLoadingWeeks] = useState(false);
    const [resolvingWeek, setResolvingWeek] = useState<string | null>(null);
    const [exportingPlanId, setExportingPlanId] = useState<string | null>(null);
    const [deletingPlanId, setDeletingPlanId] = useState<string | null>(null);
    const [fullBackupRunning, setFullBackupRunning] = useState(false);
    const [createBackupWhenKeepOnly, setCreateBackupWhenKeepOnly] = useState(true);
    const [weekSortMode, setWeekSortMode] = useState<WeekSortMode>('school');
    const [restorePreview, setRestorePreview] = useState<PlanBackupPayload | null>(null);
    const [restoreReplaceExisting, setRestoreReplaceExisting] = useState(false);
    const [restoreLoading, setRestoreLoading] = useState(false);
    const [restoreFileName, setRestoreFileName] = useState<string | null>(null);
    const [copiedBackupPath, setCopiedBackupPath] = useState<string | null>(null);

    useEffect(() => {
        fetchStats();
    }, []);

    useEffect(() => {
        if (currentUser?.id) {
            fetchPlansByWeek();
        } else {
            setWeekGroups([]);
        }
    }, [currentUser?.id, weekSortMode]);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/admin/maintenance/stats`);
            if (!response.ok) throw new Error('Failed to fetch stats');
            const data = await response.json();
            setStats(data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to load stats');
        } finally {
            setLoading(false);
        }
    };

    const handleRunMaintenance = async () => {
        setRunning(true);
        setShowConfirm(false);
        setMessage({ type: 'info', text: 'Maintenance started in background...' });

        try {
            const response = await fetch(`${API_BASE}/admin/maintenance`, {
                method: 'POST',
            });

            if (!response.ok) throw new Error('Failed to trigger maintenance');

            await response.json();
            setMessage({ type: 'success', text: 'Maintenance task has been queued successfully.' });

            setTimeout(fetchStats, 3000);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Maintenance failed');
            setMessage(null);
        } finally {
            setRunning(false);
        }
    };

    const formatSize = (kb: number) => {
        if (kb > 1024) return `${(kb / 1024).toFixed(2)} MB`;
        return `${kb} KB`;
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return 'Never';
        return new Date(dateStr).toLocaleString();
    };

    const fetchPlansByWeek = async () => {
        if (!currentUser?.id) return;
        setLoadingWeeks(true);
        try {
            const q = new URLSearchParams({ sort: weekSortMode });
            const res = await fetch(`${API_BASE}/users/${currentUser.id}/plans/by-week?${q}`);
            if (!res.ok) throw new Error('Failed to fetch plan versions by week');
            const data = await res.json();
            setWeekGroups(data);
        } catch {
            setWeekGroups([]);
        } finally {
            setLoadingWeeks(false);
        }
    };

    const handleRestoreFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        setRestorePreview(null);
        setRestoreFileName(file ? file.name : null);
        setError(null);
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            try {
                const text = reader.result as string;
                const j = JSON.parse(text) as PlanBackupPayload;
                if (!j || typeof j !== 'object' || !j.id || !j.user_id || !j.week_of) {
                    throw new Error('Missing id, user_id, or week_of');
                }
                setRestorePreview(j);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Invalid JSON backup file');
                setRestorePreview(null);
            }
        };
        reader.onerror = () => {
            setError('Could not read file');
            setRestorePreview(null);
        };
        reader.readAsText(file);
        e.target.value = '';
    };

    const handleRestoreFromBackup = async () => {
        if (!currentUser?.id || !restorePreview) return;
        if (restorePreview.user_id !== currentUser.id) {
            setError('This backup belongs to a different user. Switch user or use another file.');
            return;
        }
        setRestoreLoading(true);
        setError(null);
        setMessage(null);
        try {
            const payload = { ...restorePreview, replace_existing: restoreReplaceExisting };
            const res = await fetch(`${API_BASE}/users/${currentUser.id}/plans/restore-from-export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (res.status === 409) {
                const err = await res.json().catch(() => ({}));
                setError(
                    err.detail ||
                        'A plan with this id already exists. Enable "Replace existing plan" to overwrite it.'
                );
                return;
            }
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || res.statusText);
            }
            const data = await res.json();
            setMessage({
                type: 'success',
                text: `Restored plan ${data.plan_id || restorePreview.id}. Lesson steps are not in JSON backups; open the week in the app to regenerate if needed.`,
            });
            setRestorePreview(null);
            setRestoreFileName(null);
            setRestoreReplaceExisting(false);
            fetchPlansByWeek();
            setTimeout(fetchStats, 500);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Restore failed');
        } finally {
            setRestoreLoading(false);
        }
    };

    const handleFullDatabaseBackup = async () => {
        setFullBackupRunning(true);
        setError(null);
        setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/admin/database/backup`, { method: 'POST' });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || res.statusText);
            }
            const data = await res.json();
            const name = data.backup_path ? String(data.backup_path).split(/[/\\]/).pop() : '';
            setMessage({
                type: 'success',
                text: name ? `Full database backup created: ${name}` : 'Full database backup created.',
            });
            setTimeout(fetchStats, 500);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Backup failed');
        } finally {
            setFullBackupRunning(false);
        }
    };

    const handleBackupPlanJson = async (planId: string, weekOf: string) => {
        if (!currentUser?.id) return;
        setExportingPlanId(planId);
        setError(null);
        try {
            await downloadWeeklyPlanJsonBackup(currentUser.id, planId, weekOf, 'manual');
            setMessage({ type: 'success', text: `Downloaded JSON backup for plan ${planId}.` });
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Export failed');
        } finally {
            setExportingPlanId(null);
        }
    };

    const handleDeletePlan = async (planId: string, weekOf: string) => {
        if (!currentUser?.id) return;
        const ok = window.confirm(
            `Delete this plan version from the database?\n\nWeek: ${weekOf}\nPlan: ${planId}\n\nA JSON backup will be downloaded first (filename starts with plan-backup_pre-delete). If that download fails, nothing will be removed.`
        );
        if (!ok) return;
        setDeletingPlanId(planId);
        setError(null);
        setMessage(null);
        try {
            try {
                await downloadWeeklyPlanJsonBackup(currentUser.id, planId, weekOf, 'pre-delete');
            } catch (backupErr: unknown) {
                const msg =
                    backupErr instanceof Error ? backupErr.message : 'Pre-delete backup failed';
                setError(
                    `${msg} The plan was not deleted. Fix the issue or use Backup to export manually, then try again.`
                );
                return;
            }
            const res = await fetch(
                `${API_BASE}/users/${currentUser.id}/plans/${encodeURIComponent(planId)}`,
                { method: 'DELETE' }
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || res.statusText);
            }
            setMessage({
                type: 'success',
                text: `Downloaded pre-delete JSON backup and removed plan ${planId}.`,
            });
            fetchPlansByWeek();
            setTimeout(fetchStats, 500);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Delete failed');
        } finally {
            setDeletingPlanId(null);
        }
    };

    const handleCopyBackupPath = async (pathValue: string) => {
        try {
            await navigator.clipboard.writeText(pathValue);
            setCopiedBackupPath(pathValue);
            setTimeout(() => setCopiedBackupPath((prev) => (prev === pathValue ? null : prev)), 1500);
        } catch {
            setError('Could not copy backup path to clipboard');
        }
    };

    const handleKeepOnlyThis = async (weekOf: string, keepPlanId: string, otherCount: number) => {
        if (!currentUser?.id) return;
        const ok = window.confirm(
            `Keep only this version and remove ${otherCount} other version(s) for week ${weekOf}?\n\nKeeping: ${keepPlanId}`
        );
        if (!ok) return;
        setResolvingWeek(weekOf);
        setError(null);
        setMessage(null);
        try {
            const res = await fetch(`${API_BASE}/users/${currentUser.id}/plans/resolve-duplicates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    week_of: weekOf,
                    keep_plan_id: keepPlanId,
                    create_backup: createBackupWhenKeepOnly,
                }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || res.statusText);
            }
            const data = await res.json();
            setMessage({
                type: 'success',
                text: data.backup_path
                    ? `Kept 1 plan, removed ${data.removed_count} version(s). Backup: ${String(data.backup_path).split(/[/\\]/).pop()}`
                    : `Kept 1 plan, removed ${data.removed_count} version(s).`,
            });
            fetchPlansByWeek();
            setTimeout(fetchStats, 1000);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Resolve failed');
        } finally {
            setResolvingWeek(null);
        }
    };

    if (loading && !stats) {
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Database className="w-6 h-6" />
                    Database Management
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                    Monitor and maintain your local lesson plan database.
                </p>
            </div>

            {error && (
                <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
                    <div>
                        <p className="text-destructive font-medium">Error</p>
                        <p className="text-sm text-muted-foreground">{error}</p>
                    </div>
                </div>
            )}

            {message && (
                <div className={`${message.type === 'success' ? 'bg-green-500/10 border-green-500/50' : 'bg-blue-500/10 border-blue-500/50'} border rounded-lg p-4 flex items-start gap-3`}>
                    {message.type === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                    ) : (
                        <RefreshCw className="w-5 h-5 text-blue-500 mt-0.5 animate-spin" />
                    )}
                    <div>
                        <p className={`${message.type === 'success' ? 'text-green-500' : 'text-blue-500'} font-medium`}>
                            {message.type === 'success' ? 'Success' : 'Processing'}
                        </p>
                        <p className="text-sm text-muted-foreground">{message.text}</p>
                    </div>
                </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-card border rounded-lg p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <HardDrive className="w-4 h-4" />
                        <span className="text-sm font-medium">Database Size</span>
                    </div>
                    <p className="text-2xl font-bold">{stats ? formatSize(stats.db_size_kb) : '---'}</p>
                </div>

                <div className="bg-card border rounded-lg p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Database className="w-4 h-4" />
                        <span className="text-sm font-medium">Total Plans</span>
                    </div>
                    <p className="text-2xl font-bold">{stats?.total_plans ?? '---'}</p>
                </div>

                <div className="bg-card border rounded-lg p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Shield className="w-4 h-4" />
                        <span className="text-sm font-medium">Completed</span>
                    </div>
                    <p className="text-2xl font-bold text-green-500">{stats?.completed_plans ?? '---'}</p>
                </div>

                <div className="bg-card border rounded-lg p-4">
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm font-medium">Last Backup</span>
                    </div>
                    <p className="text-sm font-semibold truncate" title={stats?.last_backup || undefined}>
                        {stats ? formatDate(stats.last_backup) : '---'}
                    </p>
                </div>
            </div>

            {/* Maintenance Card */}
            <div className="bg-card border rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b bg-muted/30">
                    <h3 className="font-semibold flex items-center gap-2 text-lg">
                        <RefreshCw className="w-5 h-5" />
                        Maintenance Tasks
                    </h3>
                </div>
                <div className="p-6 space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-1">
                            <p className="font-medium">Optimize and Cleanup</p>
                            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                                <li>Create a timestamped backup in /data/archives/</li>
                                <li>Remove invalid 'password' user accounts</li>
                                <li>Prune redundant/failed plans (keep latest completed per week)</li>
                            </ul>
                        </div>

                        {!showConfirm ? (
                            <button
                                onClick={() => setShowConfirm(true)}
                                disabled={running}
                                className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                                Run Maintenance Now
                            </button>
                        ) : (
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setShowConfirm(false)}
                                    className="px-4 py-2 border rounded-md hover:bg-muted transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleRunMaintenance}
                                    className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors flex items-center gap-2"
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Confirm Cleanup
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 flex gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-yellow-800 dark:text-yellow-200">
                            <strong>Warning:</strong> Pruning will permanently delete older draft versions of lesson plans for each week. Only the most recent completed plan will be kept.
                        </p>
                    </div>
                </div>
            </div>

            {currentUser && (
                <div className="bg-card border rounded-lg overflow-hidden">
                    <div className="px-6 py-4 border-b bg-muted/30">
                        <h3 className="font-semibold flex items-center gap-2 text-lg">
                            <Copy className="w-5 h-5" />
                            Weekly plan versions
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Each row is one stored version for that week (newest version first within each week). Download JSON to back up a version before deleting it. Use &quot;Keep only this&quot; when a week has multiple versions and you want one click to remove the rest (optional full database backup first).
                        </p>
                    </div>
                    <div className="p-6 space-y-4">
                        <div className="space-y-2">
                            <p className="text-sm font-medium">Week order</p>
                            <div className="flex flex-wrap gap-2">
                                <button
                                    type="button"
                                    onClick={() => setWeekSortMode('school')}
                                    className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                                        weekSortMode === 'school'
                                            ? 'bg-primary text-primary-foreground border-primary'
                                            : 'hover:bg-muted border-border'
                                    }`}
                                >
                                    School calendar
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setWeekSortMode('recent')}
                                    className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                                        weekSortMode === 'recent'
                                            ? 'bg-primary text-primary-foreground border-primary'
                                            : 'hover:bg-muted border-border'
                                    }`}
                                >
                                    Recently updated
                                </button>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {weekSortMode === 'school'
                                    ? 'Weeks are ordered by real calendar (newest week first). Labels without a year: if the week is within the next few days, that upcoming date is used; otherwise the most recent past occurrence of that week (so last fall stays below this spring).'
                                    : 'Weeks are ordered by the most recent generated time of any version in that week.'}
                            </p>
                        </div>

                        <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3">
                            <button
                                type="button"
                                onClick={handleFullDatabaseBackup}
                                disabled={fullBackupRunning}
                                className="px-4 py-2 border rounded-md hover:bg-muted transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm w-fit"
                            >
                                {fullBackupRunning ? (
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                    <HardDrive className="w-4 h-4" />
                                )}
                                {fullBackupRunning ? 'Backing up…' : 'Backup entire database now'}
                            </button>
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={createBackupWhenKeepOnly}
                                    onChange={(e) => setCreateBackupWhenKeepOnly(e.target.checked)}
                                    className="w-4 h-4"
                                />
                                Create full DB backup before &quot;Keep only this&quot; removes other versions
                            </label>
                        </div>

                        {loadingWeeks ? (
                            <div className="flex items-center justify-center py-8">
                                <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : weekGroups.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-4">
                                No weekly plans in the database for this user.
                            </p>
                        ) : (
                            <div className="space-y-6">
                                {weekGroups.map((week) => (
                                    <div key={week.week_of} className="border rounded-lg overflow-hidden">
                                        <div className="px-3 py-2 bg-muted/40 border-b flex flex-wrap items-baseline justify-between gap-2">
                                            <p className="font-medium text-sm">
                                                Week of {week.week_of}
                                                <span className="text-muted-foreground font-normal ml-2">
                                                    ({week.plans.length} version{week.plans.length === 1 ? '' : 's'})
                                                </span>
                                            </p>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b bg-muted/20 text-left">
                                                        <th className="p-2 font-medium">Plan ID</th>
                                                        <th className="p-2 font-medium whitespace-nowrap">Generated</th>
                                                        <th className="p-2 font-medium">Status</th>
                                                        <th className="p-2 font-medium">Auto backup file</th>
                                                        <th className="p-2 font-medium text-right whitespace-nowrap">Actions</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {week.plans.map((plan) => (
                                                        <tr key={plan.id} className="border-b border-border/60 last:border-0">
                                                            <td className="p-2 font-mono text-xs align-top break-all max-w-[200px]" title={plan.id}>
                                                                {plan.id}
                                                            </td>
                                                            <td className="p-2 text-xs text-muted-foreground whitespace-nowrap align-top">
                                                                {plan.generated_at ? new Date(plan.generated_at).toLocaleString() : '—'}
                                                            </td>
                                                            <td className="p-2 align-top">
                                                                <span className="text-xs px-2 py-0.5 rounded bg-muted">{plan.status}</span>
                                                            </td>
                                                            <td className="p-2 align-top">
                                                                {plan.auto_backup_file ? (
                                                                    <div className="flex flex-col gap-1">
                                                                        <code className="text-[11px] break-all">{plan.auto_backup_file}</code>
                                                                        <button
                                                                            type="button"
                                                                            onClick={() => handleCopyBackupPath(plan.auto_backup_file as string)}
                                                                            className="px-2 py-1 text-xs border rounded-md hover:bg-muted w-fit inline-flex items-center gap-1"
                                                                        >
                                                                            {copiedBackupPath === plan.auto_backup_file ? (
                                                                                <CheckCircle className="w-3 h-3" />
                                                                            ) : (
                                                                                <Copy className="w-3 h-3" />
                                                                            )}
                                                                            {copiedBackupPath === plan.auto_backup_file ? 'Copied' : 'Copy path'}
                                                                        </button>
                                                                    </div>
                                                                ) : (
                                                                    <span className="text-xs text-muted-foreground">Not available</span>
                                                                )}
                                                            </td>
                                                            <td className="p-2 align-top">
                                                                <div className="flex flex-wrap justify-end gap-1.5">
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => handleBackupPlanJson(plan.id, week.week_of)}
                                                                        disabled={exportingPlanId === plan.id}
                                                                        className="px-2 py-1 text-xs border rounded-md hover:bg-muted disabled:opacity-50 inline-flex items-center gap-1"
                                                                    >
                                                                        {exportingPlanId === plan.id ? (
                                                                            <RefreshCw className="w-3 h-3 animate-spin" />
                                                                        ) : (
                                                                            <Download className="w-3 h-3" />
                                                                        )}
                                                                        Backup
                                                                    </button>
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => handleDeletePlan(plan.id, week.week_of)}
                                                                        disabled={deletingPlanId === plan.id}
                                                                        className="px-2 py-1 text-xs border border-destructive/50 text-destructive rounded-md hover:bg-destructive/10 disabled:opacity-50 inline-flex items-center gap-1"
                                                                    >
                                                                        {deletingPlanId === plan.id ? (
                                                                            <RefreshCw className="w-3 h-3 animate-spin" />
                                                                        ) : (
                                                                            <Trash2 className="w-3 h-3" />
                                                                        )}
                                                                        Delete
                                                                    </button>
                                                                    {week.plans.length > 1 && (
                                                                        <button
                                                                            type="button"
                                                                            onClick={() =>
                                                                                handleKeepOnlyThis(
                                                                                    week.week_of,
                                                                                    plan.id,
                                                                                    week.plans.length - 1
                                                                                )
                                                                            }
                                                                            disabled={resolvingWeek === week.week_of}
                                                                            className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 inline-flex items-center gap-1"
                                                                        >
                                                                            {resolvingWeek === week.week_of ? (
                                                                                <RefreshCw className="w-3 h-3 animate-spin" />
                                                                            ) : (
                                                                                <CheckSquare className="w-3 h-3" />
                                                                            )}
                                                                            Keep only this
                                                                        </button>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {currentUser && (
                <div className="bg-card border rounded-lg overflow-hidden">
                    <div className="px-6 py-4 border-b bg-muted/30">
                        <h3 className="font-semibold flex items-center gap-2 text-lg">
                            <Upload className="w-5 h-5" />
                            Restore from backup file
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Deleting a version downloads a <code className="text-xs">plan-backup_pre-delete</code> JSON file first, then removes the row. You can also use <strong>Backup</strong> anytime. Restore uses the same JSON format; it does not restore lesson-step rows from Lesson Mode (only the weekly plan and <code className="text-xs">lesson_json</code>).
                        </p>
                    </div>
                    <div className="p-6 space-y-4">
                        <div>
                            <label className="text-sm font-medium block mb-2">Choose JSON backup</label>
                            <input
                                type="file"
                                accept=".json,application/json"
                                onChange={handleRestoreFileChange}
                                className="text-sm w-full max-w-md"
                            />
                            {restoreFileName && (
                                <p className="text-xs text-muted-foreground mt-1">Selected: {restoreFileName}</p>
                            )}
                        </div>
                        {restorePreview && (
                            <div className="border rounded-lg p-4 bg-muted/20 space-y-2 text-sm">
                                <p className="font-medium">Preview</p>
                                <ul className="text-xs font-mono space-y-1 break-all">
                                    <li>id: {restorePreview.id}</li>
                                    <li>user_id: {restorePreview.user_id}</li>
                                    <li>week_of: {restorePreview.week_of}</li>
                                    <li>status: {restorePreview.status ?? '—'}</li>
                                </ul>
                                {restorePreview.user_id !== currentUser.id && (
                                    <p className="text-xs text-destructive">
                                        This file is for another user. Switch to that user in the app before restoring.
                                    </p>
                                )}
                                <label className="flex items-center gap-2 text-sm cursor-pointer pt-2">
                                    <input
                                        type="checkbox"
                                        checked={restoreReplaceExisting}
                                        onChange={(e) => setRestoreReplaceExisting(e.target.checked)}
                                        className="w-4 h-4"
                                    />
                                    Replace existing plan if this id is already in the database (removes current row first)
                                </label>
                                <button
                                    type="button"
                                    onClick={handleRestoreFromBackup}
                                    disabled={
                                        restoreLoading ||
                                        restorePreview.user_id !== currentUser.id
                                    }
                                    className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 text-sm flex items-center gap-2"
                                >
                                    {restoreLoading ? (
                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Upload className="w-4 h-4" />
                                    )}
                                    {restoreLoading ? 'Restoring…' : 'Restore plan'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="bg-card border border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center opacity-60">
                <Database className="w-10 h-10 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">Sync logs and cloud integrations may appear in future updates.</p>
            </div>
        </div>
    );
}
