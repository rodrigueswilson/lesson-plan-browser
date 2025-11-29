package com.bilingual.lessonplanner.data.sync

import android.content.Context
import com.bilingual.lessonplanner.data.local.database.dao.SyncMetadataDao
import com.bilingual.lessonplanner.data.local.database.entities.SyncMetadataEntity
import com.bilingual.lessonplanner.data.local.repository.LocalPlanRepository
import com.bilingual.lessonplanner.data.mapper.toEntity
import com.bilingual.lessonplanner.data.remote.api.SupabaseApi
import com.bilingual.lessonplanner.data.remote.repository.RemotePlanRepository
import com.bilingual.lessonplanner.utils.Logger
import kotlinx.coroutines.flow.first

class SyncManager(
    private val context: Context,
    private val localRepository: LocalPlanRepository,
    private val remoteRepository: RemotePlanRepository,
    private val syncMetadataDao: SyncMetadataDao,
    private val networkAwareSyncManager: NetworkAwareSyncManager
) {
    
    suspend fun syncPlans(userId: String, forceFullSync: Boolean = false) {
        if (userId == "local-test-user") {
            Logger.d("Using local test user, generating/refreshing sample data")
            generateSampleData(userId)
            return
        }

        val networkType = networkAwareSyncManager.getNetworkType()
        val policy = SyncPolicy.forNetwork(networkType)
        
        if (!policy.allowFullSync && !policy.allowIncrementalSync) {
            Logger.d("Skipping sync for plans: no network available")
            return // No network, skip sync
        }
        
        Logger.d("Starting sync for plans, userId: $userId, networkType: $networkType, forceFullSync: $forceFullSync")
        
        try {
            val lastSyncKey = "plans_user_$userId"
            val lastSync = syncMetadataDao.getSyncMetadata(lastSyncKey)
            val shouldFullSync = forceFullSync || lastSync == null || policy.allowFullSync
            
            if (shouldFullSync && policy.allowFullSync) {
                // Full sync
                Logger.d("Performing full sync for plans")
                Logger.d("Fetching plans from Supabase for userId: $userId")
                val remotePlans = remoteRepository.getPlans(userId).first()
                Logger.d("Fetched ${remotePlans.size} plans from Supabase")
                
                // Log sample plan details
                remotePlans.take(3).forEach { plan ->
                    Logger.d("Plan: id=${plan.id}, weekOf=${plan.weekOf}, status=${plan.status}, hasLessonJson=${plan.lessonJson != null}")
                    plan.lessonJson?.let { json ->
                        Logger.d("  lesson_json length: ${json.length} chars")
                    }
                }
                
                // Save to local repository
                if (remotePlans.isNotEmpty()) {
                    localRepository.savePlans(remotePlans)
                    Logger.d("Saved ${remotePlans.size} plans to local database")
                } else {
                    Logger.w("No plans found in Supabase for userId: $userId")
                    Logger.w("This could mean: 1) Tables are empty, 2) RLS policies blocking access, 3) User has no plans")
                }
                syncMetadataDao.insertSyncMetadata(
                    SyncMetadataEntity(
                        id = lastSyncKey,
                        lastSyncedAt = System.currentTimeMillis(),
                        syncType = "plans",
                        entityId = userId
                    )
                )
            } else if (policy.allowIncrementalSync) {
                // Incremental sync - only fetch updated plans
                Logger.d("Performing incremental sync for plans, lastSyncTime: ${lastSync?.lastSyncedAt}")
                val lastSyncTime = lastSync?.lastSyncedAt ?: 0L
                Logger.d("Fetching plans updated after: $lastSyncTime (${java.util.Date(lastSyncTime)})")
                val remotePlans = remoteRepository.getPlans(userId, updatedAfter = lastSyncTime)
                Logger.d("Fetched ${remotePlans.size} updated plans from Supabase")
                
                // Save to local repository
                if (remotePlans.isNotEmpty()) {
                    localRepository.savePlans(remotePlans)
                    Logger.d("Saved ${remotePlans.size} updated plans to local database")
                } else {
                    Logger.d("No updated plans to sync (all plans are up to date)")
                }
                syncMetadataDao.insertSyncMetadata(
                    SyncMetadataEntity(
                        id = lastSyncKey,
                        lastSyncedAt = System.currentTimeMillis(),
                        syncType = "plans",
                        entityId = userId
                    )
                )
            }
        } catch (e: Exception) {
            Logger.e("Failed to sync plans for userId: $userId", e)
            Logger.e("Error type: ${e.javaClass.simpleName}, message: ${e.message}")
            e.printStackTrace()
            throw SyncException("Failed to sync plans: ${e.message}", e)
        }
    }
    
    suspend fun syncLessonSteps(planId: String) {
        if (planId.startsWith("sample-plan")) {
             Logger.d("Using sample plan, skipping remote step sync")
             return
        }

        val networkType = networkAwareSyncManager.getNetworkType()
        val policy = SyncPolicy.forNetwork(networkType)
        
        if (!policy.allowFullSync && !policy.allowIncrementalSync) {
            return
        }
        
        try {
            val lastSyncKey = "steps_plan_$planId"
            Logger.d("Fetching lesson steps for planId: $planId")
            val remoteSteps = remoteRepository.getLessonSteps(planId, null, null).first()
            Logger.d("Fetched ${remoteSteps.size} lesson steps from Supabase")
            
            // Log sample step details
            remoteSteps.take(3).forEach { step ->
                Logger.d("Step: ${step.stepNumber} - ${step.stepName} (${step.durationMinutes} min), day=${step.dayOfWeek}, slot=${step.slotNumber}")
            }
            
            // Save to local repository
            if (remoteSteps.isNotEmpty()) {
                localRepository.saveLessonSteps(remoteSteps)
                Logger.d("Saved ${remoteSteps.size} lesson steps to local database")
            } else {
                Logger.w("No lesson steps found for planId: $planId")
            }
            syncMetadataDao.insertSyncMetadata(
                SyncMetadataEntity(
                    id = lastSyncKey,
                    lastSyncedAt = System.currentTimeMillis(),
                    syncType = "steps",
                    entityId = planId
                )
            )
        } catch (e: Exception) {
            Logger.e("Failed to sync lesson steps for planId: $planId", e)
            Logger.e("Error type: ${e.javaClass.simpleName}, message: ${e.message}")
            throw SyncException("Failed to sync lesson steps: ${e.message}", e)
        }
    }
    
    suspend fun syncSchedule(userId: String) {
        if (userId == "local-test-user") {
            Logger.d("Using local test user, skipping remote schedule sync")
            // Sample data already generated by syncPlans or syncUsers
            return
        }

        val networkType = networkAwareSyncManager.getNetworkType()
        val policy = SyncPolicy.forNetwork(networkType)
        
        if (!policy.allowFullSync && !policy.allowIncrementalSync) {
            return
        }
        
        try {
            val lastSyncKey = "schedule_user_$userId"
            Logger.d("Fetching schedule for userId: $userId")
            val remoteSchedule = remoteRepository.getSchedule(userId, null).first()
            Logger.d("Fetched ${remoteSchedule.size} schedule entries from Supabase")
            
            // Log sample schedule details
            remoteSchedule.take(5).forEach { entry ->
                Logger.d("Schedule: ${entry.dayOfWeek} ${entry.startTime}-${entry.endTime} ${entry.subject} (slot ${entry.slotNumber})")
            }
            
            // Save to local repository
            if (remoteSchedule.isNotEmpty()) {
                localRepository.saveSchedule(remoteSchedule)
                Logger.d("Saved ${remoteSchedule.size} schedule entries to local database")
            } else {
                Logger.w("No schedule entries found for userId: $userId")
            }
            syncMetadataDao.insertSyncMetadata(
                SyncMetadataEntity(
                    id = lastSyncKey,
                    lastSyncedAt = System.currentTimeMillis(),
                    syncType = "schedule",
                    entityId = userId
                )
            )
            } catch (e: Exception) {
                Logger.e("Failed to sync schedule for userId: $userId", e)
                Logger.e("Error type: ${e.javaClass.simpleName}, message: ${e.message}")
                throw SyncException("Failed to sync schedule: ${e.message}", e)
            }
    }
    
    suspend fun syncUsers() {
        val networkType = networkAwareSyncManager.getNetworkType()
        val policy = SyncPolicy.forNetwork(networkType)
        
        if (!policy.allowFullSync && !policy.allowIncrementalSync) {
            Logger.d("Skipping sync for users: no network available")
            return
        }
        
            try {
                Logger.d("Starting sync for users")
                val lastSyncKey = "users"
                Logger.d("Fetching users from Supabase (both Project 1 and Project 2)")
                val remoteUsers = remoteRepository.getUsers().first()
                Logger.d("Fetched ${remoteUsers.size} users from Supabase")
                
                // Log user details
                remoteUsers.forEach { user ->
                    Logger.d("User: id=${user.id}, name=${user.name}, email=${user.email}")
                }
            
            // Save to local repository
            if (remoteUsers.isNotEmpty()) {
                localRepository.saveUsers(remoteUsers)
                Logger.d("Saved ${remoteUsers.size} users to local database")
            } else {
                Logger.d("No users to save")
                
                // FALLBACK FOR TESTING: If no users found remotely, create a local test user
                // This ensures the app is usable for testing even with an empty backend
                val mockUser = com.bilingual.lessonplanner.domain.model.User(
                    id = "local-test-user",
                    name = "Test User (Local)",
                    email = "test@local",
                    createdAt = System.currentTimeMillis(),
                    updatedAt = System.currentTimeMillis()
                )
                localRepository.saveUsers(listOf(mockUser))
                Logger.d("Created local test user because remote list was empty")
                
                // Generate sample data for testing
                generateSampleData(mockUser.id)
            }
            
            syncMetadataDao.insertSyncMetadata(
                SyncMetadataEntity(
                    id = lastSyncKey,
                    lastSyncedAt = System.currentTimeMillis(),
                    syncType = "users",
                    entityId = null
                )
            )
            Logger.d("Sync metadata updated for users")
            } catch (e: Exception) {
                Logger.e("Failed to sync users", e)
                Logger.e("Error type: ${e.javaClass.simpleName}, message: ${e.message}")
                Logger.e("This could indicate: 1) Supabase connection issue, 2) RLS policy blocking access, 3) Network error")
                e.printStackTrace()
                throw SyncException("Failed to sync users: ${e.message}", e)
            }
    }

    private suspend fun generateSampleData(userId: String) {
        Logger.d("Generating sample data for user: $userId")
        val currentWeekOf = "2025-11-24" // Sample date
        
        // 1. Create Sample Plan
        val samplePlan = com.bilingual.lessonplanner.domain.model.WeeklyPlan(
            id = "sample-plan-1",
            userId = userId,
            weekOf = currentWeekOf,
            generatedAt = "2025-11-23T12:00:00Z",
            status = "ready",
            lessonJson = "[]",
            outputFile = null,
            errorMessage = null,
            updatedAt = System.currentTimeMillis(),
            syncedAt = System.currentTimeMillis()
        )
        localRepository.savePlans(listOf(samplePlan))
        
        // 2. Create Sample Schedule
        val schedule = mutableListOf<com.bilingual.lessonplanner.domain.model.ScheduleEntry>()
        val days = listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
        
        days.forEach { day ->
            // Slot 1: Math
            schedule.add(
                com.bilingual.lessonplanner.domain.model.ScheduleEntry(
                    id = "sched-$day-1",
                    userId = userId,
                    dayOfWeek = day,
                    startTime = "08:00",
                    endTime = "09:00",
                    subject = "Math",
                    homeroom = "101",
                    grade = "5",
                    slotNumber = 1,
                    planSlotGroupId = "math-group",
                    isActive = true,
                    syncedAt = System.currentTimeMillis()
                )
            )
            
            // Slot 2: ELA
            schedule.add(
                com.bilingual.lessonplanner.domain.model.ScheduleEntry(
                    id = "sched-$day-2",
                    userId = userId,
                    dayOfWeek = day,
                    startTime = "09:00",
                    endTime = "10:00",
                    subject = "ELA",
                    homeroom = "101",
                    grade = "5",
                    slotNumber = 2,
                    planSlotGroupId = "ela-group",
                    isActive = true,
                    syncedAt = System.currentTimeMillis()
                )
            )
        }
        localRepository.saveSchedule(schedule)
        
        // 3. Create Sample Lesson Steps
        val steps = mutableListOf<com.bilingual.lessonplanner.domain.model.LessonStep>()
        
        // Monday Math Lesson
        steps.add(
            com.bilingual.lessonplanner.domain.model.LessonStep(
                id = "step-mon-1-1",
                lessonPlanId = samplePlan.id,
                dayOfWeek = "Monday",
                slotNumber = 1,
                stepNumber = 1,
                stepName = "Warm-up",
                durationMinutes = 10,
                contentType = "text",
                displayContent = "Review multiplication tables.",
                hiddenContent = null,
                sentenceFrames = "The product of _ and _ is _.",
                materialsNeeded = "Whiteboard, markers",
                vocabularyCognates = "Product / Producto",
                syncedAt = System.currentTimeMillis()
            )
        )
        steps.add(
            com.bilingual.lessonplanner.domain.model.LessonStep(
                id = "step-mon-1-2",
                lessonPlanId = samplePlan.id,
                dayOfWeek = "Monday",
                slotNumber = 1,
                stepNumber = 2,
                stepName = "Instruction",
                durationMinutes = 20,
                contentType = "text",
                displayContent = "Introduce long division concepts.",
                hiddenContent = "Use visual aids.",
                sentenceFrames = "First, I divide... then I multiply...",
                materialsNeeded = null,
                vocabularyCognates = "Division / División",
                syncedAt = System.currentTimeMillis()
            )
        )
        
        // Monday ELA Lesson
        steps.add(
            com.bilingual.lessonplanner.domain.model.LessonStep(
                id = "step-mon-2-1",
                lessonPlanId = samplePlan.id,
                dayOfWeek = "Monday",
                slotNumber = 2,
                stepNumber = 1,
                stepName = "Reading",
                durationMinutes = 30,
                contentType = "text",
                displayContent = "Read Chapter 1 of 'The Giver'.",
                hiddenContent = null,
                sentenceFrames = "I think the character is feeling...",
                materialsNeeded = "Books",
                vocabularyCognates = "Memory / Memoria",
                syncedAt = System.currentTimeMillis()
            )
        )
        
        localRepository.saveLessonSteps(steps)
        Logger.d("Sample data generation complete")
    }
}

class SyncException(message: String, cause: Throwable? = null) : Exception(message, cause)

