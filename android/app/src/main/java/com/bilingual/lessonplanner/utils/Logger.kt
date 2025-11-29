package com.bilingual.lessonplanner.utils

import android.util.Log

object Logger {
    private const val TAG = "LessonPlanner"
    private const val DEBUG = true // Set to false in production
    
    fun d(message: String, throwable: Throwable? = null) {
        if (DEBUG) {
            if (throwable != null) {
                Log.d(TAG, message, throwable)
            } else {
                Log.d(TAG, message)
            }
        }
    }
    
    fun i(message: String, throwable: Throwable? = null) {
        if (throwable != null) {
            Log.i(TAG, message, throwable)
        } else {
            Log.i(TAG, message)
        }
    }
    
    fun w(message: String, throwable: Throwable? = null) {
        if (throwable != null) {
            Log.w(TAG, message, throwable)
        } else {
            Log.w(TAG, message)
        }
    }
    
    fun e(message: String, throwable: Throwable? = null) {
        if (throwable != null) {
            Log.e(TAG, message, throwable)
        } else {
            Log.e(TAG, message)
        }
    }
}

