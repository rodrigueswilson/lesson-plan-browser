package com.bilingual.lessonplanner.ui.debug

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DataDiagnosticsViewModel @Inject constructor(
    private val repository: PlanRepository
) : ViewModel() {
    
    suspend fun getDiagnosticData(userId: String): DiagnosticData {
        return try {
            val users = repository.getUsers().first()
            val plans = repository.getPlans(userId).first()
            val schedule = repository.getSchedule(userId, null).first()
            
            val samplePlan = plans.firstOrNull()
            val steps = if (samplePlan != null) {
                try {
                    repository.getLessonSteps(samplePlan.id, null, null).first()
                } catch (e: Exception) {
                    android.util.Log.e("DataDiagnostics", "Error fetching steps for plan ${samplePlan.id}", e)
                    emptyList()
                }
            } else {
                emptyList()
            }
            
            DiagnosticData(
                userCount = users.size,
                planCount = plans.size,
                scheduleCount = schedule.size,
                stepCount = steps.size,
                samplePlan = samplePlan,
                sampleSteps = steps.take(3),
                sampleSchedule = schedule.take(3)
            )
        } catch (e: Exception) {
            android.util.Log.e("DataDiagnostics", "Error in getDiagnosticData for userId: $userId", e)
            throw e
        }
    }
}

data class DiagnosticData(
    val userCount: Int,
    val planCount: Int,
    val scheduleCount: Int,
    val stepCount: Int,
    val samplePlan: WeeklyPlan?,
    val sampleSteps: List<LessonStep>,
    val sampleSchedule: List<ScheduleEntry>
)

