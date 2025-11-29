package com.bilingual.lessonplanner.data.mapper

import com.bilingual.lessonplanner.data.local.database.entities.ScheduleEntryEntity
import com.bilingual.lessonplanner.domain.model.ScheduleEntry

fun ScheduleEntryEntity.toDomain(): ScheduleEntry {
    return ScheduleEntry(
        id = id,
        userId = userId,
        dayOfWeek = dayOfWeek,
        startTime = startTime,
        endTime = endTime,
        subject = subject,
        homeroom = homeroom,
        grade = grade,
        slotNumber = slotNumber,
        planSlotGroupId = planSlotGroupId,
        isActive = isActive,
        syncedAt = syncedAt
    )
}

fun ScheduleEntry.toEntity(): ScheduleEntryEntity {
    return ScheduleEntryEntity(
        id = id,
        userId = userId,
        dayOfWeek = dayOfWeek,
        startTime = startTime,
        endTime = endTime,
        subject = subject,
        homeroom = homeroom,
        grade = grade,
        slotNumber = slotNumber,
        planSlotGroupId = planSlotGroupId,
        isActive = isActive,
        syncedAt = syncedAt
    )
}

