package com.bilingual.lessonplanner.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "sync_metadata")
data class SyncMetadataEntity(
    @PrimaryKey
    val id: String, // e.g., "plans_user_123" or "steps_plan_456"
    val lastSyncedAt: Long,
    val syncType: String, // "plans" | "steps" | "schedule" | "users"
    val entityId: String? // Optional: specific entity ID if applicable
)

