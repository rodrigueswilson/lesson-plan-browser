package com.bilingual.lessonplanner.ui.browser

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.Logger
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import javax.inject.Inject

@HiltViewModel
class BrowserViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(BrowserUiState())
    val uiState: StateFlow<BrowserUiState> = _uiState.asStateFlow()
    
    private val _availableWeeks = MutableStateFlow<List<String>>(emptyList())
    val availableWeeks: StateFlow<List<String>> = _availableWeeks.asStateFlow()
    
    init {
        loadAvailableWeeks()
    }
    
    private fun loadAvailableWeeks() {
        viewModelScope.launch {
            // This will be populated when we have a userId
            // For now, we'll load it when needed
        }
    }
    
    fun loadWeeksForUser(userId: String) {
        viewModelScope.launch {
            try {
                val plans = repository.getPlans(userId).first()
                val weeks = plans
                    .mapNotNull { it.weekOf }
                    .distinct()
                    .sortedDescending()
                _availableWeeks.value = weeks
                
                // Auto-select first week if none selected
                if (_uiState.value.selectedWeek == null && weeks.isNotEmpty()) {
                    _uiState.value = _uiState.value.copy(selectedWeek = weeks.first())
                }
            } catch (e: Exception) {
                Logger.e("Failed to load weeks for user: $userId", e)
                _uiState.value = _uiState.value.copy(
                    error = "Failed to load weeks: ${e.message ?: "Unknown error"}"
                )
            }
        }
    }
    
    fun setViewMode(mode: ViewMode) {
        _uiState.value = _uiState.value.copy(currentViewMode = mode)
    }
    
    fun setSelectedWeek(week: String) {
        _uiState.value = _uiState.value.copy(selectedWeek = week)
    }
    
    fun setSelectedDay(day: String) {
        _uiState.value = _uiState.value.copy(selectedDay = day)
    }
    
    fun setSelectedLesson(lessonId: String) {
        _uiState.value = _uiState.value.copy(selectedLessonId = lessonId)
    }
    
    fun refresh(userId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                repository.syncPlans(userId)
                repository.syncSchedule(userId)
                loadWeeksForUser(userId)
                _uiState.value = _uiState.value.copy(isLoading = false, error = null)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }
    
    fun jumpToToday() {
        // Get Monday of current week
        val today = LocalDate.now()
        val mondayOfThisWeek = today.with(DayOfWeek.MONDAY)
        val weekOfFormatted = mondayOfThisWeek.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"))
        
        // Check if this week exists in available weeks
        val availableWeeks = _availableWeeks.value
        val matchingWeek = availableWeeks.find { it == weekOfFormatted || it.startsWith(weekOfFormatted) }
        
        if (matchingWeek != null) {
            _uiState.value = _uiState.value.copy(selectedWeek = matchingWeek)
        } else {
            // If current week not found, select the closest week (newest)
            if (availableWeeks.isNotEmpty()) {
                _uiState.value = _uiState.value.copy(selectedWeek = availableWeeks.first())
            }
        }
    }
    
    fun getCurrentWeekString(): String {
        val today = LocalDate.now()
        val mondayOfThisWeek = today.with(DayOfWeek.MONDAY)
        return mondayOfThisWeek.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"))
    }
}

