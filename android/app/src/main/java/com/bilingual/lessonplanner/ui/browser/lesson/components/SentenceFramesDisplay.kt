package com.bilingual.lessonplanner.ui.browser.lesson.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.bilingual.lessonplanner.ui.browser.components.ExpandableCard
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.jsonPrimitive

@Composable
fun SentenceFramesDisplay(
    sentenceFramesJson: String?,
    modifier: Modifier = Modifier
) {
    if (sentenceFramesJson.isNullOrBlank()) return
    
    val items = remember(sentenceFramesJson) {
        runCatching {
            val json = Json { ignoreUnknownKeys = true }
            val jsonElement = json.parseToJsonElement(sentenceFramesJson)
            if (jsonElement is JsonArray) {
                jsonElement.map { it.jsonPrimitive.content }
            } else {
                listOf(sentenceFramesJson)
            }
        }.getOrElse { listOf(sentenceFramesJson) }
    }
    
    ExpandableCard(
        title = "Sentence Frames",
        initiallyExpanded = false,
        modifier = modifier
    ) {
        Column {
            items.forEach { item ->
                Text(
                    text = "• $item",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(vertical = 4.dp)
                )
            }
        }
    }
}
