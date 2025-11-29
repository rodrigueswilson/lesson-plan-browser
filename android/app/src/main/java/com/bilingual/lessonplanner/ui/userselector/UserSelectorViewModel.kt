package com.bilingual.lessonplanner.ui.userselector

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.data.datastore.UserPreferences
import com.bilingual.lessonplanner.domain.model.User
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.Logger
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch
import javax.inject.Inject

data class UserSelectorUiState(
    val users: List<User> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class UserSelectorViewModel @Inject constructor(
    private val repository: PlanRepository,
    private val userPreferences: UserPreferences,
    private val syncManager: com.bilingual.lessonplanner.data.sync.SyncManager
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(UserSelectorUiState(isLoading = true))
    val uiState: StateFlow<UserSelectorUiState> = _uiState.asStateFlow()
    
    init {
        Log.d("UserSelectorVM", "ViewModel initialized")
        loadUsers()
    }
    
    private fun loadUsers() {
        viewModelScope.launch {
            Log.d("UserSelectorVM", "Starting loadUsers()")
            repository.getUsers()
                .catch { e ->
                    Log.e("UserSelectorVM", "Failed to load users", e)
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "Failed to load users"
                    )
                }
                .collect { users ->
                    Log.d("UserSelectorVM", "Loaded ${users.size} users")
                    _uiState.value = _uiState.value.copy(
                        users = users,
                        isLoading = false,
                        error = null
                    )
                    
                    if (users.isEmpty()) {
                        Log.d("UserSelectorVM", "No users found, triggering sync")
                        syncUsers()
                    }
                }
        }
    }
    
    fun syncUsers() {
        viewModelScope.launch {
            Log.d("UserSelectorVM", "Starting syncUsers()")
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                syncManager.syncUsers()
                Log.d("UserSelectorVM", "Sync completed successfully")
                // Users will be emitted by repository.getUsers() flow automatically
            } catch (e: Exception) {
                Log.e("UserSelectorVM", "Sync failed", e)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Sync failed: ${e.message}"
                )
            }
        }
    }
    
    fun selectUser(user: User) {
        viewModelScope.launch {
            try {
                userPreferences.setSelectedUserId(user.id)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = e.message)
            }
        }
    }
}
