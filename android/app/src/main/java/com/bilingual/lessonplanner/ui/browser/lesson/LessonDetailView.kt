package com.bilingual.lessonplanner.ui.browser.lesson

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.ui.browser.lesson.components.InstructionStepsDisplay
import com.bilingual.lessonplanner.ui.browser.lesson.components.MaterialsDisplay
import com.bilingual.lessonplanner.ui.browser.lesson.components.SentenceFramesDisplay
import com.bilingual.lessonplanner.ui.browser.lesson.components.VocabularyDisplay
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LessonDetailView(
    planId: String,
    userId: String,
    dayOfWeek: String? = null,
    slotNumber: Int? = null,
    onBack: () -> Unit,
    onStartLesson: () -> Unit,
    viewModel: LessonDetailViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(planId, userId, dayOfWeek, slotNumber) {
        viewModel.loadLessonDetail(planId, userId, dayOfWeek, slotNumber)
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Lesson Details") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
            )
        },
        floatingActionButton = {
            if (uiState.plan != null && !uiState.isLoading) {
                ExtendedFloatingActionButton(
                    onClick = onStartLesson,
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                    icon = { Icon(Icons.Default.PlayArrow, contentDescription = null) },
                    text = { Text("Start Lesson") }
                )
            }
        }
    ) { paddingValues ->
        when {
            uiState.isLoading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            uiState.error != null -> {
                Text(
                    text = "Error: ${uiState.error}",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .padding(16.dp)
                )
            }
            else -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Objectives - prefer slotData from lesson_json, otherwise show placeholder
                    uiState.slotData?.objectives?.let { objectives ->
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.primaryContainer
                            )
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "Objectives",
                                    style = MaterialTheme.typography.titleLarge,
                                    modifier = Modifier.padding(bottom = 8.dp)
                                )
                                objectives.content?.let { content ->
                                    Text(
                                        text = "Content: $content",
                                        style = MaterialTheme.typography.bodyLarge,
                                        modifier = Modifier.padding(bottom = 4.dp)
                                    )
                                }
                                objectives.language?.let { language ->
                                    Text(
                                        text = "Language: $language",
                                        style = MaterialTheme.typography.bodyLarge
                                    )
                                }
                            }
                        }
                    }
                    
                    // Vocabulary & Cognates - prefer slotData, fallback to steps
                    val vocabularyJson = uiState.slotData?.vocabulary_cognates?.let { list ->
                        Json.encodeToString(JsonArray(list.map { JsonPrimitive(it) }))
                    } ?: uiState.slotData?.vocabulary?.let { list ->
                        Json.encodeToString(JsonArray(list.map { JsonPrimitive(it) }))
                    } ?: uiState.steps.firstOrNull()?.vocabularyCognates
                    
                    if (!vocabularyJson.isNullOrBlank()) {
                        VocabularyDisplay(
                            vocabularyJson = vocabularyJson,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                    
                    // Sentence Frames - prefer slotData, fallback to steps
                    val sentenceFramesJson = uiState.slotData?.sentence_frames?.let { list ->
                        Json.encodeToString(JsonArray(list.map { JsonPrimitive(it) }))
                    } ?: uiState.steps.firstOrNull()?.sentenceFrames
                    
                    if (!sentenceFramesJson.isNullOrBlank()) {
                        SentenceFramesDisplay(
                            sentenceFramesJson = sentenceFramesJson,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                    
                    // Materials - prefer slotData, fallback to steps
                    val materialsJson = uiState.slotData?.materials_needed?.let { list ->
                        Json.encodeToString(JsonArray(list.map { JsonPrimitive(it) }))
                    } ?: uiState.steps.firstOrNull()?.materialsNeeded
                    
                    if (!materialsJson.isNullOrBlank()) {
                        MaterialsDisplay(
                            materialsJson = materialsJson,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                    
                    // Instruction Steps
                    InstructionStepsDisplay(
                        steps = uiState.steps,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}

