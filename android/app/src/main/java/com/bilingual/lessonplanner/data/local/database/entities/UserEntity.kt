package com.bilingual.lessonplanner.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey
    val id: String,
    val name: String,
    val email: String?,
    val createdAt: Long?,
    val updatedAt: Long?
)

