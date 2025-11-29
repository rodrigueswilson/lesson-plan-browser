package com.bilingual.lessonplanner.di

import android.content.Context
import androidx.room.Room
import androidx.work.WorkManager
import com.bilingual.lessonplanner.data.local.database.AppDatabase
import com.bilingual.lessonplanner.data.local.repository.LocalPlanRepository
import com.bilingual.lessonplanner.data.remote.api.SupabaseApi
import com.bilingual.lessonplanner.data.remote.config.SupabaseClientFactory
import com.bilingual.lessonplanner.data.remote.config.SupabaseConfig
import com.bilingual.lessonplanner.data.remote.config.SupabaseConfigProvider
import com.bilingual.lessonplanner.data.remote.repository.RemotePlanRepository
import com.bilingual.lessonplanner.data.repository.PlanRepositoryImpl
import com.bilingual.lessonplanner.data.sync.BackgroundSyncWorker
import com.bilingual.lessonplanner.data.sync.NetworkAwareSyncManager
import com.bilingual.lessonplanner.data.sync.SyncManager
import com.bilingual.lessonplanner.data.datastore.UserPreferences
import com.bilingual.lessonplanner.domain.repository.PlanRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import io.github.jan.supabase.SupabaseClient
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "lesson_planner_db"
        )
            .addMigrations(AppDatabase.MIGRATION_1_2)
            .build()
    }
    
    @Provides
    @Singleton
    fun provideSupabaseConfig(@ApplicationContext context: Context): SupabaseConfig {
        return SupabaseConfigProvider.getConfig(context)
    }
    
    @Provides
    @Singleton
    fun provideSupabaseClient(config: SupabaseConfig): SupabaseClient {
        // Default to project1, will be switched based on user selection
        return SupabaseClientFactory.createClient("project1", config)
    }
    
    @Provides
    @Singleton
    fun provideSupabaseApi(client: SupabaseClient): SupabaseApi {
        return SupabaseApi(client)
    }
    
    @Provides
    @Singleton
    fun provideLocalPlanRepository(database: AppDatabase): LocalPlanRepository {
        return LocalPlanRepository(database)
    }
    
    @Provides
    @Singleton
    fun provideRemotePlanRepository(
        supabaseApi: SupabaseApi,
        config: SupabaseConfig
    ): RemotePlanRepository {
        return RemotePlanRepository(supabaseApi, config)
    }
    
    @Provides
    @Singleton
    fun provideNetworkAwareSyncManager(@ApplicationContext context: Context): NetworkAwareSyncManager {
        return NetworkAwareSyncManager(context)
    }
    
    @Provides
    @Singleton
    fun provideSyncManager(
        @ApplicationContext context: Context,
        localRepository: LocalPlanRepository,
        remoteRepository: RemotePlanRepository,
        database: AppDatabase,
        networkAwareSyncManager: NetworkAwareSyncManager
    ): SyncManager {
        return SyncManager(
            context = context,
            localRepository = localRepository,
            remoteRepository = remoteRepository,
            syncMetadataDao = database.syncMetadataDao(),
            networkAwareSyncManager = networkAwareSyncManager
        )
    }
    
    @Provides
    @Singleton
    fun providePlanRepository(
        localRepository: LocalPlanRepository,
        syncManager: SyncManager
    ): PlanRepository {
        return PlanRepositoryImpl(localRepository, syncManager)
    }
    
    @Provides
    @Singleton
    fun provideWorkManager(@ApplicationContext context: Context): WorkManager {
        return WorkManager.getInstance(context)
    }
    
    @Provides
    @Singleton
    fun provideUserPreferences(@ApplicationContext context: Context): UserPreferences {
        return UserPreferences(context)
    }
}
