package com.bilingual.lessonplanner.utils

import com.bilingual.lessonplanner.domain.model.LessonStep
import kotlin.math.ceil
import kotlin.math.max

sealed class TimerAdjustment {
    data class Add(val minutes: Int) : TimerAdjustment()
    data class Subtract(val minutes: Int) : TimerAdjustment()
    object Reset : TimerAdjustment()
    data class Skip(val targetStepIndex: Int) : TimerAdjustment()
}

data class RecalculatedStep(
    val step: LessonStep,
    val adjustedDurationSeconds: Long,
    val originalDurationSeconds: Long
) {
    fun toLessonStep(): LessonStep {
        return step.copy(
            durationMinutes = ceil(adjustedDurationSeconds / 60.0).toInt()
        )
    }
}

object LessonStepRecalculation {
    fun recalculateStepDurations(
        steps: List<RecalculatedStep>,
        currentStepIndex: Int,
        adjustment: TimerAdjustment
    ): List<RecalculatedStep> {
        if (steps.isEmpty() || currentStepIndex < 0 || currentStepIndex >= steps.size) {
            return steps
        }

        val result = steps.toMutableList()
        val currentStep = result[currentStepIndex]
        
        when (adjustment) {
            is TimerAdjustment.Add -> {
                val addedSeconds = adjustment.minutes * 60L
                val newDuration = currentStep.adjustedDurationSeconds + addedSeconds
                result[currentStepIndex] = currentStep.copy(adjustedDurationSeconds = newDuration)
            }
            is TimerAdjustment.Subtract -> {
                val subSeconds = adjustment.minutes * 60L
                val newDuration = max(60L, currentStep.adjustedDurationSeconds - subSeconds)
                result[currentStepIndex] = currentStep.copy(adjustedDurationSeconds = newDuration)
            }
            is TimerAdjustment.Reset -> {
                return result.map { it.copy(adjustedDurationSeconds = it.originalDurationSeconds) }
            }
            is TimerAdjustment.Skip -> {
                return result
            }
        }
        
        // Proportionally adjust remaining steps if Add/Subtract
        if (currentStepIndex + 1 < result.size && (adjustment is TimerAdjustment.Add || adjustment is TimerAdjustment.Subtract)) {
            val currentStepNew = result[currentStepIndex]
            val diff = currentStepNew.adjustedDurationSeconds - currentStep.adjustedDurationSeconds
            
            // Calculate total duration of remaining steps (using current/adjusted values)
            var totalRemaining = 0L
            for (i in (currentStepIndex + 1) until result.size) {
                totalRemaining += result[i].adjustedDurationSeconds
            }
            
            if (totalRemaining > 0) {
                for (i in (currentStepIndex + 1) until result.size) {
                    val step = result[i]
                    val proportion = step.adjustedDurationSeconds.toDouble() / totalRemaining
                    val stepAdjustment = (diff * proportion).toLong()
                    val newDuration = max(60L, step.adjustedDurationSeconds + stepAdjustment)
                    result[i] = step.copy(adjustedDurationSeconds = newDuration)
                }
            }
        }
        
        return result
    }
}
