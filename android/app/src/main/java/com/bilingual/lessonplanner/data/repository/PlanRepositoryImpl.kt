package com.bilingual.lessonplanner.data.repository

import com.bilingual.lessonplanner.data.local.repository.LocalPlanRepository
import com.bilingual.lessonplanner.data.mapper.toEntity
import com.bilingual.lessonplanner.data.sync.SyncManager
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.User
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.Logger
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow

class PlanRepositoryImpl(
    private val localRepository: LocalPlanRepository,
    private val syncManager: SyncManager
) : PlanRepository {
    
    // UI always reads from local (offline-first)
    override fun getPlans(userId: String): Flow<List<WeeklyPlan>> {
        return localRepository.getPlans(userId)
            .catch { e ->
                Logger.w("Local read failed for plans, attempting sync", e)
                // If local read fails, try to sync (but don't block on it)
                try {
                    syncManager.syncPlans(userId)
                } catch (syncError: Exception) {
                    Logger.e("Sync also failed after local read failure", syncError)
                }
                throw e
            }
    }
    
    override suspend fun getPlanById(planId: String): WeeklyPlan? {
        return localRepository.getPlanById(planId)
    }
    
    override suspend fun getPlanDetail(planId: String, userId: String): WeeklyPlan? {
        return localRepository.getPlanDetail(planId, userId)
    }
    
    override fun getLessonSteps(planId: String, dayOfWeek: String?, slotNumber: Int?): Flow<List<LessonStep>> {
        return localRepository.getLessonSteps(planId, dayOfWeek, slotNumber)
            .catch { e ->
                syncManager.syncLessonSteps(planId)
                throw e
            }
    }
    
    override suspend fun getLessonStepById(stepId: String): LessonStep? {
        return localRepository.getLessonStepById(stepId)
    }
    
    override fun getSchedule(userId: String, dayOfWeek: String?): Flow<List<ScheduleEntry>> {
        return localRepository.getSchedule(userId, dayOfWeek)
            .catch { e ->
                syncManager.syncSchedule(userId)
                throw e
            }
    }
    
    override suspend fun getScheduleEntryById(entryId: String): ScheduleEntry? {
        return localRepository.getScheduleEntryById(entryId)
    }
    
    override fun getUsers(): Flow<List<User>> {
        return localRepository.getUsers()
            .catch { e ->
                syncManager.syncUsers()
                throw e
            }
    }
    
    override suspend fun getUserById(userId: String): User? {
        return localRepository.getUserById(userId)
    }
    
    // Sync methods trigger background sync
    override suspend fun syncPlans(userId: String) {
        syncManager.syncPlans(userId)
    }
    
    override suspend fun syncLessonSteps(planId: String) {
        syncManager.syncLessonSteps(planId)
    }
    
    override suspend fun syncSchedule(userId: String) {
        syncManager.syncSchedule(userId)
    }
    
    override suspend fun syncUsers() {
        syncManager.syncUsers()
    }
}

