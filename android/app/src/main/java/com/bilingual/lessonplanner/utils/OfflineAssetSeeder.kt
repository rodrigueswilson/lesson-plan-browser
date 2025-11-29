package com.bilingual.lessonplanner.utils

import android.content.Context
import android.util.Log
import java.io.File
import java.io.IOException

object OfflineAssetSeeder {
    private const val TAG = "OfflineAssetSeeder"
    private const val LESSON_PLAN_ASSET_ROOT = "lesson-plans"

    /**
     * Copies pre-bundled lesson JSON files from the APK assets into
     * the internal storage cache used by the shared lesson API
     * (files/lesson-plans/<userId>/<weekToken>__<planId>.json).
     */
    fun seedLessonPlanCache(context: Context) {
        runCatching {
            val assetManager = context.assets
            val destinationRoot = File(context.filesDir, LESSON_PLAN_ASSET_ROOT)
            if (!destinationRoot.exists()) {
                destinationRoot.mkdirs()
            }

            val userFolders = assetManager.list(LESSON_PLAN_ASSET_ROOT) ?: emptyArray()
            if (userFolders.isEmpty()) {
                Log.d(TAG, "No lesson plan assets packaged under $LESSON_PLAN_ASSET_ROOT")
                return
            }

            for (userFolder in userFolders) {
                val assetPath = "$LESSON_PLAN_ASSET_ROOT/$userFolder"
                val lessonFiles = assetManager.list(assetPath) ?: continue
                if (lessonFiles.isEmpty()) continue

                val userDestination = File(destinationRoot, userFolder)
                if (!userDestination.exists()) {
                    userDestination.mkdirs()
                }

                for (lessonFile in lessonFiles) {
                    copyAssetFile(
                        context = context,
                        assetPath = "$assetPath/$lessonFile",
                        destinationFile = File(userDestination, lessonFile)
                    )
                }
            }

            Log.d(TAG, "Seeded lesson plan cache to ${destinationRoot.absolutePath}")
        }.onFailure { error ->
            Log.e(TAG, "Failed to seed lesson plan cache", error)
        }
    }

    private fun copyAssetFile(context: Context, assetPath: String, destinationFile: File) {
        try {
            context.assets.open(assetPath).use { input ->
                destinationFile.parentFile?.mkdirs()
                destinationFile.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
        } catch (io: IOException) {
            Log.e(TAG, "Failed to copy asset $assetPath → ${destinationFile.absolutePath}", io)
        }
    }
}

