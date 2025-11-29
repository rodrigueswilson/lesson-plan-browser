package com.bilingual.lessonplanner.data.remote.config

import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.realtime.Realtime
import io.ktor.client.engine.android.Android

object SupabaseClientFactory {
    fun createClient(project: String, config: SupabaseConfig): SupabaseClient {
        val (url, key) = when (project) {
            "project1" -> config.project1Url to config.project1Key
            "project2" -> config.project2Url to config.project2Key
            else -> throw IllegalArgumentException("Unknown project: $project")
        }
        
        if (url.isEmpty() || key.isEmpty()) {
            throw IllegalStateException(
                "Supabase credentials not configured for $project. " +
                "Please set SUPABASE_URL_PROJECT1, SUPABASE_KEY_PROJECT1, " +
                "SUPABASE_URL_PROJECT2, and SUPABASE_KEY_PROJECT2 in local.properties. " +
                "See SUPABASE_SETUP.md for instructions."
            )
        }
        
        return createSupabaseClient(
            supabaseUrl = url,
            supabaseKey = key
        ) {
            install(Postgrest)
            install(Realtime)
            httpEngine = Android.create()
        }
    }
    
    fun createClientForUser(userId: String, config: SupabaseConfig): SupabaseClient {
        val project = SupabaseConfigProvider.getUserProjectMapping(userId)
        return createClient(project, config)
    }
}

