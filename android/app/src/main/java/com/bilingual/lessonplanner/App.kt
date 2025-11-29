package com.bilingual.lessonplanner

import android.app.Application
import android.util.Log
import com.bilingual.lessonplanner.data.remote.config.SupabaseConfigProvider
import com.bilingual.lessonplanner.utils.ConfigValidator
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class App : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Validate Supabase configuration on app startup
        val config = SupabaseConfigProvider.getConfig(this)
        val validation = ConfigValidator.validate(config)
        
        if (!validation.isValid) {
            Log.e("App", "Supabase configuration errors:")
            validation.errors.forEach { error ->
                Log.e("App", "  - $error")
            }
            Log.e("App", ConfigValidator.getConfigurationHelp())
        } else {
            Log.d("App", "Supabase configuration validated successfully")
            if (validation.warnings.isNotEmpty()) {
                validation.warnings.forEach { warning ->
                    Log.w("App", "Configuration warning: $warning")
                }
            }
        }
    }
}

