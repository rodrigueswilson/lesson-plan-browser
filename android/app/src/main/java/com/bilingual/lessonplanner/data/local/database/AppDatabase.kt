package com.bilingual.lessonplanner.data.local.database

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.bilingual.lessonplanner.data.local.database.dao.LessonStepDao
import com.bilingual.lessonplanner.data.local.database.dao.PlanDao
import com.bilingual.lessonplanner.data.local.database.dao.ScheduleDao
import com.bilingual.lessonplanner.data.local.database.dao.SyncMetadataDao
import com.bilingual.lessonplanner.data.local.database.dao.UserDao
import com.bilingual.lessonplanner.data.local.database.entities.LessonStepEntity
import com.bilingual.lessonplanner.data.local.database.entities.ScheduleEntryEntity
import com.bilingual.lessonplanner.data.local.database.entities.SyncMetadataEntity
import com.bilingual.lessonplanner.data.local.database.entities.UserEntity
import com.bilingual.lessonplanner.data.local.database.entities.WeeklyPlanEntity

@Database(
    entities = [
        WeeklyPlanEntity::class,
        LessonStepEntity::class,
        ScheduleEntryEntity::class,
        UserEntity::class,
        SyncMetadataEntity::class
    ],
    version = 2,
    exportSchema = false
)
@TypeConverters
abstract class AppDatabase : RoomDatabase() {
    abstract fun planDao(): PlanDao
    abstract fun lessonStepDao(): LessonStepDao
    abstract fun scheduleDao(): ScheduleDao
    abstract fun userDao(): UserDao
    abstract fun syncMetadataDao(): SyncMetadataDao
    
    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                // Add indices for performance optimization
                // Note: Room uses property names (camelCase) as column names by default
                database.execSQL("CREATE INDEX IF NOT EXISTS index_weekly_plans_userId ON weekly_plans(userId)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_weekly_plans_weekOf ON weekly_plans(weekOf)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_weekly_plans_updatedAt ON weekly_plans(updatedAt)")
                
                database.execSQL("CREATE INDEX IF NOT EXISTS index_schedule_entries_userId ON schedule_entries(userId)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_schedule_entries_dayOfWeek ON schedule_entries(dayOfWeek)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_schedule_entries_userId_dayOfWeek ON schedule_entries(userId, dayOfWeek)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_schedule_entries_isActive ON schedule_entries(isActive)")
                
                database.execSQL("CREATE INDEX IF NOT EXISTS index_lesson_steps_lessonPlanId ON lesson_steps(lessonPlanId)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_lesson_steps_dayOfWeek ON lesson_steps(dayOfWeek)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_lesson_steps_lessonPlanId_dayOfWeek_slotNumber ON lesson_steps(lessonPlanId, dayOfWeek, slotNumber)")
            }
        }
    }
}

