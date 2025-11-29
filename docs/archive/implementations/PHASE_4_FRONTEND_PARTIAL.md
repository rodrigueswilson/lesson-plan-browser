# Phase 4 Partial: Frontend Updates Started

**Date:** October 26, 2025  
**Status:** 🔄 IN PROGRESS  
**Completed:** API client + UserSelector component

---

## What's Been Done

### 1. API Client (`frontend/src/lib/api.ts`) ✅

**Updated Types:**
```typescript
export interface User {
  id: string;
  name: string;  // Computed for backward compatibility
  first_name: string;
  last_name: string;
  email?: string;
  base_path_override?: string;
  created_at: string;
  updated_at: string;
}

export interface ClassSlot {
  // ... existing fields ...
  primary_teacher_name?: string;  // Computed
  primary_teacher_first_name?: string;
  primary_teacher_last_name?: string;
  // ... other fields ...
}
```

**Updated Methods:**
```typescript
// userApi.create - now requires firstName/lastName
create: (firstName: string, lastName: string, email?: string) => 
  request<User>('POST', `${API_BASE_URL}/users`, { 
    first_name: firstName, 
    last_name: lastName, 
    email 
  }),

// userApi.update - now accepts structured fields
update: (userId: string, data: { 
  first_name?: string; 
  last_name?: string; 
  email?: string 
}) =>
  request<User>('PUT', `${API_BASE_URL}/users/${userId}`, data),
```

---

### 2. Utility Functions (`frontend/src/utils/formatters.ts`) ✅

**Created new file with:**

```typescript
// Build teacher name as "Primary First Last / Bilingual First Last"
export function buildTeacherName(
  primaryFirst: string,
  primaryLast: string,
  bilingualFirst: string,
  bilingualLast: string
): string

// Format week dates to MM/DD-MM/DD
export function formatWeekDates(weekOf: string): string
```

---

### 3. UserSelector Component (`frontend/src/components/UserSelector.tsx`) ✅

**State Variables Updated:**
```typescript
// Before:
const [newUserName, setNewUserName] = useState('');

// After:
const [newUserFirstName, setNewUserFirstName] = useState('');
const [newUserLastName, setNewUserLastName] = useState('');
```

**Validation Updated:**
```typescript
// Before:
if (!newUserName.trim()) {
  alert('Please enter a name');
  return;
}

// After:
if (!newUserFirstName.trim()) {
  alert('Please enter a first name');
  return;
}
if (!newUserLastName.trim()) {
  alert('Please enter a last name');
  return;
}
```

**API Call Updated:**
```typescript
// Before:
const response = await userApi.create(newUserName, newUserEmail || undefined);

// After:
const response = await userApi.create(
  newUserFirstName, 
  newUserLastName, 
  newUserEmail || undefined
);
```

**UI Updated:**
```tsx
{/* Before: Single name field */}
<Label htmlFor="name">Name *</Label>
<Input
  id="name"
  placeholder="e.g., Wilson Rodrigues"
  value={newUserName}
  onChange={(e) => setNewUserName(e.target.value)}
/>

{/* After: Separate first/last name fields */}
<Label htmlFor="firstName">First Name *</Label>
<Input
  id="firstName"
  placeholder="e.g., Wilson"
  value={newUserFirstName}
  onChange={(e) => setNewUserFirstName(e.target.value)}
/>

<Label htmlFor="lastName">Last Name *</Label>
<Input
  id="lastName"
  placeholder="e.g., Rodrigues"
  value={newUserLastName}
  onChange={(e) => setNewUserLastName(e.target.value)}
/>
```

---

## What's Still Needed

### 4. SlotConfigurator Component ⏳

**Needs:**
- Add `primaryTeacherFirstName` and `primaryTeacherLastName` state
- Add input fields for teacher first/last names
- Update API calls to pass teacher names
- Show preview: "Primary First Last"

### 5. Display Components ⏳

**Needs:**
- Use `buildTeacherName()` utility to show combined names
- Display as: "Primary First Last / Bilingual First Last"
- Use `formatWeekDates()` for consistent date formatting

### 6. Migration Warning ⏳

**Needs:**
- Check if `user.first_name` or `user.last_name` is empty
- Show warning banner if incomplete
- Prompt user to update profile

---

## Files Modified So Far

1. ✅ `frontend/src/lib/api.ts` - Types and methods updated
2. ✅ `frontend/src/utils/formatters.ts` - NEW file created
3. ✅ `frontend/src/components/UserSelector.tsx` - User creation updated

---

## Files Still To Modify

4. ⏳ `frontend/src/components/SlotConfigurator.tsx` - Add teacher name fields
5. ⏳ `frontend/src/components/BatchProcessor.tsx` - Use formatWeekDates()
6. ⏳ `frontend/src/components/PlanHistory.tsx` - Display formatted dates

---

## Testing Status

### What Can Be Tested Now ✅
- User creation with first/last name
- API client types match backend

### What Can't Be Tested Yet ⏳
- Slot configuration with teacher names
- Display of combined teacher names
- Week date formatting in UI

---

## Next Steps

1. Update `SlotConfigurator.tsx` to add teacher name fields
2. Add migration warning to `UserSelector.tsx`
3. Update display components to use utility functions
4. Test end-to-end with backend running

---

## Summary

**Phase 4 Status:** 🔄 IN PROGRESS (40% complete)

**Completed:**
- ✅ API client updated
- ✅ Utility functions created
- ✅ UserSelector updated

**Remaining:**
- ⏳ SlotConfigurator
- ⏳ Display components
- ⏳ Migration warning
- ⏳ End-to-end testing

**Time So Far:** ~45 minutes

**Estimated Remaining:** ~30 minutes

---

Would you like me to continue with the remaining components?
