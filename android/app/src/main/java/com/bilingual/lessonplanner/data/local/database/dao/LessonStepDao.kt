package com.bilingual.lessonplanner.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bilingual.lessonplanner.data.local.database.entities.LessonStepEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface LessonStepDao {
    @Query("SELECT * FROM lesson_steps WHERE lessonPlanId = :planId ORDER BY stepNumber ASC")
    fun getStepsByPlanId(planId: String): Flow<List<LessonStepEntity>>
    
    @Query("SELECT * FROM lesson_steps WHERE lessonPlanId = :planId AND dayOfWeek = :dayOfWeek ORDER BY stepNumber ASC")
    fun getStepsByPlanIdAndDay(planId: String, dayOfWeek: String): Flow<List<LessonStepEntity>>
    
    @Query("SELECT * FROM lesson_steps WHERE lessonPlanId = :planId AND dayOfWeek = :dayOfWeek AND slotNumber = :slotNumber ORDER BY stepNumber ASC")
    fun getStepsByPlanIdDayAndSlot(planId: String, dayOfWeek: String, slotNumber: Int): Flow<List<LessonStepEntity>>
    
    @Query("SELECT * FROM lesson_steps WHERE id = :stepId")
    suspend fun getStepById(stepId: String): LessonStepEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertStep(step: LessonStepEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSteps(steps: List<LessonStepEntity>)
    
    @Query("DELETE FROM lesson_steps WHERE id = :stepId")
    suspend fun deleteStep(stepId: String)
    
    @Query("DELETE FROM lesson_steps WHERE lessonPlanId = :planId")
    suspend fun deleteStepsByPlanId(planId: String)
}

