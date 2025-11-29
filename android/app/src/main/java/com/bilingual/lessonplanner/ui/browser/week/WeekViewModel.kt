package com.bilingual.lessonplanner.ui.browser.week

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import javax.inject.Inject

data class WeekViewUiState(
    val mondayLessons: List<ScheduleEntry> = emptyList(),
    val tuesdayLessons: List<ScheduleEntry> = emptyList(),
    val wednesdayLessons: List<ScheduleEntry> = emptyList(),
    val thursdayLessons: List<ScheduleEntry> = emptyList(),
    val fridayLessons: List<ScheduleEntry> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class WeekViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(WeekViewUiState(isLoading = true))
    val uiState: StateFlow<WeekViewUiState> = _uiState.asStateFlow()
    
    fun loadWeekSchedule(userId: String) {
        viewModelScope.launch {
            try {
                combine(
                    repository.getSchedule(userId, "Monday"),
                    repository.getSchedule(userId, "Tuesday"),
                    repository.getSchedule(userId, "Wednesday"),
                    repository.getSchedule(userId, "Thursday"),
                    repository.getSchedule(userId, "Friday")
                ) { monday, tuesday, wednesday, thursday, friday ->
                    WeekViewUiState(
                        // Return all active entries, View will handle class vs non-class distinction
                        mondayLessons = monday.filter { it.isActive },
                        tuesdayLessons = tuesday.filter { it.isActive },
                        wednesdayLessons = wednesday.filter { it.isActive },
                        thursdayLessons = thursday.filter { it.isActive },
                        fridayLessons = friday.filter { it.isActive },
                        isLoading = false,
                        error = null
                    )
                }.collect { state ->
                    _uiState.value = state
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }
}
