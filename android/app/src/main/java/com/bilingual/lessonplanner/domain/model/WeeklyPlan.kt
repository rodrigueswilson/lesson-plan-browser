package com.bilingual.lessonplanner.domain.model

data class WeeklyPlan(
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

