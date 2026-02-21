import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, X } from 'lucide-react';
import { Button } from '@lesson-ui/Button';
import { settingsApi } from '@lesson-api';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Settings({ isOpen, onClose }: SettingsProps) {
  const [enableSync, setEnableSync] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('[Settings] Loading settings...');
      const response = await settingsApi.getSupabaseSync();
      console.log('[Settings] Full response:', JSON.stringify(response, null, 2));
      console.log('[Settings] Response.data:', response.data);
      console.log('[Settings] Response.data.enable_supabase_sync:', response.data?.enable_supabase_sync);
      
      if (response.data && typeof response.data.enable_supabase_sync === 'boolean') {
        setEnableSync(response.data.enable_supabase_sync);
      } else {
        console.warn('[Settings] Unexpected response format, using default:', response.data);
        setEnableSync(true);
      }
    } catch (err: any) {
      console.error('[Settings] Failed to load settings:', err);
      console.error('[Settings] Error details:', err);
      setError(err.message || 'Failed to load settings');
      // Don't set loading to false on error so user can see the error message
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            <h2 className="text-xl font-semibold">Settings</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-6 space-y-4">
          {loading && (
            <div className="text-center py-4 text-sm text-muted-foreground">Loading settings...</div>
          )}
          {error && (
            <div className="text-red-600 text-sm mb-4 p-2 bg-red-50 rounded">{error}</div>
          )}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <label className="text-sm font-medium">
                  Enable Supabase Synchronization
                </label>
                <p className="text-sm text-muted-foreground mt-1">
                  Sync lesson plans and data with Supabase cloud storage
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={enableSync}
                onClick={() => handleToggle(!enableSync)}
                disabled={saving || loading}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
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
    </div>
  );
}

