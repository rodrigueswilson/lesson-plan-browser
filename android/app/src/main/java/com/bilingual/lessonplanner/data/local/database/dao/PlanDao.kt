package com.bilingual.lessonplanner.data.local.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bilingual.lessonplanner.data.local.database.entities.WeeklyPlanEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PlanDao {
    @Query("SELECT * FROM weekly_plans WHERE userId = :userId ORDER BY weekOf DESC")
    fun getPlansByUserId(userId: String): Flow<List<WeeklyPlanEntity>>
    
    @Query("SELECT * FROM weekly_plans WHERE id = :planId")
    suspend fun getPlanById(planId: String): WeeklyPlanEntity?
    
    @Query("SELECT * FROM weekly_plans WHERE id = :planId AND userId = :userId")
    suspend fun getPlanByIdAndUserId(planId: String, userId: String): WeeklyPlanEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPlan(plan: WeeklyPlanEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPlans(plans: List<WeeklyPlanEntity>)
    
    @Query("DELETE FROM weekly_plans WHERE id = :planId")
    suspend fun deletePlan(planId: String)
    
    @Query("DELETE FROM weekly_plans WHERE userId = :userId")
    suspend fun deletePlansByUserId(userId: String)
}

