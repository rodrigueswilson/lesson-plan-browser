package com.bilingual.lessonplanner.ui.browser.day

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DayViewUiState(
    val lessons: List<ScheduleEntry> = emptyList(),
    val selectedDay: String = "monday",
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class DayViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(DayViewUiState())
    val uiState: StateFlow<DayViewUiState> = _uiState.asStateFlow()
    
    fun loadDaySchedule(userId: String, dayOfWeek: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                selectedDay = dayOfWeek
            )
            
            repository.getSchedule(userId, dayOfWeek)
                .map { entries ->
                    // Return all active entries, View will handle class vs non-class distinction
                    entries.filter { it.isActive }
                        .sortedBy { it.startTime }
                }
                .collect { lessons ->
                    _uiState.value = _uiState.value.copy(
                        lessons = lessons,
                        isLoading = false,
                        error = null
                    )
                }
        }
    }
}
