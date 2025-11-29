package com.bilingual.lessonplanner.data.remote.config

/**
 * Supabase configuration data class.
 * Contains URLs and API keys for both Supabase projects.
 */
data class SupabaseConfig(
    val project1Url: String,
    val project1Key: String,
    val project2Url: String,
    val project2Key: String
) {
    fun isValid(): Boolean {
        return project1Url.isNotEmpty() && project1Key.isNotEmpty() &&
               project2Url.isNotEmpty() && project2Key.isNotEmpty()
    }
}

