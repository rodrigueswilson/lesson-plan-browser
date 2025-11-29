package com.bilingual.lessonplanner.data.mapper

import com.bilingual.lessonplanner.data.local.database.entities.WeeklyPlanEntity
import com.bilingual.lessonplanner.domain.model.WeeklyPlan

fun WeeklyPlanEntity.toDomain(): WeeklyPlan {
    return WeeklyPlan(
        id = id,
        userId = userId,
        weekOf = weekOf,
        generatedAt = generatedAt,
        status = status,
        lessonJson = lessonJson,
        outputFile = outputFile,
        errorMessage = errorMessage,
        updatedAt = updatedAt,
        syncedAt = syncedAt
    )
}

fun WeeklyPlan.toEntity(): WeeklyPlanEntity {
    return WeeklyPlanEntity(
        id = id,
        userId = userId,
        weekOf = weekOf,
        generatedAt = generatedAt,
        status = status,
        lessonJson = lessonJson,
        outputFile = outputFile,
        errorMessage = errorMessage,
        updatedAt = updatedAt,
        syncedAt = syncedAt
    )
}

