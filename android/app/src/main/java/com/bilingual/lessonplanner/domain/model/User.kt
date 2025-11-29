package com.bilingual.lessonplanner.domain.model

data class User(
    val id: String,
    val name: String,
    val email: String?,
    val createdAt: Long?,
    val updatedAt: Long?
)

