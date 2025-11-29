package com.bilingual.lessonplanner.domain.repository

import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.User
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import kotlinx.coroutines.flow.Flow

interface PlanRepository {
    // Weekly Plans
    fun getPlans(userId: String): Flow<List<WeeklyPlan>>
    suspend fun getPlanById(planId: String): WeeklyPlan?
    suspend fun getPlanDetail(planId: String, userId: String): WeeklyPlan?
    
    // Lesson Steps
    fun getLessonSteps(planId: String, dayOfWeek: String?, slotNumber: Int?): Flow<List<LessonStep>>
    suspend fun getLessonStepById(stepId: String): LessonStep?
    
    // Schedule
    fun getSchedule(userId: String, dayOfWeek: String?): Flow<List<ScheduleEntry>>
    suspend fun getScheduleEntryById(entryId: String): ScheduleEntry?
    
    // Users
    fun getUsers(): Flow<List<User>>
    suspend fun getUserById(userId: String): User?
    
    // Sync
    suspend fun syncPlans(userId: String)
    suspend fun syncLessonSteps(planId: String)
    suspend fun syncSchedule(userId: String)
    suspend fun syncUsers()
}

