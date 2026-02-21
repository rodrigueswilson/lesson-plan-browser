/**
 * Temporary test component for testing IPC sync functionality
 * This can be removed after testing is complete
 */

import { useState } from 'react';
import { triggerSync } from '@lesson-api';
import { useStore } from '@lesson-browser';

export function SyncTestButton() {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const currentUser = useStore((state) => state.currentUser);

  const handleSync = async () => {
    if (!currentUser?.id) {
      setError('No user selected');
      return;
    }

    setSyncing(true);
    setResult(null);
    setError(null);

    try {
      const syncResult = await triggerSync(currentUser.id);
      setResult(
        `Sync completed! Pulled: ${syncResult.pulled}, Pushed: ${syncResult.pushed}${
          syncResult.conflicts ? `, Conflicts: ${syncResult.conflicts.length}` : ''
        }`
      );
    } catch (err: any) {
      const msg = err.message || 'Sync failed';
      setError(
        msg.includes('Supabase not configured')
          ? 'Supabase is not configured. Sync requires SUPABASE_URL and SUPABASE_KEY in .env. You can use the app with local data only.'
          : msg
      );
      console.error('Sync error:', err);
    } finally {
      setSyncing(false);
    }
  };

  if (!currentUser) {
    return null;
  }

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="text-sm font-semibold mb-2">IPC Sync Test</h3>
      <button
        onClick={handleSync}
        disabled={syncing}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
      >
        {syncing ? 'Syncing...' : 'Test Sync'}
      </button>
      {result && (
        <div className="mt-2 p-2 bg-green-100 text-green-800 rounded text-sm">
          {result}
        </div>
      )}
      {error && (
        <div className="mt-2 p-2 bg-red-100 text-red-800 rounded text-sm">
          Error: {error}
        </div>
      )}
    </div>
  );
}

