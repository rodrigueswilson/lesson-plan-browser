package com.bilingual.lessonplanner.ui.lessonmode

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.LessonSession
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.LessonJsonParser
import com.bilingual.lessonplanner.utils.LessonStepRecalculation
import com.bilingual.lessonplanner.utils.RecalculatedStep
import com.bilingual.lessonplanner.utils.TimerAdjustment
import com.bilingual.lessonplanner.utils.Logger
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class LessonModeUiState(
    val session: LessonSession? = null,
    val steps: List<LessonStep> = emptyList(),
    val adjustedSteps: List<RecalculatedStep> = emptyList(),
    val currentStep: LessonStep? = null,
    val nextStep: LessonStep? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class LessonModeViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(LessonModeUiState(isLoading = true))
    val uiState: StateFlow<LessonModeUiState> = _uiState.asStateFlow()

    private var timerJob: Job? = null

    fun initializeSession(planId: String, dayOfWeek: String, slotNumber: Int) {
        if (_uiState.value.session != null) return // Already initialized

        viewModelScope.launch {
            try {
                // Try to get plan and parse lesson_json first
                val plan = repository.getPlanById(planId)
                val lessonJsonData = plan?.lessonJson?.let { LessonJsonParser.parse(it) }
                val slotData = LessonJsonParser.getSlotData(lessonJsonData, dayOfWeek, slotNumber)
                
                // Get steps - prefer lesson_json if available, otherwise fallback to lesson_steps table
                val steps = if (slotData != null && !slotData.instruction_steps.isNullOrEmpty()) {
                    // Convert instruction_steps from lesson_json to LessonStep objects
                    LessonJsonParser.convertToLessonSteps(slotData, planId, dayOfWeek, slotNumber)
                        .sortedBy { it.stepNumber }
                } else {
                    // Fallback to lesson_steps table
                    repository.getLessonSteps(planId, dayOfWeek, slotNumber).first()
                        .sortedBy { it.stepNumber }
                }
                
                if (steps.isEmpty()) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false, 
                        error = "No steps found for this lesson."
                    )
                    return@launch
                }

                // Initialize adjusted steps
                val initialAdjustedSteps = steps.map { step ->
                    RecalculatedStep(
                        step = step,
                        adjustedDurationSeconds = step.durationMinutes * 60L,
                        originalDurationSeconds = step.durationMinutes * 60L
                    )
                }

                val session = LessonSession(
                    sessionId = UUID.randomUUID().toString(),
                    planId = planId,
                    dayOfWeek = dayOfWeek,
                    slotNumber = slotNumber,
                    startTime = System.currentTimeMillis()
                )

                _uiState.value = LessonModeUiState(
                    session = session,
                    steps = steps,
                    adjustedSteps = initialAdjustedSteps,
                    currentStep = steps.firstOrNull(),
                    nextStep = steps.getOrNull(1),
                    isLoading = false
                )
                
                // Start paused
            } catch (e: Exception) {
                Logger.e("Failed to initialize lesson session", e)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    fun toggleTimer() {
        val currentSession = _uiState.value.session ?: return
        
        if (currentSession.isPaused) {
            startTimer()
        } else {
            pauseTimer()
        }
    }

    private fun startTimer() {
        val currentSession = _uiState.value.session ?: return
        if (!currentSession.isPaused) return

        _uiState.value = _uiState.value.copy(
            session = currentSession.copy(isPaused = false)
        )

        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            while (isActive) {
                delay(1000L)
                val session = _uiState.value.session ?: break
                if (session.isPaused) break
                
                _uiState.value = _uiState.value.copy(
                    session = session.copy(
                        elapsedSeconds = session.elapsedSeconds + 1,
                        stepElapsedSeconds = session.stepElapsedSeconds + 1
                    )
                )
            }
        }
    }

    private fun pauseTimer() {
        val currentSession = _uiState.value.session ?: return
        _uiState.value = _uiState.value.copy(
            session = currentSession.copy(isPaused = true)
        )
        timerJob?.cancel()
    }
    
    fun resetStepTimer() {
        _uiState.value.session?.let { session ->
            _uiState.value = _uiState.value.copy(
                session = session.copy(stepElapsedSeconds = 0L)
            )
        }
    }

    fun handleTimerAdjust(adjustment: TimerAdjustment) {
        val currentState = _uiState.value
        val steps = currentState.adjustedSteps.ifEmpty { return }
        val currentStepIndex = currentState.session?.currentStepIndex ?: return
        
        val recalculated = LessonStepRecalculation.recalculateStepDurations(steps, currentStepIndex, adjustment)
        
        // Update LessonStep list for UI display
        val updatedLessonSteps = recalculated.map { it.toLessonStep() }
        
        // Update state
        _uiState.value = currentState.copy(
            adjustedSteps = recalculated,
            steps = updatedLessonSteps,
            currentStep = updatedLessonSteps.getOrNull(currentStepIndex),
            nextStep = updatedLessonSteps.getOrNull(currentStepIndex + 1)
        )
        
        if (adjustment is TimerAdjustment.Skip) {
             jumpToStep(adjustment.targetStepIndex)
        } else if (adjustment is TimerAdjustment.Reset) {
             resetStepTimer()
        }
    }

    fun jumpToStep(index: Int) {
        val currentState = _uiState.value
        val session = currentState.session ?: return
        val steps = currentState.steps // Uses updated steps
        
        if (index in steps.indices) {
            val completedIds = steps.take(index).map { it.id }.toSet()
            
            _uiState.value = currentState.copy(
                session = session.copy(
                    currentStepIndex = index,
                    stepElapsedSeconds = 0L, 
                    completedStepIds = completedIds
                ),
                currentStep = steps.getOrNull(index),
                nextStep = steps.getOrNull(index + 1)
            )
        }
    }

    fun nextStep() {
        val currentState = _uiState.value
        val session = currentState.session ?: return
        
        if (session.currentStepIndex < currentState.steps.lastIndex) {
            jumpToStep(session.currentStepIndex + 1)
        }
    }

    fun previousStep() {
        val currentState = _uiState.value
        val session = currentState.session ?: return
        
        if (session.currentStepIndex > 0) {
            jumpToStep(session.currentStepIndex - 1)
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        timerJob?.cancel()
    }
}
