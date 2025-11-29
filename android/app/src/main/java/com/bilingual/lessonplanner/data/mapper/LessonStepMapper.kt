package com.bilingual.lessonplanner.data.mapper

import com.bilingual.lessonplanner.data.local.database.entities.LessonStepEntity
import com.bilingual.lessonplanner.domain.model.LessonStep

fun LessonStepEntity.toDomain(): LessonStep {
    return LessonStep(
        id = id,
        lessonPlanId = lessonPlanId,
        dayOfWeek = dayOfWeek,
        slotNumber = slotNumber,
        stepNumber = stepNumber,
        stepName = stepName,
        durationMinutes = durationMinutes,
        contentType = contentType,
        displayContent = displayContent,
        hiddenContent = hiddenContent,
        sentenceFrames = sentenceFrames,
        materialsNeeded = materialsNeeded,
        vocabularyCognates = vocabularyCognates,
        syncedAt = syncedAt
    )
}

fun LessonStep.toEntity(): LessonStepEntity {
    return LessonStepEntity(
        id = id,
        lessonPlanId = lessonPlanId,
        dayOfWeek = dayOfWeek,
        slotNumber = slotNumber,
        stepNumber = stepNumber,
        stepName = stepName,
        durationMinutes = durationMinutes,
        contentType = contentType,
        displayContent = displayContent,
        hiddenContent = hiddenContent,
        sentenceFrames = sentenceFrames,
        materialsNeeded = materialsNeeded,
        vocabularyCognates = vocabularyCognates,
        syncedAt = syncedAt
    )
}

