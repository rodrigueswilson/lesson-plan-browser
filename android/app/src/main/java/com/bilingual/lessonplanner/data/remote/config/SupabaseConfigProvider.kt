package com.bilingual.lessonplanner.data.remote.config

import android.content.Context
import java.util.Properties
import java.io.File
import java.io.FileInputStream

object SupabaseConfigProvider {
    private var cachedConfig: SupabaseConfig? = null
    
    /**
     * Get Supabase configuration.
     * 
     * Priority order:
     * 1. BuildConfig (if set in build.gradle.kts from local.properties)
     * 2. local.properties file (root or app-level)
     * 3. Default empty values (will cause connection errors - user must configure)
     */
    fun getConfig(context: Context? = null): SupabaseConfig {
        if (cachedConfig != null) {
            return cachedConfig!!
        }
        
        // Try BuildConfig first (set in build.gradle.kts from local.properties)
        val buildConfigUrl1 = try {
            val field = com.bilingual.lessonplanner.BuildConfig::class.java.getField("SUPABASE_URL_PROJECT1")
            field.get(null) as? String ?: ""
        } catch (e: Exception) {
            ""
        }
        
        val buildConfigKey1 = try {
            val field = com.bilingual.lessonplanner.BuildConfig::class.java.getField("SUPABASE_KEY_PROJECT1")
            field.get(null) as? String ?: ""
        } catch (e: Exception) {
            ""
        }
        
        val buildConfigUrl2 = try {
            val field = com.bilingual.lessonplanner.BuildConfig::class.java.getField("SUPABASE_URL_PROJECT2")
            field.get(null) as? String ?: ""
        } catch (e: Exception) {
            ""
        }
        
        val buildConfigKey2 = try {
            val field = com.bilingual.lessonplanner.BuildConfig::class.java.getField("SUPABASE_KEY_PROJECT2")
            field.get(null) as? String ?: ""
        } catch (e: Exception) {
            ""
        }
        
        // If BuildConfig has values, use them
        if (buildConfigUrl1.isNotEmpty() && buildConfigKey1.isNotEmpty() &&
            buildConfigUrl2.isNotEmpty() && buildConfigKey2.isNotEmpty()) {
            cachedConfig = SupabaseConfig(
                project1Url = buildConfigUrl1,
                project1Key = buildConfigKey1,
                project2Url = buildConfigUrl2,
                project2Key = buildConfigKey2
            )
            return cachedConfig!!
        }
        
        // Try local.properties files
        val properties = Properties()
        
        // Try app-level local.properties first
        val appLocalPropertiesFile = File("app/local.properties")
        if (appLocalPropertiesFile.exists() && appLocalPropertiesFile.isFile) {
            try {
                FileInputStream(appLocalPropertiesFile).use { properties.load(it) }
            } catch (e: Exception) {
                // Continue to next option
            }
        }
        
        // Try root-level local.properties
        val rootLocalPropertiesFile = File("local.properties")
        if (rootLocalPropertiesFile.exists() && rootLocalPropertiesFile.isFile) {
            try {
                FileInputStream(rootLocalPropertiesFile).use { 
                    val rootProps = Properties()
                    rootProps.load(it)
                    // Merge with app-level properties (app-level takes precedence)
                    rootProps.forEach { key, value ->
                        if (!properties.containsKey(key)) {
                            properties[key] = value
                        }
                    }
                }
            } catch (e: Exception) {
                // Continue
            }
        }
        
        // Try context-based path (for runtime)
        context?.let { ctx ->
            try {
                val contextLocalProperties = File(ctx.filesDir.parentFile, "local.properties")
                if (contextLocalProperties.exists() && contextLocalProperties.isFile) {
                    FileInputStream(contextLocalProperties).use {
                        val contextProps = Properties()
                        contextProps.load(it)
                        contextProps.forEach { key, value ->
                            if (!properties.containsKey(key)) {
                                properties[key] = value
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                // Continue
            }
        }
        
        // Extract values from properties
        val url1 = properties.getProperty("SUPABASE_URL_PROJECT1", "").trim()
        val key1 = properties.getProperty("SUPABASE_KEY_PROJECT1", "").trim()
        val url2 = properties.getProperty("SUPABASE_URL_PROJECT2", "").trim()
        val key2 = properties.getProperty("SUPABASE_KEY_PROJECT2", "").trim()
        
        if (url1.isNotEmpty() && key1.isNotEmpty() && url2.isNotEmpty() && key2.isNotEmpty()) {
            cachedConfig = SupabaseConfig(
                project1Url = url1,
                project1Key = key1,
                project2Url = url2,
                project2Key = key2
            )
            return cachedConfig!!
        }
        
        // Default: empty values (user must configure)
        cachedConfig = SupabaseConfig(
            project1Url = "",
            project1Key = "",
            project2Url = "",
            project2Key = ""
        )
        
        return cachedConfig!!
    }
    
    /**
     * Clear cached config (useful for testing or reconfiguration)
     */
    fun clearCache() {
        cachedConfig = null
    }
    
    /**
     * Map user ID to Supabase project (project1 or project2).
     * This should match the backend logic.
     */
    fun getUserProjectMapping(userId: String): String {
        return when {
            userId.contains("wilson", ignoreCase = true) -> "project1"
            userId.contains("daniela", ignoreCase = true) -> "project2"
            else -> "project1" // Default
        }
    }
}
