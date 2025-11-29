package com.bilingual.lessonplanner.data.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

object UserPreferencesKeys {
    val SELECTED_USER_ID = stringPreferencesKey("selected_user_id")
}

class UserPreferences(private val context: Context) {
    val selectedUserId: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[UserPreferencesKeys.SELECTED_USER_ID]
    }
    
    suspend fun setSelectedUserId(userId: String) {
        context.dataStore.edit { preferences ->
            preferences[UserPreferencesKeys.SELECTED_USER_ID] = userId
        }
    }
    
    suspend fun clearSelectedUserId() {
        context.dataStore.edit { preferences ->
            preferences.remove(UserPreferencesKeys.SELECTED_USER_ID)
        }
    }
}

