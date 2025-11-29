package com.bilingual.lessonplanner.domain.model

data class ScheduleEntry(
    val id: String,
    val userId: String,
    val dayOfWeek: String, // "monday" | "tuesday" | etc.
    val startTime: String, // "08:15"
    val endTime: String, // "08:30"
    val subject: String,
    val homeroom: String?,
    val grade: String?,
    val slotNumber: Int,
    val planSlotGroupId: String?,
    val isActive: Boolean,
    val syncedAt: Long?
)

