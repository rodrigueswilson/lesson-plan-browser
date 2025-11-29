package com.bilingual.lessonplanner.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bilingual.lessonplanner.data.local.database.entities.ScheduleEntryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ScheduleDao {
    @Query("SELECT * FROM schedule_entries WHERE userId = :userId AND isActive = 1 ORDER BY dayOfWeek, startTime ASC")
    fun getScheduleByUserId(userId: String): Flow<List<ScheduleEntryEntity>>
    
    @Query("SELECT * FROM schedule_entries WHERE userId = :userId AND dayOfWeek = :dayOfWeek AND isActive = 1 ORDER BY startTime ASC")
    fun getScheduleByUserIdAndDay(userId: String, dayOfWeek: String): Flow<List<ScheduleEntryEntity>>
    
    @Query("SELECT * FROM schedule_entries WHERE id = :entryId")
    suspend fun getEntryById(entryId: String): ScheduleEntryEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntry(entry: ScheduleEntryEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntries(entries: List<ScheduleEntryEntity>)
    
    @Query("DELETE FROM schedule_entries WHERE id = :entryId")
    suspend fun deleteEntry(entryId: String)
    
    @Query("DELETE FROM schedule_entries WHERE userId = :userId")
    suspend fun deleteEntriesByUserId(userId: String)
}

