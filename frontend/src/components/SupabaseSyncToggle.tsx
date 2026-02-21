import { useState, useEffect } from 'react';
import { settingsApi } from '@lesson-api';

export function SupabaseSyncToggle() {
  const [enableSync, setEnableSync] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('[SupabaseSyncToggle] Loading settings...');
      const response = await settingsApi.getSupabaseSync();
      console.log('[SupabaseSyncToggle] Full response:', JSON.stringify(response, null, 2));
      console.log('[SupabaseSyncToggle] Response.data:', response.data);
      console.log('[SupabaseSyncToggle] Response.data.enable_supabase_sync:', response.data?.enable_supabase_sync);
      
      if (response.data && typeof response.data.enable_supabase_sync === 'boolean') {
        setEnableSync(response.data.enable_supabase_sync);
      } else {
        console.warn('[SupabaseSyncToggle] Unexpected response format, using default:', response.data);
        setEnableSync(true);
      }
    } catch (err: any) {
      console.error('[SupabaseSyncToggle] Failed to load settings:', err);
      console.error('[SupabaseSyncToggle] Error details:', err);
      setError(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (enabled: boolean) => {
    setSaving(true);
    setError(null);
    try {
      await settingsApi.setSupabaseSync(enabled);
      setEnableSync(enabled);
      console.log(`Supabase sync ${enabled ? 'enabled' : 'disabled'}`);
    } catch (err: any) {
      console.error('Failed to save settings:', err);
      setError(err.message || 'Failed to save settings');
      // Revert the toggle on error
      setEnableSync(!enabled);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="px-6 py-4 bg-card border-b">
        <h2 className="text-lg font-semibold">User Settings</h2>
        <p className="text-sm text-muted-foreground">Manage your application preferences</p>
      </div>
      
      <div className="p-6 space-y-6">
        {loading && (
          <div className="text-center py-4 text-sm text-muted-foreground">Loading settings...</div>
        )}
        {error && (
          <div className="text-red-600 text-sm mb-4 p-2 bg-red-50 rounded">{error}</div>
        )}
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <label className="text-sm font-medium">
                Enable Supabase Synchronization
              </label>
              <p className="text-sm text-muted-foreground mt-1">
                Sync lesson plans and data with Supabase cloud storage. When disabled, the application will use local SQLite storage only.
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={enableSync}
              onClick={() => handleToggle(!enableSync)}
              disabled={saving || loading}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ml-4
                ${enableSync ? 'bg-blue-600' : 'bg-gray-200'}
                ${saving || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${enableSync ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

