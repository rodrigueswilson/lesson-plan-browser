package com.bilingual.lessonplanner.ui.browser

enum class ViewMode {
    WEEK,
    DAY,
    LESSON
}

data class BrowserUiState(
    val currentViewMode: ViewMode = ViewMode.WEEK,
    val selectedWeek: String? = null, // Format: "2025-W01"
    val selectedDay: String? = null, // "monday", "tuesday", etc.
    val selectedLessonId: String? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

