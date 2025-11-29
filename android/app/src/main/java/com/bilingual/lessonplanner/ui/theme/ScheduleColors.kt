package com.bilingual.lessonplanner.ui.theme

import androidx.compose.ui.graphics.Color

data class SubjectColor(
    val bg: Color,
    val border: Color,
    val text: Color
)

object ScheduleColors {
    // Non-class periods
    val Prep = SubjectColor(
        bg = Color(0xFFE2E8F0), // bg-slate-200
        border = Color(0xFF94A3B8), // border-slate-400
        text = Color(0xFF0F172A) // text-slate-900
    )
    
    val AMRoutine = SubjectColor(
        bg = Color(0xFFEFF6FF), // bg-blue-50
        border = Color(0xFFBFDBFE), // border-blue-200
        text = Color(0xFF1E40AF) // text-blue-800
    )
    
    val Lunch = SubjectColor(
        bg = Color(0xFFFFEDD5), // bg-orange-100
        border = Color(0xFFFB923C), // border-orange-400
        text = Color(0xFF7C2D12) // text-orange-900
    )
    
    val Dismissal = SubjectColor(
        bg = Color(0xFFFAF5FF), // bg-purple-50
        border = Color(0xFFE9D5FF), // border-purple-200
        text = Color(0xFF6B21A8) // text-purple-800
    )

    // Homeroom Colors
    val Green = SubjectColor(
        bg = Color(0xFFF0FDF4), // bg-green-50
        border = Color(0xFF86EFAC), // border-green-300
        text = Color(0xFF166534) // text-green-800
    )
    
    val Blue = SubjectColor(
        bg = Color(0xFFEFF6FF), // bg-blue-50
        border = Color(0xFF93C5FD), // border-blue-300
        text = Color(0xFF1E40AF) // text-blue-800
    )
    
    val Purple = SubjectColor(
        bg = Color(0xFFFAF5FF), // bg-purple-50
        border = Color(0xFFD8B4FE), // border-purple-300
        text = Color(0xFF6B21A8) // text-purple-800
    )
    
    val Yellow = SubjectColor(
        bg = Color(0xFFFEFCE8), // bg-yellow-50
        border = Color(0xFFFDE047), // border-yellow-300
        text = Color(0xFF854D0E) // text-yellow-800
    )
    
    val Pink = SubjectColor(
        bg = Color(0xFFFDF2F8), // bg-pink-50
        border = Color(0xFFF9A8D4), // border-pink-300
        text = Color(0xFF9D174D) // text-pink-800
    )
    
    val Indigo = SubjectColor(
        bg = Color(0xFFEEF2FF), // bg-indigo-50
        border = Color(0xFFA5B4FC), // border-indigo-300
        text = Color(0xFF3730A3) // text-indigo-800
    )
    
    val Teal = SubjectColor(
        bg = Color(0xFFF0FDFA), // bg-teal-50
        border = Color(0xFF5EEAD4), // border-teal-300
        text = Color(0xFF115E59) // text-teal-800
    )
    
    val Orange = SubjectColor(
        bg = Color(0xFFFFF7ED), // bg-orange-50
        border = Color(0xFFFDBA74), // border-orange-300
        text = Color(0xFF9A3412) // text-orange-800
    )
    
    val Cyan = SubjectColor(
        bg = Color(0xFFECFEFF), // bg-cyan-50
        border = Color(0xFF67E8F9), // border-cyan-300
        text = Color(0xFF155E75) // text-cyan-800
    )
    
    val Emerald = SubjectColor(
        bg = Color(0xFFECFDF5), // bg-emerald-50
        border = Color(0xFF6EE7B7), // border-emerald-300
        text = Color(0xFF065F46) // text-emerald-800
    )
    
    val Default = SubjectColor(
        bg = Color(0xFFF9FAFB), // bg-gray-50
        border = Color(0xFFE5E7EB), // border-gray-200
        text = Color(0xFF374151) // text-gray-700
    )

    private val homeroomPalette = listOf(
        Green, Blue, Purple, Yellow, Pink, Indigo, Teal, Orange, Cyan, Emerald
    )

    fun getSubjectColors(subject: String?, grade: String? = null, homeroom: String? = null): SubjectColor {
        if (subject.isNullOrEmpty()) return Default

        val normalized = subject.trim().uppercase()

        // Non-class periods
        if (normalized == "PREP" || normalized == "PREP TIME") return Prep
        if (normalized == "LUNCH") return Lunch
        if (normalized in listOf("A.M. ROUTINE", "AM ROUTINE", "MORNING ROUTINE")) return AMRoutine
        if (normalized == "DISMISSAL") return Dismissal

        // Homeroom-based coloring
        if (homeroom != null) {
            return generateColorFromHomeroom(homeroom)
        }

        // Fallback mapping for known subjects if no homeroom
        return when (normalized) {
            "ELA" -> Green
            "MATH" -> Blue
            "SCIENCE" -> Yellow
            "SOCIAL STUDIES", "SOCIAL S.", "SOCIAL SCIENCE" -> SubjectColor(
                bg = Color(0xFFFEF2F2), // bg-red-50
                border = Color(0xFFFCA5A5), // border-red-300
                text = Color(0xFF991B1B) // text-red-800
            )
            else -> Default
        }
    }

    private fun generateColorFromHomeroom(homeroom: String): SubjectColor {
        var hash = 0
        val normalized = homeroom.trim().uppercase()
        for (char in normalized) {
            hash = char.code + ((hash shl 5) - hash)
        }
        val index = Math.abs(hash) % homeroomPalette.size
        return homeroomPalette[index]
    }
    
    fun isNonClassPeriod(subject: String?): Boolean {
        if (subject == null) return false
        val normalized = subject.trim().uppercase()
        val amRoutinePattern = Regex("^A\\.?\\s*M\\.?\\s*ROUTINE$")
        return normalized in listOf("PREP", "PREP TIME", "LUNCH", "A.M. ROUTINE", "A. M. ROUTINE", "AM ROUTINE", "MORNING ROUTINE", "DISMISSAL") ||
                amRoutinePattern.matches(normalized)
    }
}

