package com.bilingual.lessonplanner.data.local.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "weekly_plans",
    indices = [
        Index(value = ["userId"]),
        Index(value = ["weekOf"]),
        Index(value = ["updatedAt"])
    ]
)
data class WeeklyPlanEntity(
    @PrimaryKey
    val id: String,
    val userId: String,
    val weekOf: String, // Format: "2025-W01"
    val generatedAt: String,
    val status: String, // "pending" | "processing" | "completed" | "failed"
    val lessonJson: String?, // Full JSON plan data
    val outputFile: String?,
    val errorMessage: String?,
    val updatedAt: Long, // Timestamp for sync
    val syncedAt: Long? // Last successful sync
)

