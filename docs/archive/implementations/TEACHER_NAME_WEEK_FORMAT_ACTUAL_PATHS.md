# Actual Frontend Component Paths - Addendum

**Date:** October 26, 2025  
**Purpose:** Correct component paths for implementation

---

## Actual Frontend Structure

### Existing Components (Verified)

```
frontend/src/
├── App.tsx
├── main.tsx
├── components/
│   ├── Analytics.tsx
│   ├── BatchProcessor.tsx
│   ├── PlanHistory.tsx
│   ├── SlotConfigurator.tsx      ← Slot configuration UI
│   ├── UserSelector.tsx           ← User selection/creation UI
│   └── ui/
│       ├── Alert.tsx
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Dialog.tsx
│       ├── Input.tsx
│       ├── Label.tsx
│       ├── Progress.tsx
│       └── Select.tsx
├── lib/
│   └── api.ts                     ← API client
└── store/
    └── useStore.ts                ← State management
```

---

## Corrected Implementation Paths

### Phase 3: Frontend Updates

#### 3.1 User Registration/Creation

**File:** `frontend/src/components/UserSelector.tsx` (EXISTING)

**Current Implementation:**
```typescript
const handleAddUser = async () => {
  if (!newUserName.trim()) {
    alert('Please enter a name');
    return;
  }
  
  const response = await userApi.create(newUserName, newUserEmail || undefined);
  // ...
}
```

**Update Required:**
```typescript
// Add state for first/last name
const [newUserFirstName, setNewUserFirstName] = useState('');
const [newUserLastName, setNewUserLastName] = useState('');

const handleAddUser = async () => {
  // Validate first and last name
  if (!newUserFirstName.trim()) {
    alert('Please enter a first name');
    return;
  }
  if (!newUserLastName.trim()) {
    alert('Please enter a last name');
    return;
  }
  
  // Update API call
  const response = await userApi.create(
    newUserFirstName,
    newUserLastName,
    newUserEmail || undefined
  );
  // ...
}

// Update JSX to show two name fields instead of one
<div>
  <Label htmlFor="firstName">First Name *</Label>
  <Input
    id="firstName"
    value={newUserFirstName}
    onChange={(e) => setNewUserFirstName(e.target.value)}
    placeholder="e.g., Daniela"
    required
  />
</div>
<div>
  <Label htmlFor="lastName">Last Name *</Label>
  <Input
    id="lastName"
    value={newUserLastName}
    onChange={(e) => setNewUserLastName(e.target.value)}
    placeholder="e.g., Silva"
    required
  />
</div>
```

---

#### 3.2 Slot Configuration

**File:** `frontend/src/components/SlotConfigurator.tsx` (EXISTING)

**Update Required:**
- Add fields for `primary_teacher_first_name` and `primary_teacher_last_name`
- Show preview: "Primary First Last / User First Last"
- Update API calls to include new fields

---

#### 3.3 Migration Warning Banner

**File:** `frontend/src/components/UserSelector.tsx` (EXISTING)

**Add Warning Logic:**
```typescript
// In UserSelector component
const needsNameUpdate = currentUser && (!currentUser.first_name || !currentUser.last_name);

// Add warning banner in JSX
{needsNameUpdate && (
  <Alert variant="warning" className="mb-4">
    <AlertCircle className="h-4 w-4" />
    <div>
      <h4 className="font-semibold">Profile Update Required</h4>
      <p className="text-sm">
        Please update your profile with your first and last name for proper lesson plan formatting.
      </p>
      <Button
        size="sm"
        variant="outline"
        onClick={() => setShowSettings(true)}
        className="mt-2"
      >
        Update Profile
      </Button>
    </div>
  </Alert>
)}
```

---

#### 3.4 API Client Updates

**File:** `frontend/src/lib/api.ts` (EXISTING)

**Update User API:**
```typescript
export const userApi = {
  // Update create method
  create: async (firstName: string, lastName: string, email?: string) => {
    return axios.post('/api/users', {
      first_name: firstName,
      last_name: lastName,
      email
    });
  },
  
  // Update update method
  update: async (userId: string, data: {
    first_name?: string;
    last_name?: string;
    email?: string;
  }) => {
    return axios.put(`/api/users/${userId}`, data);
  },
  
  // ... other methods
};

export const slotApi = {
  // Update create/update methods
  create: async (userId: string, data: {
    // ... existing fields
    primary_teacher_first_name?: string;
    primary_teacher_last_name?: string;
  }) => {
    return axios.post(`/api/users/${userId}/slots`, data);
  },
  
  // ... other methods
};
```

---

#### 3.5 Type Definitions

**File:** `frontend/src/types/index.ts` (CREATE if doesn't exist)

```typescript
export interface User {
  id: string;
  name: string;  // Computed for backward compat
  first_name: string;
  last_name: string;
  email?: string;
  base_path_override?: string;
  created_at: string;
}

export interface ClassSlot {
  id: string;
  user_id: string;
  slot_number: number;
  subject: string;
  grade: string;
  homeroom?: string;
  primary_teacher_name?: string;  // Computed
  primary_teacher_first_name?: string;
  primary_teacher_last_name?: string;
  primary_teacher_file?: string;
  // ... other fields
}
```

---

#### 3.6 Utility Functions

**File:** `frontend/src/utils/formatters.ts` (CREATE)

```typescript
export function buildTeacherName(
  primaryFirst: string,
  primaryLast: string,
  bilingualFirst: string,
  bilingualLast: string
): string {
  const primary = `${primaryFirst} ${primaryLast}`.trim();
  const bilingual = `${bilingualFirst} ${bilingualLast}`.trim();
  
  if (primary && bilingual) {
    return `${primary} / ${bilingual}`;
  } else if (primary) {
    return primary;
  } else if (bilingual) {
    return bilingual;
  } else {
    return 'Unknown';
  }
}

export function formatWeekDates(weekOf: string): string {
  if (!weekOf) return '';
  
  // Remove common prefixes
  let cleaned = weekOf.replace(/Week of/i, '').trim();
  
  // Remove spaces and normalize
  cleaned = cleaned.replace(/\s+/g, '').replace(/to/i, '-');
  
  // Try to extract dates
  const datePattern = /(\d{1,2})[/-](\d{1,2})(?:[/-]\d{4})?/g;
  const matches = [...cleaned.matchAll(datePattern)];
  
  if (matches.length >= 2) {
    const [, startMonth, startDay] = matches[0];
    const [, endMonth, endDay] = matches[1];
    return `${startMonth}/${startDay}-${endMonth}/${endDay}`;
  }
  
  // Fallback: try "10-27-10-31" format
  const parts = cleaned.split('-');
  if (parts.length === 4) {
    return `${parts[0]}/${parts[1]}-${parts[2]}/${parts[3]}`;
  }
  
  return weekOf;
}
```

---

## Summary of Actual Files to Modify

### Frontend Files (Existing)
1. ✅ `frontend/src/components/UserSelector.tsx` - Add first/last name fields, warning banner
2. ✅ `frontend/src/components/SlotConfigurator.tsx` - Add primary teacher first/last fields
3. ✅ `frontend/src/lib/api.ts` - Update API methods

### Frontend Files (New)
4. ⭐ `frontend/src/types/index.ts` - Type definitions
5. ⭐ `frontend/src/utils/formatters.ts` - Utility functions

### Backend Files (From Original Plan)
6. ✅ `backend/database.py` - CRUD updates
7. ✅ `backend/models.py` - Request/response models
8. ✅ `backend/api.py` - Endpoint updates
9. ✅ `tools/batch_processor.py` - Metadata building
10. ⭐ `backend/migrations/add_structured_names.py` - Migration script
11. ⭐ `backend/utils/date_formatter.py` - Week formatter

---

## Implementation Order (Revised)

### Step 1: Backend Foundation
1. Create `backend/utils/date_formatter.py`
2. Update `backend/database.py` (schema + CRUD)
3. Create `backend/migrations/add_structured_names.py`
4. Run migration

### Step 2: Backend API
5. Update `backend/models.py`
6. Update `backend/api.py`
7. Update `tools/batch_processor.py`

### Step 3: Frontend Foundation
8. Create `frontend/src/types/index.ts`
9. Create `frontend/src/utils/formatters.ts`
10. Update `frontend/src/lib/api.ts`

### Step 4: Frontend UI
11. Update `frontend/src/components/UserSelector.tsx`
12. Update `frontend/src/components/SlotConfigurator.tsx`

### Step 5: Testing
13. Test user creation with first/last name
14. Test slot configuration with primary teacher name
15. Test lesson plan processing
16. Verify output format

---

## Key Differences from Original Plan

**Original Plan Said:**
- `frontend/src/components/UserProfile.tsx` ❌ (doesn't exist)
- `frontend/src/components/SlotConfiguration.tsx` ❌ (wrong name)
- `frontend/src/components/MigrationWarning.tsx` ❌ (not needed - add to UserSelector)

**Actual Implementation:**
- `frontend/src/components/UserSelector.tsx` ✅ (handles user creation + settings)
- `frontend/src/components/SlotConfigurator.tsx` ✅ (correct name)
- Warning banner added to `UserSelector.tsx` ✅ (no separate component needed)

---

## Ready to Implement

All paths are now verified and correct. The implementation can proceed with confidence that the files exist and are in the right locations.
