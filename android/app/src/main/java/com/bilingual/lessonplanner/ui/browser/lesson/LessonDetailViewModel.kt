package com.bilingual.lessonplanner.ui.browser.lesson

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.LessonJsonData
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.SlotData
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.LessonJsonParser
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LessonDetailUiState(
    val plan: WeeklyPlan? = null,
    val steps: List<LessonStep> = emptyList(),
    val slotData: SlotData? = null, // Parsed data from lesson_json
    val lessonJsonData: LessonJsonData? = null, // Full parsed lesson_json
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class LessonDetailViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(LessonDetailUiState(isLoading = true))
    val uiState: StateFlow<LessonDetailUiState> = _uiState.asStateFlow()
    
    fun loadLessonDetail(planId: String, userId: String, dayOfWeek: String?, slotNumber: Int?) {
        viewModelScope.launch {
            try {
                val plan = repository.getPlanDetail(planId, userId)
                
                // Try to parse lesson_json first
                val lessonJsonData = plan?.lessonJson?.let { LessonJsonParser.parse(it) }
                val slotData = if (dayOfWeek != null && slotNumber != null) {
                    LessonJsonParser.getSlotData(lessonJsonData, dayOfWeek, slotNumber)
                } else {
                    null
                }
                
                // Get steps - prefer lesson_json if available, otherwise fallback to lesson_steps table
                if (slotData != null && !slotData.instruction_steps.isNullOrEmpty()) {
                    // Convert instruction_steps from lesson_json to LessonStep objects
                    val steps = LessonJsonParser.convertToLessonSteps(slotData, planId, dayOfWeek ?: "", slotNumber ?: 0)
                    
                    _uiState.value = LessonDetailUiState(
                        plan = plan,
                        steps = steps,
                        slotData = slotData,
                        lessonJsonData = lessonJsonData,
                        isLoading = false,
                        error = null
                    )
                } else {
                    // Fallback to lesson_steps table
                    repository.getLessonSteps(planId, dayOfWeek, slotNumber)
                        .collect { stepList ->
                            _uiState.value = LessonDetailUiState(
                                plan = plan,
                                steps = stepList,
                                slotData = slotData,
                                lessonJsonData = lessonJsonData,
                                isLoading = false,
                                error = null
                            )
                        }
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

