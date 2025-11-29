package com.bilingual.lessonplanner.data.remote.repository

import com.bilingual.lessonplanner.data.remote.api.SupabaseApi
import com.bilingual.lessonplanner.data.remote.api.SupabaseApiException
import com.bilingual.lessonplanner.data.remote.config.SupabaseClientFactory
import com.bilingual.lessonplanner.data.remote.config.SupabaseConfig
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.User
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import com.bilingual.lessonplanner.utils.Logger
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class RemotePlanRepository(
    private val supabaseApi: SupabaseApi,
    private val supabaseConfig: SupabaseConfig
) : PlanRepository {
    
    override fun getPlans(userId: String): Flow<List<WeeklyPlan>> = flow {
        try {
            val client = SupabaseClientFactory.createClientForUser(userId, supabaseConfig)
            val api = SupabaseApi(client)
            val responses = api.getPlans(userId)
            emit(responses.map { it.toDomain() })
        } catch (e: SupabaseApiException) {
            throw e
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch plans", e)
        }
    }
    
    suspend fun getPlans(userId: String, updatedAfter: Long?): List<WeeklyPlan> {
        return try {
            val client = SupabaseClientFactory.createClientForUser(userId, supabaseConfig)
            val api = SupabaseApi(client)
            val responses = api.getPlans(userId, updatedAfter)
            responses.map { it.toDomain() }
        } catch (e: SupabaseApiException) {
            throw e
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch plans", e)
        }
    }
    
    override suspend fun getPlanById(planId: String): WeeklyPlan? {
        return try {
            supabaseApi.getPlanById(planId)?.toDomain()
        } catch (e: SupabaseApiException) {
            throw e
        }
    }
    
    override suspend fun getPlanDetail(planId: String, userId: String): WeeklyPlan? {
        return try {
            val client = SupabaseClientFactory.createClientForUser(userId, supabaseConfig)
            val api = SupabaseApi(client)
            val plan = api.getPlanById(planId)
            if (plan?.user_id == userId) {
                plan.toDomain()
            } else {
                null
            }
        } catch (e: SupabaseApiException) {
            throw e
        }
    }
    
    override fun getLessonSteps(planId: String, dayOfWeek: String?, slotNumber: Int?): Flow<List<LessonStep>> = flow {
        try {
            val responses = supabaseApi.getLessonSteps(planId, dayOfWeek, slotNumber)
            emit(responses.map { it.toDomain() })
        } catch (e: SupabaseApiException) {
            throw e
        }
    }
    
    override suspend fun getLessonStepById(stepId: String): LessonStep? {
        return try {
            supabaseApi.getLessonStepById(stepId)?.toDomain()
        } catch (e: SupabaseApiException) {
            throw e
        }
    }
    
    override fun getSchedule(userId: String, dayOfWeek: String?): Flow<List<ScheduleEntry>> = flow {
        try {
            val client = SupabaseClientFactory.createClientForUser(userId, supabaseConfig)
            val api = SupabaseApi(client)
            val responses = api.getSchedule(userId, dayOfWeek)
            emit(responses.map { it.toDomain() })
        } catch (e: SupabaseApiException) {
            throw e
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch schedule", e)
        }
    }
    
    override suspend fun getScheduleEntryById(entryId: String): ScheduleEntry? {
        return try {
            supabaseApi.getScheduleEntryById(entryId)?.toDomain()
        } catch (e: SupabaseApiException) {
            throw e
        }
    }
    
    override fun getUsers(): Flow<List<User>> = flow {
        val allUsers = mutableListOf<User>()
        val errors = mutableListOf<String>()
        
        // Project 1
        if (supabaseConfig.project1Url.isNotEmpty() && supabaseConfig.project1Key.isNotEmpty()) {
            try {
                Logger.d("Fetching users from Project 1")
                val client1 = SupabaseClientFactory.createClient("project1", supabaseConfig)
                val api1 = SupabaseApi(client1)
                val users1 = api1.getUsers().map { it.toDomain() }
                Logger.d("Fetched ${users1.size} users from Project 1")
                allUsers.addAll(users1)
            } catch (e: Exception) {
                Logger.e("Failed to fetch users from Project 1", e)
                errors.add("Project 1: ${e.message}")
            }
        }
        
        // Project 2
        if (supabaseConfig.project2Url.isNotEmpty() && supabaseConfig.project2Key.isNotEmpty()) {
            try {
                Logger.d("Fetching users from Project 2")
                val client2 = SupabaseClientFactory.createClient("project2", supabaseConfig)
                val api2 = SupabaseApi(client2)
                val users2 = api2.getUsers().map { it.toDomain() }
                Logger.d("Fetched ${users2.size} users from Project 2")
                // Avoid duplicates if user exists in both (by ID)
                for (user in users2) {
                    if (allUsers.none { it.id == user.id }) {
                        allUsers.add(user)
                    }
                }
            } catch (e: Exception) {
                Logger.e("Failed to fetch users from Project 2", e)
                errors.add("Project 2: ${e.message}")
            }
        }
        
        if (allUsers.isEmpty() && errors.isNotEmpty()) {
            throw SupabaseApiException("Failed to fetch users from any project: ${errors.joinToString("; ")}")
        }
        
        emit(allUsers)
    }
    
    override suspend fun getUserById(userId: String): User? {
        return try {
            val client = SupabaseClientFactory.createClientForUser(userId, supabaseConfig)
            val api = SupabaseApi(client)
            api.getUserById(userId)?.toDomain()
        } catch (e: SupabaseApiException) {
            throw e
        }
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
    
    // Extension functions to convert responses to domain models
    private fun com.bilingual.lessonplanner.data.remote.api.WeeklyPlanResponse.toDomain(): WeeklyPlan {
        return WeeklyPlan(
            id = id,
            userId = user_id,
            weekOf = week_of,
            generatedAt = generated_at,
            status = status,
            lessonJson = lesson_json,
            outputFile = output_file,
            errorMessage = error_message,
            updatedAt = updated_at,
            syncedAt = synced_at
        )
    }
    
    private fun com.bilingual.lessonplanner.data.remote.api.LessonStepResponse.toDomain(): LessonStep {
        return LessonStep(
            id = id,
            lessonPlanId = lesson_plan_id,
            dayOfWeek = day_of_week,
            slotNumber = slot_number,
            stepNumber = step_number,
            stepName = step_name,
            durationMinutes = duration_minutes,
            contentType = content_type,
            displayContent = display_content,
            hiddenContent = hidden_content,
            sentenceFrames = sentence_frames,
            materialsNeeded = materials_needed,
            vocabularyCognates = vocabulary_cognates,
            syncedAt = synced_at
        )
    }
    
    private fun com.bilingual.lessonplanner.data.remote.api.ScheduleEntryResponse.toDomain(): ScheduleEntry {
        return ScheduleEntry(
            id = id,
            userId = user_id,
            dayOfWeek = day_of_week,
            startTime = start_time,
            endTime = end_time,
            subject = subject,
            homeroom = homeroom,
            grade = grade,
            slotNumber = slot_number,
            planSlotGroupId = plan_slot_group_id,
            isActive = is_active,
            syncedAt = synced_at
        )
    }
    
    private fun com.bilingual.lessonplanner.data.remote.api.UserResponse.toDomain(): User {
        return User(
            id = id,
            name = name,
            email = email,
            createdAt = created_at,
            updatedAt = updated_at
        )
    }
}
