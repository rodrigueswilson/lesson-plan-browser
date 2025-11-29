package com.bilingual.lessonplanner.domain.model

data class LessonStep(
    val id: String,
    val lessonPlanId: String,
    val dayOfWeek: String, // "monday" | "tuesday" | etc.
    val slotNumber: Int,
    val stepNumber: Int,
    val stepName: String,
    val durationMinutes: Int,
    val contentType: String, // "objective" | "sentence_frames" | etc.
    val displayContent: String,
    val hiddenContent: String?, // JSON array
    val sentenceFrames: String?, // JSON array
    val materialsNeeded: String?, // JSON array
    val vocabularyCognates: String?, // JSON array
    val syncedAt: Long?
)

