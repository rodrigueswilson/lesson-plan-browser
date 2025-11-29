package com.bilingual.lessonplanner.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bilingual.lessonplanner.data.local.database.entities.SyncMetadataEntity

@Dao
interface SyncMetadataDao {
    @Query("SELECT * FROM sync_metadata WHERE id = :id")
    suspend fun getSyncMetadata(id: String): SyncMetadataEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSyncMetadata(metadata: SyncMetadataEntity)
    
    @Query("DELETE FROM sync_metadata WHERE id = :id")
    suspend fun deleteSyncMetadata(id: String)
}

