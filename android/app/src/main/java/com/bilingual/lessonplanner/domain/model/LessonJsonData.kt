package com.bilingual.lessonplanner.domain.model

data class LessonJsonData(
    val days: Map<String, DayData> // Map of day names (Monday, Tuesday, etc.) to day data
)

data class DayData(
    val slots: Map<String, SlotData> // Map of slot numbers (as strings) to slot data
)

data class SlotData(
    val objectives: ObjectiveData?,
    val vocabulary: List<String>?,
    val vocabulary_cognates: List<String>?,
    val sentence_frames: List<String>?,
    val materials_needed: List<String>?,
    val instruction_steps: List<InstructionStepData>?
)

data class ObjectiveData(
    val content: String?,
    val language: String?
)

data class InstructionStepData(
    val stepNumber: Int?,
    val stepName: String?,
    val durationMinutes: Int?,
    val content: String?,
    val hiddenContent: String?
)

