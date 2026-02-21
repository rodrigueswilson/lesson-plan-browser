import { useState, useEffect } from 'react';
import { Database, RefreshCw, Trash2, AlertCircle, CheckCircle, Shield, HardDrive, Clock } from 'lucide-react';
import { useStore } from '@lesson-browser';

interface MaintenanceStats {
    db_size_kb: number;
    total_users: number;
    total_plans: number;
    completed_plans: number;
    last_backup: string | null;
}

export function DatabaseSettings() {
    const { currentUser } = useStore();
    const [stats, setStats] = useState<MaintenanceStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfirm, setShowConfirm] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'info', text: string } | null>(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/admin/maintenance/stats');
            if (!response.ok) throw new Error('Failed to fetch stats');
            const data = await response.json();
            setStats(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRunMaintenance = async () => {
        setRunning(true);
        setShowConfirm(false);
        setMessage({ type: 'info', text: 'Maintenance started in background...' });

        try {
            const response = await fetch('http://localhost:8000/api/admin/maintenance', {
                method: 'POST',
            });

            if (!response.ok) throw new Error('Failed to trigger maintenance');

            const data = await response.json();
            setMessage({ type: 'success', text: 'Maintenance task has been queued successfully.' });

            // Refresh stats after a short delay
            setTimeout(fetchStats, 3000);
        } catch (err: any) {
            setError(err.message);
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

            {/* Future Expansion */}
            <div className="bg-card border border-dashed rounded-lg p-12 flex flex-col items-center justify-center text-center opacity-60">
                <Database className="w-12 h-12 text-muted-foreground mb-4" />
                <h3 className="font-medium">Future Data Features</h3>
                <p className="text-sm text-muted-foreground max-w-xs mt-1">
                    Export full database, view sync logs, and manage cloud storage integrations here in future updates.
                </p>
            </div>
        </div>
    );
}
