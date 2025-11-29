package com.bilingual.lessonplanner.data.remote.api

import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Columns
import kotlinx.serialization.Serializable

@Serializable
data class WeeklyPlanResponse(
    val id: String,
    val user_id: String,
    val week_of: String,
    val generated_at: String,
    val status: String,
    val lesson_json: String?,
    val output_file: String?,
    val error_message: String?,
    val updated_at: Long,
    val synced_at: Long?
)

@Serializable
data class LessonStepResponse(
    val id: String,
    val lesson_plan_id: String,
    val day_of_week: String,
    val slot_number: Int,
    val step_number: Int,
    val step_name: String,
    val duration_minutes: Int,
    val content_type: String,
    val display_content: String,
    val hidden_content: String?,
    val sentence_frames: String?,
    val materials_needed: String?,
    val vocabulary_cognates: String?,
    val synced_at: Long?
)

@Serializable
data class ScheduleEntryResponse(
    val id: String,
    val user_id: String,
    val day_of_week: String,
    val start_time: String,
    val end_time: String,
    val subject: String,
    val homeroom: String?,
    val grade: String?,
    val slot_number: Int,
    val plan_slot_group_id: String?,
    val is_active: Boolean,
    val synced_at: Long?
)

@Serializable
data class UserResponse(
    val id: String,
    val name: String,
    val email: String?,
    val created_at: Long?,
    val updated_at: Long?
)

class SupabaseApi(private val client: SupabaseClient) {
    
    suspend fun getPlans(userId: String, updatedAfter: Long? = null): List<WeeklyPlanResponse> {
        return try {
            val query = client.from("weekly_plans")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("user_id", userId)
                        updatedAfter?.let { gt("updated_at", it) }
                    }
                }
            query.decodeList<WeeklyPlanResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch plans", e)
        }
    }
    
    suspend fun getPlanById(planId: String): WeeklyPlanResponse? {
        return try {
            client.from("weekly_plans")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("id", planId)
                    }
                }
                .decodeSingleOrNull<WeeklyPlanResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch plan", e)
        }
    }
    
    suspend fun getLessonSteps(planId: String, dayOfWeek: String? = null, slotNumber: Int? = null): List<LessonStepResponse> {
        return try {
            val query = client.from("lesson_steps")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("lesson_plan_id", planId)
                        dayOfWeek?.let { eq("day_of_week", it) }
                        slotNumber?.let { eq("slot_number", it) }
                    }
                }
            query.decodeList<LessonStepResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch lesson steps", e)
        }
    }
    
    suspend fun getLessonStepById(stepId: String): LessonStepResponse? {
        return try {
            client.from("lesson_steps")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("id", stepId)
                    }
                }
                .decodeSingleOrNull<LessonStepResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch lesson step", e)
        }
    }
    
    suspend fun getSchedule(userId: String, dayOfWeek: String? = null): List<ScheduleEntryResponse> {
        return try {
            val query = client.from("schedule_entries")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("user_id", userId)
                        eq("is_active", true)
                        dayOfWeek?.let { eq("day_of_week", it) }
                    }
                }
            query.decodeList<ScheduleEntryResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch schedule", e)
        }
    }
    
    suspend fun getScheduleEntryById(entryId: String): ScheduleEntryResponse? {
        return try {
            client.from("schedule_entries")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("id", entryId)
                    }
                }
                .decodeSingleOrNull<ScheduleEntryResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch schedule entry", e)
        }
    }
    
    suspend fun getUsers(): List<UserResponse> {
        return try {
            client.from("users")
                .select(columns = Columns.ALL)
                .decodeList<UserResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch users", e)
        }
    }
    
    suspend fun getUserById(userId: String): UserResponse? {
        return try {
            client.from("users")
                .select(columns = Columns.ALL) {
                    filter {
                        eq("id", userId)
                    }
                }
                .decodeSingleOrNull<UserResponse>()
        } catch (e: Exception) {
            throw SupabaseApiException("Failed to fetch user", e)
        }
    }
}

class SupabaseApiException(message: String, cause: Throwable? = null) : Exception(message, cause)

