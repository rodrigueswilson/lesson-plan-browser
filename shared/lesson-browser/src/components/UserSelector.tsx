// Improved UserSelector with better error handling and debugging
// Replace the content of frontend/src/components/UserSelector.tsx with this

import React, { useEffect, useState, useRef } from 'react';
import { User, Plus, FolderOpen, Settings, AlertCircle } from 'lucide-react';
import { useStore } from '../store/useStore';
import { userApi, slotApi, planApi } from '@lesson-api';
import { Button } from '@lesson-ui/Button';
import { Select } from '@lesson-ui/Select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@lesson-ui/Card';
import { Input } from '@lesson-ui/Input';
import { Label } from '@lesson-ui/Label';

type UserSelectorProps = {
  /**
   * Auto-selection behavior.
   * - 'single': if there is exactly one user, select it
   * - 'first': if there is at least one user, select the first (useful for tablets assigned to one user)
   * - 'off': never auto-select
   *
   * This is primarily intended for tablet builds where each tablet is assigned
   * to one teacher/user.
   */
  autoSelect?: 'off' | 'single' | 'first';
};

export const UserSelector: React.FC<UserSelectorProps> = ({ autoSelect = 'off' }) => {
  const { currentUser, setCurrentUser, users, setUsers, slots, setSlots, plans, setPlans } = useStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUser, setIsLoadingUser] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [newUserFirstName, setNewUserFirstName] = useState('');
  const [newUserLastName, setNewUserLastName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [basePath, setBasePath] = useState('');
  const [templatePath, setTemplatePath] = useState('');
  const [signatureImagePath, setSignatureImagePath] = useState('');
  const [error, setError] = useState<string | null>(null);
  const selectUserTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isSelectingRef = useRef(false);
  const autoSelectedRef = useRef(false);

  useEffect(() => {
    console.log('[UserSelector] Component mounted, loading users...');
    loadUsers();
    
    // Cleanup timeout on unmount
    return () => {
      if (selectUserTimeoutRef.current) {
        clearTimeout(selectUserTimeoutRef.current);
      }
    };
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
      
      // Keep waiting for explicit user selection when multiple profiles exist.
      // Previously the first user was auto-selected, which prevented the picker
      // from showing on Android builds. Now we simply populate the dropdown.
    } catch (error: any) {
      console.error('[UserSelector] Failed to load users:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to load users: ${errorMsg}`);
      
      // Show alert for critical error
      const userAgent = navigator.userAgent || '';
      const isAndroid = userAgent.includes('Android');
      const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
      
      let errorMessage = `Cannot load users!\n\nError: ${errorMsg}`;
      if (isAndroid && isTauri) {
        errorMessage += '\n\nYou are in standalone mode. Make sure the local database is initialized and accessible.';
      } else {
        errorMessage += '\n\nMake sure the backend is running on http://localhost:8000';
      }
      alert(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const selectUser = async (userId: string, forceReload: boolean = false) => {
    console.log('[UserSelector] Selecting user:', userId, 'forceReload:', forceReload);
    setError(null);
    
    // If empty string, clear selection (user selected "Select User...")
    if (!userId || userId.trim() === '') {
      console.log('[UserSelector] Clearing user selection');
      setCurrentUser(null);
      setSlots([]);
      setPlans([]);
      setBasePath('');
      return;
    }
    
    // Check if user is already selected and data is cached
    if (!forceReload && currentUser?.id === userId && slots.length > 0 && plans.length > 0) {
      console.log('[UserSelector] User already selected with cached data, skipping API calls');
      // Update local state from cached user data
      setBasePath(currentUser.base_path_override || '');
      setTemplatePath(currentUser.template_path || '');
      setSignatureImagePath(currentUser.signature_image_path || '');
      return;
    }
    
    // Prevent concurrent calls
    if (isSelectingRef.current) {
      console.log('[UserSelector] Selection already in progress, skipping');
      return;
    }
    
    // Clear any pending timeout
    if (selectUserTimeoutRef.current) {
      clearTimeout(selectUserTimeoutRef.current);
      selectUserTimeoutRef.current = null;
    }
    
    // Debounce rapid selections
    return new Promise<void>((resolve) => {
      selectUserTimeoutRef.current = setTimeout(async () => {
        isSelectingRef.current = true;
        setIsLoadingUser(true);
        
        try {
          // Check again if user is already selected (race condition protection)
          if (!forceReload && currentUser?.id === userId && slots.length > 0 && plans.length > 0) {
            console.log('[UserSelector] User data already loaded during debounce, skipping');
            setBasePath(currentUser.base_path_override || '');
            setTemplatePath(currentUser.template_path || '');
            setSignatureImagePath(currentUser.signature_image_path || '');
            isSelectingRef.current = false;
            setIsLoadingUser(false);
            resolve();
            return;
          }
          
          console.log('[UserSelector] Fetching user data from API...');
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
          setTemplatePath(userResponse.data.template_path || '');
          setSignatureImagePath(userResponse.data.signature_image_path || '');
        } catch (error: any) {
          console.error('[UserSelector] Failed to select user:', error);
          const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
          setError(`Failed to load user data: ${errorMsg}`);
        } finally {
          isSelectingRef.current = false;
          setIsLoadingUser(false);
          resolve();
        }
      }, 300); // 300ms debounce
    });
  };

  useEffect(() => {
    if (autoSelect === 'off') return;
    if (autoSelectedRef.current) return;
    if (currentUser) return;
    if (autoSelect === 'single' && users.length !== 1) return;
    if (autoSelect === 'first' && users.length < 1) return;

    autoSelectedRef.current = true;
    if (autoSelect === 'first' && users.length > 1) {
      console.warn(
        `[UserSelector] autoSelect=first: multiple users found (${users.length}). ` +
        `Auto-selecting first user: ${users[0].id}. Tablet DB should normally contain exactly one user.`
      );
    } else {
      console.log('[UserSelector] autoSelect enabled; selecting user:', users[0].id);
    }
    // Fire and forget; selectUser handles its own loading states.
    void selectUser(users[0].id);
  }, [autoSelect, currentUser, users]);  

  const handleUpdateBasePath = async () => {
    if (!currentUser) return;
    
    console.log('[UserSelector] Updating base path:', basePath);
    setError(null);
    
    try {
      await userApi.updateBasePath(currentUser.id, basePath);
      setShowSettings(false);
      // Reload user to get updated data (force reload)
      await selectUser(currentUser.id, true);
      alert('Base path updated successfully!');
    } catch (error: any) {
      console.error('[UserSelector] Failed to update base path:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to update path: ${errorMsg}`);
      alert(`Failed to update path: ${errorMsg}`);
    }
  };

  const handleUpdateTemplatePaths = async () => {
    if (!currentUser) return;
    
    console.log('[UserSelector] Updating template paths:', { templatePath, signatureImagePath });
    setError(null);
    
    try {
      await userApi.updateTemplatePaths(
        currentUser.id,
        templatePath.trim() || undefined,
        signatureImagePath.trim() || undefined
      );
      setShowSettings(false);
      // Reload user to get updated data (force reload)
      await selectUser(currentUser.id, true);
      alert('Template paths updated successfully!');
    } catch (error: any) {
      console.error('[UserSelector] Failed to update template paths:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setError(`Failed to update template paths: ${errorMsg}`);
      alert(`Failed to update template paths: ${errorMsg}`);
    }
  };

  const handleAddUser = async () => {
    if (!newUserFirstName.trim()) {
      alert('Please enter a first name');
      return;
    }
    if (!newUserLastName.trim()) {
      alert('Please enter a last name');
      return;
    }
    
    console.log('[UserSelector] Creating user:', { 
      firstName: newUserFirstName, 
      lastName: newUserLastName, 
      email: newUserEmail 
    });
    setIsCreating(true);
    setError(null);
    
    try {
      console.log('[UserSelector] Sending create user request...');
      const response = await userApi.create(
        newUserFirstName, 
        newUserLastName, 
        newUserEmail || undefined
      );
      console.log('[UserSelector] User created successfully:', response.data);
      
      // Reload users list
      await loadUsers();
      
      // Select the newly created user
      await selectUser(response.data.id);
      
      // Reset form
      setShowAddUser(false);
      setNewUserFirstName('');
      setNewUserLastName('');
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
              <Label htmlFor="firstName">First Name *</Label>
              <Input
                id="firstName"
                placeholder="e.g., Wilson"
                value={newUserFirstName}
                onChange={(e) => setNewUserFirstName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                disabled={isCreating}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name *</Label>
              <Input
                id="lastName"
                placeholder="e.g., Rodrigues"
                value={newUserLastName}
                onChange={(e) => setNewUserLastName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddUser()}
                disabled={isCreating}
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
                disabled={!newUserFirstName.trim() || !newUserLastName.trim() || isCreating}
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
            <CardDescription>Configure lesson plan folder location and template paths</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
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
                <Button onClick={handleUpdateBasePath}>
                  <FolderOpen className="w-4 h-4 mr-2" />
                  Save Folder Path
                </Button>
              </div>
            </div>

            <div className="border-t pt-4 space-y-4">
              <h3 className="text-sm font-medium">Template Configuration</h3>
              <div className="space-y-2">
                <Label htmlFor="templatePath">Lesson Plan Template Path (Optional)</Label>
                <Input
                  id="templatePath"
                  placeholder="e.g., input/Lesson Plan Template SY'25-26.docx"
                  value={templatePath}
                  onChange={(e) => setTemplatePath(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Path to your custom lesson plan template. Leave empty to use default template.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="signatureImagePath">Signature Image Path (Optional)</Label>
                <Input
                  id="signatureImagePath"
                  placeholder="e.g., F:\path\to\signature.PNG"
                  value={signatureImagePath}
                  onChange={(e) => setSignatureImagePath(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Path to your signature image file. Leave empty to not include signature image in lesson plans.
                </p>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleUpdateTemplatePaths}>
                  Save Template Paths
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
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  // Migration warning banner
  const needsNameUpdate = currentUser && (!currentUser.first_name || !currentUser.last_name);
  const MigrationWarning = needsNameUpdate ? (
    <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm font-medium text-yellow-900">Profile Update Required</p>
        <p className="text-sm text-yellow-700">
          Please update your profile with your first and last name for proper lesson plan formatting.
        </p>
      </div>
      <Button
        size="sm"
        variant="outline"
        onClick={() => setShowSettings(true)}
        className="text-yellow-700 border-yellow-300 hover:bg-yellow-100"
      >
        Update Profile
      </Button>
    </div>
  ) : null;

  return (
    <>
      {ErrorBanner}
      {MigrationWarning}
      <div className="space-y-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 flex-1">
            <User className="w-5 h-5 text-muted-foreground" />
            <Select
              id="user-selector"
              name="user-selector"
              value={currentUser?.id || ''}
              onChange={(e) => selectUser(e.target.value)}
              disabled={isLoading || isLoadingUser}
              className="flex-1"
            >
              <option value="">
                {isLoading ? 'Loading users...' : isLoadingUser ? 'Loading user data...' : 'Select User...'}
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
        
        {(isLoading || isLoadingUser) && (
          <div className="text-sm text-muted-foreground text-center py-2">
            {isLoading ? 'Loading users...' : 'Loading user data...'}
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
