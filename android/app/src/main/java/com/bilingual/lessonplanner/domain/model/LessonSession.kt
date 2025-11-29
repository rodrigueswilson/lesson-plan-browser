package com.bilingual.lessonplanner.domain.model

data class LessonSession(
    val sessionId: String,
    val planId: String,
    val dayOfWeek: String,
    val slotNumber: Int,
    val startTime: Long,
    val currentStepIndex: Int = 0,
    val isPaused: Boolean = true,
    val elapsedSeconds: Long = 0L, // Total elapsed time for the lesson
    val stepElapsedSeconds: Long = 0L, // Elapsed time for the current step
    val completedStepIds: Set<String> = emptySet()
)