package com.bilingual.lessonplanner.data.local.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "schedule_entries",
    indices = [
        Index(value = ["userId"]),
        Index(value = ["dayOfWeek"]),
        Index(value = ["userId", "dayOfWeek"]),
        Index(value = ["isActive"])
    ]
)
data class ScheduleEntryEntity(
    @PrimaryKey
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

