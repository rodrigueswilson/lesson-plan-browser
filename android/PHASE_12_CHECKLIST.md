# Phase 12: Optimization & Testing Checklist

## Configuration Tasks

- [ ] **Configure Supabase Credentials**
  - [ ] Update `SupabaseConfigProvider.getConfig()` with project1 URL and key
  - [ ] Update `SupabaseConfigProvider.getConfig()` with project2 URL and key
  - [ ] Test Supabase connection

## Testing Tasks

### Unit Tests
- [ ] Write unit tests for `BrowserViewModel`
- [ ] Write unit tests for `DayViewModel`
- [ ] Write unit tests for `WeekViewModel`
- [ ] Write unit tests for `LessonDetailViewModel`
- [ ] Write unit tests for `UserSelectorViewModel`
- [ ] Write unit tests for `LocalPlanRepository`
- [ ] Write unit tests for `RemotePlanRepository`
- [ ] Write unit tests for `SyncManager`
- [ ] Write unit tests for data mappers

### Integration Tests
- [ ] Test Room database operations
- [ ] Test Supabase API calls
- [ ] Test sync functionality (WiFi vs Mobile)
- [ ] Test offline functionality
- [ ] Test data persistence

### UI Tests
- [ ] Test user selection flow
- [ ] Test navigation between screens
- [ ] Test week view display
- [ ] Test day view display
- [ ] Test lesson detail view
- [ ] Test refresh functionality

### Manual Testing
- [ ] Test on Android tablet (10" recommended)
- [ ] Test on Android phone (7"+ in landscape)
- [ ] Test offline mode
- [ ] Test sync on WiFi
- [ ] Test sync on mobile data
- [ ] Test app startup and user selection
- [ ] Test navigation flows
- [ ] Test error handling

## Performance Optimization

- [ ] **Database Query Optimization**
  - [ ] Review and optimize Room queries
  - [ ] Add database indices if needed
  - [ ] Optimize Flow collections

- [ ] **UI Performance**
  - [ ] Optimize Compose recomposition
  - [ ] Add list virtualization where needed
  - [ ] Optimize image loading (if images added)

- [ ] **Memory Management**
  - [ ] Review memory leaks
  - [ ] Optimize ViewModel lifecycle
  - [ ] Review Flow subscriptions

- [ ] **Battery Optimization**
  - [ ] Review background sync frequency
  - [ ] Optimize WorkManager constraints
  - [ ] Review network request patterns

## Bug Fixes & Edge Cases

- [ ] **Plan ID Resolution**
  - [ ] Implement proper plan ID resolution from schedule entries
  - [ ] Handle cases where plan doesn't exist
  - [ ] Handle multiple plans per week

- [ ] **Error Handling**
  - [ ] Improve error messages for users
  - [ ] Handle network errors gracefully
  - [ ] Handle database errors
  - [ ] Handle Supabase API errors

- [ ] **Edge Cases**
  - [ ] Handle empty lesson lists
  - [ ] Handle missing lesson data
  - [ ] Handle invalid JSON in lesson steps
  - [ ] Handle user switching
  - [ ] Handle app backgrounding/foregrounding

## UI/UX Improvements

- [ ] **Loading States**
  - [ ] Add skeleton loaders for lists
  - [ ] Improve loading indicators
  - [ ] Add pull-to-refresh

- [ ] **Week Selection**
  - [ ] Add week selector dropdown in BrowserScreen
  - [ ] Implement week navigation

- [ ] **Polish**
  - [ ] Improve spacing and padding
  - [ ] Add animations and transitions
  - [ ] Improve tablet layouts
  - [ ] Add accessibility improvements

## Documentation

- [ ] Update README with setup instructions
- [ ] Document API endpoints used
- [ ] Document data models
- [ ] Add code comments where needed

## Deployment Preparation

- [ ] **Build Configuration**
  - [ ] Set up release signing
  - [ ] Configure ProGuard rules
  - [ ] Set version numbers

- [ ] **Security**
  - [ ] Review API key storage
  - [ ] Review data encryption
  - [ ] Review network security

## Notes

- Most critical: Configure Supabase credentials and test basic functionality
- Plan ID resolution needs to be implemented based on actual data structure
- Week selection feature is not yet implemented in BrowserScreen
- Some error handling could be more user-friendly

