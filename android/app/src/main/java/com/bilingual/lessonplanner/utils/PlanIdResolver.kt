package com.bilingual.lessonplanner.utils

import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.domain.model.WeeklyPlan
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import kotlinx.coroutines.flow.first
import java.text.SimpleDateFormat
import java.util.*

/**
 * Resolves the plan ID for a schedule entry based on week context.
 * Finds the plan that matches the schedule entry's week and other criteria.
 */
suspend fun resolvePlanIdFromScheduleEntry(
    scheduleEntry: ScheduleEntry,
    userId: String,
    repository: PlanRepository,
    plans: List<WeeklyPlan>? = null
): PlanResolutionResult? {
    try {
        // If plans not provided, fetch them
        val availablePlans = plans ?: repository.getPlans(userId).first()

        if (availablePlans.isEmpty()) {
            return null
        }

        // Get the current week based on the schedule entry's day
        val currentWeekOf = getWeekOfForDay(scheduleEntry.dayOfWeek)

        // Try to find a plan that matches the week
        // First, try exact match with current week
        var matchingPlan = availablePlans.find { it.weekOf == currentWeekOf }

        // If no exact match, try to find the most recent plan for that week
        if (matchingPlan == null) {
            // Find plans that could match (same week format pattern)
            val candidatePlans = availablePlans.filter { plan ->
                plan.weekOf?.let { weeksOverlap(it, currentWeekOf) } == true
            }

            if (candidatePlans.isNotEmpty()) {
                // Sort by week_of descending (most recent first)
                matchingPlan = candidatePlans.sortedByDescending { it.weekOf }.first()
            }
        }

        // If still no match, use the most recent plan as fallback
        if (matchingPlan == null) {
            matchingPlan = availablePlans
                .filter { it.weekOf != null }
                .sortedByDescending { it.weekOf }
                .firstOrNull()
        }

        if (matchingPlan == null) {
            return null
        }

        // Verify the plan has data
        val planDetail = repository.getPlanDetail(matchingPlan.id, userId)
        if (planDetail?.lessonJson != null) {
            return PlanResolutionResult(
                planId = matchingPlan.id,
                day = scheduleEntry.dayOfWeek,
                slot = scheduleEntry.slotNumber
            )
        }

        return PlanResolutionResult(
            planId = matchingPlan.id,
            day = scheduleEntry.dayOfWeek,
            slot = scheduleEntry.slotNumber
        )
    } catch (error: Exception) {
        return null
    }
}

data class PlanResolutionResult(
    val planId: String,
    val day: String,
    val slot: Int
)

/**
 * Gets the week_of format for a given day of the week.
 * Returns format like "MM/DD-MM/DD" representing the week containing that day.
 */
private fun getWeekOfForDay(dayOfWeek: String): String {
    val now = Calendar.getInstance()
    val dayIndex = listOf("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")
        .indexOf(dayOfWeek.lowercase())

    if (dayIndex == -1) {
        return formatWeekOf(now)
    }

    // Find the Monday of the week containing this day
    val currentDayIndex = now.get(Calendar.DAY_OF_WEEK)
    val daysUntilMonday = (currentDayIndex + 7 - 1) % 7
    val monday = Calendar.getInstance().apply {
        time = now.time
        add(Calendar.DAY_OF_MONTH, -daysUntilMonday)
    }

    // Adjust if we're looking at a specific day
    val targetDayIndex = if (dayIndex == 0) 7 else dayIndex + 1
    val daysDifference = (targetDayIndex - 1) - (if (currentDayIndex == Calendar.SUNDAY) 7 else currentDayIndex - 1)
    val targetDate = Calendar.getInstance().apply {
        time = now.time
        add(Calendar.DAY_OF_MONTH, daysDifference)
    }

    // Find Monday of the week containing targetDate
    val targetDayOfWeek = targetDate.get(Calendar.DAY_OF_WEEK)
    val daysToMonday = (targetDayOfWeek + 7 - 1) % 7
    val weekMonday = Calendar.getInstance().apply {
        time = targetDate.time
        add(Calendar.DAY_OF_MONTH, -daysToMonday)
    }

    return formatWeekOf(weekMonday)
}

/**
 * Formats a date as week_of string (MM/DD-MM/DD format).
 * Assumes the date is a Monday.
 */
private fun formatWeekOf(monday: Calendar): String {
    val sunday = Calendar.getInstance().apply {
        time = monday.time
        add(Calendar.DAY_OF_MONTH, 6)
    }

    val formatDate = { cal: Calendar ->
        val month = (cal.get(Calendar.MONTH) + 1).toString().padStart(2, '0')
        val day = cal.get(Calendar.DAY_OF_MONTH).toString().padStart(2, '0')
        "$month/$day"
    }

    return "${formatDate(monday)}-${formatDate(sunday)}"
}

/**
 * Checks if two week_of strings overlap (same week).
 */
private fun weeksOverlap(week1: String, week2: String): Boolean {
    if (week1.isEmpty() || week2.isEmpty()) return false
    if (week1 == week2) return true

    try {
        val (start1, end1) = parseWeekOf(week1)
        val (start2, end2) = parseWeekOf(week2)

        if (start1 == null || end1 == null || start2 == null || end2 == null) return false

        // Check if ranges overlap
        return start1 <= end2 && start2 <= end1
    } catch (e: Exception) {
        return false
    }
}

/**
 * Parses a week_of string into start and end dates.
 */
private fun parseWeekOf(weekOf: String): Pair<Date?, Date?> {
    // Support YYYY-MM-DD format (ISO 8601) - Standard for Supabase
    if (weekOf.matches(Regex("\\d{4}-\\d{2}-\\d{2}"))) {
        try {
            val format = SimpleDateFormat("yyyy-MM-dd", Locale.US)
            val start = format.parse(weekOf) ?: return Pair(null, null)
            val cal = Calendar.getInstance()
            cal.time = start
            cal.add(Calendar.DAY_OF_YEAR, 6)
            val end = cal.time
            return Pair(start, end)
        } catch (e: Exception) {
            return Pair(null, null)
        }
    }

    val parts = weekOf.split("-")
    if (parts.size != 2) return Pair(null, null)

    try {
        val startParts = parts[0].split("/").map { it.toInt() }
        val endParts = parts[1].split("/").map { it.toInt() }

        val currentYear = Calendar.getInstance().get(Calendar.YEAR)
        val start = Calendar.getInstance().apply {
            set(currentYear, startParts[0] - 1, startParts[1])
        }.time

        val end = Calendar.getInstance().apply {
            set(currentYear, endParts[0] - 1, endParts[1])
        }.time

        return Pair(start, end)
    } catch (e: Exception) {
        return Pair(null, null)
    }
}
