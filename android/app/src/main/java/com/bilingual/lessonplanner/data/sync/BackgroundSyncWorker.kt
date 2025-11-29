package com.bilingual.lessonplanner.data.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.bilingual.lessonplanner.data.datastore.UserPreferences
import com.bilingual.lessonplanner.utils.Logger
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first
import java.util.concurrent.TimeUnit

@HiltWorker
class BackgroundSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val syncManager: SyncManager,
    private val userPreferences: UserPreferences
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            Logger.d("Background sync started")
            
            // Sync users first (always needed)
            try {
                syncManager.syncUsers()
                Logger.d("Users synced successfully")
            } catch (e: Exception) {
                Logger.w("Failed to sync users, continuing with other syncs", e)
            }
            
            // Get current user from preferences and sync their data
            val selectedUserId = userPreferences.selectedUserId.first()
            if (selectedUserId != null) {
                try {
                    syncManager.syncPlans(selectedUserId)
                    Logger.d("Plans synced successfully for user: $selectedUserId")
                } catch (e: Exception) {
                    Logger.w("Failed to sync plans for user: $selectedUserId", e)
                }
                
                try {
                    syncManager.syncSchedule(selectedUserId)
                    Logger.d("Schedule synced successfully for user: $selectedUserId")
                } catch (e: Exception) {
                    Logger.w("Failed to sync schedule for user: $selectedUserId", e)
                }
            } else {
                Logger.d("No user selected, skipping user-specific syncs")
            }
            
            Logger.d("Background sync completed successfully")
            Result.success()
        } catch (e: Exception) {
            Logger.e("Background sync failed", e)
            // Retry with exponential backoff (WorkManager handles this)
            // Limit retries to avoid battery drain
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Logger.w("Background sync failed after $runAttemptCount attempts, giving up")
                Result.failure()
            }
        }
    }
    
    companion object {
        fun schedulePeriodicSync(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.UNMETERED) // WiFi only
                .build()
            
            val syncWork = PeriodicWorkRequestBuilder<BackgroundSyncWorker>(
                4, TimeUnit.HOURS
            )
                .setConstraints(constraints)
                .build()
            
            WorkManager.getInstance(context).enqueue(syncWork)
        }
    }
}

