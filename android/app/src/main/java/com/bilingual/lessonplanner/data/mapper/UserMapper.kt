package com.bilingual.lessonplanner.data.mapper

import com.bilingual.lessonplanner.data.local.database.entities.UserEntity
import com.bilingual.lessonplanner.domain.model.User

fun UserEntity.toDomain(): User {
    return User(
        id = id,
        name = name,
        email = email,
        createdAt = createdAt,
        updatedAt = updatedAt
    )
}

fun User.toEntity(): UserEntity {
    return UserEntity(
        id = id,
        name = name,
        email = email,
        createdAt = createdAt,
        updatedAt = updatedAt
    )
}

