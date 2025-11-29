package com.bilingual.lessonplanner.utils

import com.bilingual.lessonplanner.data.remote.config.SupabaseConfig

/**
 * Validates Supabase configuration and provides helpful error messages.
 */
object ConfigValidator {
    
    data class ValidationResult(
        val isValid: Boolean,
        val errors: List<String> = emptyList(),
        val warnings: List<String> = emptyList()
    )
    
    fun validate(config: SupabaseConfig): ValidationResult {
        val errors = mutableListOf<String>()
        val warnings = mutableListOf<String>()
        
        // Validate Project 1
        if (config.project1Url.isEmpty()) {
            errors.add("SUPABASE_URL_PROJECT1 is not configured")
        } else if (!isValidSupabaseUrl(config.project1Url)) {
            errors.add("SUPABASE_URL_PROJECT1 has invalid format (should be https://xxx.supabase.co)")
        }
        
        if (config.project1Key.isEmpty()) {
            errors.add("SUPABASE_KEY_PROJECT1 is not configured")
        } else if (!isValidSupabaseKey(config.project1Key)) {
            warnings.add("SUPABASE_KEY_PROJECT1 may have invalid format")
        }
        
        // Validate Project 2
        if (config.project2Url.isEmpty()) {
            errors.add("SUPABASE_URL_PROJECT2 is not configured")
        } else if (!isValidSupabaseUrl(config.project2Url)) {
            errors.add("SUPABASE_URL_PROJECT2 has invalid format (should be https://xxx.supabase.co)")
        }
        
        if (config.project2Key.isEmpty()) {
            errors.add("SUPABASE_KEY_PROJECT2 is not configured")
        } else if (!isValidSupabaseKey(config.project2Key)) {
            warnings.add("SUPABASE_KEY_PROJECT2 may have invalid format")
        }
        
        // Check for duplicate projects
        if (config.project1Url.isNotEmpty() && config.project2Url.isNotEmpty() &&
            config.project1Url == config.project2Url) {
            warnings.add("Project 1 and Project 2 URLs are the same")
        }
        
        return ValidationResult(
            isValid = errors.isEmpty(),
            errors = errors,
            warnings = warnings
        )
    }
    
    private fun isValidSupabaseUrl(url: String): Boolean {
        return url.startsWith("https://") && 
               url.contains(".supabase.co") &&
               url.length > 20
    }
    
    private fun isValidSupabaseKey(key: String): Boolean {
        // Supabase keys are JWT tokens, typically start with "eyJ"
        return key.length > 50 && 
               (key.startsWith("eyJ") || key.length > 100)
    }
    
    fun getConfigurationHelp(): String {
        return """
            Supabase Configuration Help
            ==========================
            
            To configure Supabase credentials:
            
            1. Create android/local.properties file
            2. Add the following properties:
            
               SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
               SUPABASE_KEY_PROJECT1=your-project1-anon-key
               SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
               SUPABASE_KEY_PROJECT2=your-project2-anon-key
            
            3. Rebuild the project: ./gradlew clean build
            
            Where to find credentials:
            - Go to Supabase Dashboard → Settings → API
            - Copy "Project URL" for SUPABASE_URL_*
            - Copy "anon public" key for SUPABASE_KEY_*
            
            See SUPABASE_SETUP.md for detailed instructions.
        """.trimIndent()
    }
}

