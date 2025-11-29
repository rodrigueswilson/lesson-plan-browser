// Improved UserSelector with better error handling and debugging
// Replace the content of frontend/src/components/UserSelector.tsx with this

import React, { useEffect, useState } from 'react';
import { User, Plus, FolderOpen, Settings, AlertCircle } from 'lucide-react';
import { useStore } from '../store/useStore';
import { userApi, slotApi, planApi } from '../lib/api';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { Input } from './ui/Input';
import { Label } from './ui/Label';

export const UserSelector: React.FC = () => {
  const { currentUser, setCurrentUser, users, setUsers, setSlots, setPlans } = useStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [basePath, setBasePath] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[UserSelector] Component mounted, loading users...');
    loadUsers();
  }, []);

  const loadUsers = async () => {
    console.log('[UserSelector] loadUsers() called');
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('[UserSelector] Fetching users from API...');
      const response = await userApi.list();
      console.log('[UserSelector] Users loaded:', response.data.length, 'users');
      setUsers(response.data);
      
      // Auto-select first user if none selected
      if (!currentUser && response.data.length > 0) {
        console.log('[UserSelector] Auto-selecting first user:', response.data[0].name);
        await selectUser(response.data[0].id);
      }
    } catch (error: any) {
      console.error('[UserSelector] Failed to load users:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to load users: ${errorMsg}`);
      
      // Show alert for critical error
      alert(`Cannot load users!\n\nError: ${errorMsg}\n\nMake sure the backend is running on http://localhost:8000`);
    } finally {
      setIsLoading(false);
    }
  };

  const selectUser = async (userId: string) => {
    console.log('[UserSelector] Selecting user:', userId);
    setError(null);
    
    try {
      const [userResponse, slotsResponse, plansResponse] = await Promise.all([
        userApi.get(userId),
        slotApi.list(userId),
        planApi.list(userId),
      ]);
      
      console.log('[UserSelector] User data loaded:', {
        user: userResponse.data.name,
        slots: slotsResponse.data.length,
        plans: plansResponse.data.length
      });
      
      setCurrentUser(userResponse.data);
      setSlots(slotsResponse.data);
      setPlans(plansResponse.data);
      setBasePath(userResponse.data.base_path_override || '');
    } catch (error: any) {
      console.error('[UserSelector] Failed to select user:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to load user data: ${errorMsg}`);
    }
  };

  const handleUpdateBasePath = async () => {
    if (!currentUser || !basePath.trim()) return;
    
    console.log('[UserSelector] Updating base path:', basePath);
    setError(null);
    
    try {
      await userApi.updateBasePath(currentUser.id, basePath);
      setShowSettings(false);
      // Reload user to get updated data
      await selectUser(currentUser.id);
      alert('Base path updated successfully!');
    } catch (error: any) {
      console.error('[UserSelector] Failed to update base path:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to update path: ${errorMsg}`);
      alert(`Failed to update path: ${errorMsg}`);
    }
  };

  const handleAddUser = async () => {
    if (!newUserName.trim()) {
      alert('Please enter a name');
      return;
    }
    
    console.log('[UserSelector] Creating user:', { name: newUserName, email: newUserEmail });
    setIsCreating(true);
    setError(null);
    
    try {
      console.log('[UserSelector] Sending create user request...');
      const response = await userApi.create(newUserName, newUserEmail || undefined);
      console.log('[UserSelector] User created successfully:', response.data);
      
      // Reload users list
      await loadUsers();
      
      // Select the newly created user
      await selectUser(response.data.id);
      
      // Reset form
      setShowAddUser(false);
      setNewUserName('');
      setNewUserEmail('');
      
      alert(`User "${response.data.name}" created successfully!`);
    } catch (error: any) {
      console.error('[UserSelector] Failed to create user:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to create user: ${errorMsg}`);
      alert(`Failed to create user!\n\nError: ${errorMsg}\n\nCheck the browser console for details.`);
    } finally {
      setIsCreating(false);
    }
  };

  // Show error banner if there's an error
  const ErrorBanner = error ? (
    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm font-medium text-red-900">Error</p>
        <p className="text-sm text-red-700">{error}</p>
      </div>
      <button
        onClick={() => setError(null)}
        className="text-red-600 hover:text-red-800"
      >
        ×
      </button>
    </div>
  ) : null;

  if (showAddUser) {
    return (
      <>
        {ErrorBanner}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add New User</CardTitle>
            <CardDescription>Create a new user profile</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Wilson Rodrigues"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                disabled={isCreating}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email (optional)</Label>
              <Input
                id="email"
                type="email"
                placeholder="email@example.com"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                disabled={isCreating}
              />
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={handleAddUser} 
                disabled={!newUserName.trim() || isCreating}
              >
                {isCreating ? 'Creating...' : 'Create User'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAddUser(false);
                  setError(null);
                }}
                disabled={isCreating}
              >
                Cancel
              </Button>
            </div>
            {isCreating && (
              <p className="text-sm text-muted-foreground">
                Creating user, please wait...
              </p>
            )}
          </CardContent>
        </Card>
      </>
    );
  }

  if (showSettings && currentUser) {
    return (
      <>
        {ErrorBanner}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>User Settings - {currentUser.name}</CardTitle>
            <CardDescription>Configure lesson plan folder location</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="basePath">Lesson Plan Folder Path</Label>
              <Input
                id="basePath"
                placeholder="e.g., F:\rodri\Documents\OneDrive\AS\Lesson Plan"
                value={basePath}
                onChange={(e) => setBasePath(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                This is where your lesson plan files are stored (e.g., 25 W41 folder)
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleUpdateBasePath} disabled={!basePath.trim()}>
                <FolderOpen className="w-4 h-4 mr-2" />
                Save Path
              </Button>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowSettings(false);
                  setError(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <>
      {ErrorBanner}
      <div className="space-y-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 flex-1">
            <User className="w-5 h-5 text-muted-foreground" />
            <Select
              value={currentUser?.id || ''}
              onChange={(e) => selectUser(e.target.value)}
              disabled={isLoading}
              className="flex-1"
            >
              <option value="">
                {isLoading ? 'Loading users...' : 'Select User...'}
              </option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name}
                </option>
              ))}
            </Select>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              console.log('[UserSelector] Add User button clicked');
              setShowAddUser(true);
              setError(null);
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add User
          </Button>
          {currentUser && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowSettings(true);
                setError(null);
              }}
            >
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          )}
        </div>
        
        {currentUser && currentUser.base_path_override && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-2 rounded">
            <FolderOpen className="w-4 h-4" />
            <span className="flex-1 truncate">{currentUser.base_path_override}</span>
          </div>
        )}
        
        {isLoading && (
          <div className="text-sm text-muted-foreground text-center py-2">
            Loading users...
          </div>
        )}
        
        {!isLoading && users.length === 0 && (
          <div className="text-sm text-muted-foreground text-center py-4 bg-muted/50 rounded">
            No users found. Click "Add User" to create one.
          </div>
        )}
      </div>
    </>
  );
};
