package com.bilingual.lessonplanner.data.local.repository

import com.bilingual.lessonplanner.data.local.database.AppDatabase
import com.bilingual.lessonplanner.data.local.database.dao.LessonStepDao
import com.bilingual.lessonplanner.data.local.database.dao.PlanDao
import com.bilingual.lessonplanner.data.local.database.dao.ScheduleDao
import com.bilingual.lessonplanner.data.local.database.dao.UserDao
import com.bilingual.lessonplanner.data.mapper.toDomain
import com.bilingual.lessonplanner.data.mapper.toEntity
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.User
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class LocalPlanRepository(
    private val database: AppDatabase
) : PlanRepository {
    
    private val planDao: PlanDao = database.planDao()
    private val lessonStepDao: LessonStepDao = database.lessonStepDao()
    private val scheduleDao: ScheduleDao = database.scheduleDao()
    private val userDao: UserDao = database.userDao()
    
    override fun getPlans(userId: String): Flow<List<WeeklyPlan>> {
        return planDao.getPlansByUserId(userId).map { entities ->
            entities.map { it.toDomain() }
        }
    }
    
    override suspend fun getPlanById(planId: String): WeeklyPlan? {
        return planDao.getPlanById(planId)?.toDomain()
    }
    
    override suspend fun getPlanDetail(planId: String, userId: String): WeeklyPlan? {
        return planDao.getPlanByIdAndUserId(planId, userId)?.toDomain()
    }
    
    override fun getLessonSteps(planId: String, dayOfWeek: String?, slotNumber: Int?): Flow<List<LessonStep>> {
        return when {
            dayOfWeek != null && slotNumber != null -> {
                lessonStepDao.getStepsByPlanIdDayAndSlot(planId, dayOfWeek, slotNumber)
                    .map { entities -> entities.map { it.toDomain() } }
            }
            dayOfWeek != null -> {
                lessonStepDao.getStepsByPlanIdAndDay(planId, dayOfWeek)
                    .map { entities -> entities.map { it.toDomain() } }
            }
            else -> {
                lessonStepDao.getStepsByPlanId(planId)
                    .map { entities -> entities.map { it.toDomain() } }
            }
        }
    }
    
    override suspend fun getLessonStepById(stepId: String): LessonStep? {
        return lessonStepDao.getStepById(stepId)?.toDomain()
    }
    
    override fun getSchedule(userId: String, dayOfWeek: String?): Flow<List<ScheduleEntry>> {
        return if (dayOfWeek != null) {
            scheduleDao.getScheduleByUserIdAndDay(userId, dayOfWeek)
                .map { entities -> entities.map { it.toDomain() } }
        } else {
            scheduleDao.getScheduleByUserId(userId)
                .map { entities -> entities.map { it.toDomain() } }
        }
    }
    
    override suspend fun getScheduleEntryById(entryId: String): ScheduleEntry? {
        return scheduleDao.getEntryById(entryId)?.toDomain()
    }
    
    override fun getUsers(): Flow<List<User>> {
        return userDao.getUsers().map { entities ->
            entities.map { it.toDomain() }
        }
    }
    
    override suspend fun getUserById(userId: String): User? {
        return userDao.getUserById(userId)?.toDomain()
    }
    
    override suspend fun syncPlans(userId: String) {
        // Sync logic will be implemented in Phase 4
    }
    
    override suspend fun syncLessonSteps(planId: String) {
        // Sync logic will be implemented in Phase 4
    }
    
    override suspend fun syncSchedule(userId: String) {
        // Sync logic will be implemented in Phase 4
    }
    
    override suspend fun syncUsers() {
        // Sync logic will be implemented in Phase 4
    }
    
    // Save methods for sync operations
    suspend fun savePlans(plans: List<WeeklyPlan>) {
        planDao.insertPlans(plans.map { it.toEntity() })
    }
    
    suspend fun saveLessonSteps(steps: List<LessonStep>) {
        lessonStepDao.insertSteps(steps.map { it.toEntity() })
    }
    
    suspend fun saveSchedule(entries: List<ScheduleEntry>) {
        scheduleDao.insertEntries(entries.map { it.toEntity() })
    }
    
    suspend fun saveUsers(users: List<User>) {
        userDao.insertUsers(users.map { it.toEntity() })
    }
}

