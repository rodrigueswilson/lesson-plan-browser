package com.bilingual.lessonplanner

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.PlanResolutionResult
import com.bilingual.lessonplanner.utils.resolvePlanIdFromScheduleEntry
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MainActivityViewModel @Inject constructor(
    val repository: PlanRepository
) : ViewModel() {
    
    suspend fun resolvePlanId(
        scheduleEntryId: String,
        userId: String,
        dayOfWeek: String,
        slotNumber: Int
    ): PlanResolutionResult? {
        return try {
            // Get the schedule entry
            val scheduleEntry = repository.getScheduleEntryById(scheduleEntryId)
            if (scheduleEntry == null) {
                // Create a temporary schedule entry for resolution
                val tempEntry = ScheduleEntry(
                    id = scheduleEntryId,
                    userId = userId,
                    dayOfWeek = dayOfWeek,
                    startTime = "",
                    endTime = "",
                    subject = "",
                    homeroom = null,
                    grade = null,
                    slotNumber = slotNumber,
                    planSlotGroupId = null,
                    isActive = true,
                    syncedAt = null
                )
                resolvePlanIdFromScheduleEntry(tempEntry, userId, repository)
            } else {
                resolvePlanIdFromScheduleEntry(scheduleEntry, userId, repository)
            }
        } catch (e: Exception) {
            null
        }
    }
}

