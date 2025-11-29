package com.bilingual.lessonplanner.ui.lessonmode

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.layout
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.ui.browser.lesson.components.MaterialsDisplay
import com.bilingual.lessonplanner.ui.browser.lesson.components.SentenceFramesDisplay
import com.bilingual.lessonplanner.ui.browser.lesson.components.VocabularyDisplay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LessonModeScreen(
    planId: String,
    dayOfWeek: String,
    slotNumber: Int,
    onBack: () -> Unit,
    viewModel: LessonModeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var showAdjustDialog by remember { mutableStateOf(false) }
    
    // Collapsible Layout State
    var isTimelineExpanded by remember { mutableStateOf(true) }
    var isResourcesExpanded by remember { mutableStateOf(true) }

    LaunchedEffect(planId, dayOfWeek, slotNumber) {
        viewModel.initializeSession(planId, dayOfWeek, slotNumber)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text("Lesson Mode")
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (uiState.error != null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Error: ${uiState.error}", color = MaterialTheme.colorScheme.error)
            }
        } else {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
            ) {
                val currentIndex = uiState.session?.currentStepIndex ?: 0
                val currentAdjustedStep = uiState.adjustedSteps.getOrNull(currentIndex)
                val originalDuration = currentAdjustedStep?.originalDurationSeconds ?: 
                                      ((uiState.currentStep?.durationMinutes ?: 0) * 60L)
                
                // Calculate dynamic weights
                val timelineWeight = if (isTimelineExpanded) 0.2f else 0.05f
                val resourcesWeight = if (isResourcesExpanded) 0.2f else 0.05f
                val contentWeight = 1f - timelineWeight - resourcesWeight
                
                // Column 1: Timeline with Timer
                TimelineColumn(
                    steps = uiState.steps,
                    currentStepIndex = currentIndex,
                    onStepClick = { index -> viewModel.jumpToStep(index) },
                    
                    // Timer Props
                    totalDurationSeconds = (uiState.currentStep?.durationMinutes ?: 0) * 60L,
                    elapsedSeconds = uiState.session?.stepElapsedSeconds ?: 0L,
                    isRunning = !(uiState.session?.isPaused ?: true),
                    onStart = { viewModel.toggleTimer() },
                    onPause = { viewModel.toggleTimer() },
                    onReset = { viewModel.resetStepTimer() },
                    onAdjust = { showAdjustDialog = true },
                    originalDurationSeconds = originalDuration,
                    
                    // Collapse Props
                    isExpanded = isTimelineExpanded,
                    onToggleExpand = { isTimelineExpanded = !isTimelineExpanded },
                    
                    modifier = Modifier
                        .weight(timelineWeight)
                        .fillMaxHeight()
                        .background(MaterialTheme.colorScheme.surface)
                        .padding(if (isTimelineExpanded) 8.dp else 4.dp)
                )
                
                Divider(modifier = Modifier.fillMaxHeight().width(1.dp))

                // Column 2: Main Content
                ContentColumn(
                    step = uiState.currentStep,
                    modifier = Modifier
                        .weight(contentWeight)
                        .fillMaxHeight()
                        .padding(16.dp)
                )

                Divider(modifier = Modifier.fillMaxHeight().width(1.dp))

                // Column 3: Resources
                ResourcesColumn(
                    step = uiState.currentStep,
                    
                    // Collapse Props
                    isExpanded = isResourcesExpanded,
                    onToggleExpand = { isResourcesExpanded = !isResourcesExpanded },
                    
                    modifier = Modifier
                        .weight(resourcesWeight)
                        .fillMaxHeight()
                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f))
                        .padding(if (isResourcesExpanded) 8.dp else 4.dp)
                )
            }
            
            // Timer Adjustment Dialog
            if (showAdjustDialog && uiState.currentStep != null) {
                val currentIndex = uiState.session?.currentStepIndex ?: 0
                val currentAdjustedStep = uiState.adjustedSteps.getOrNull(currentIndex)
                val originalDur = currentAdjustedStep?.originalDurationSeconds ?: 
                                 ((uiState.currentStep!!.durationMinutes) * 60L)
                val totalDur = (uiState.currentStep!!.durationMinutes) * 60L
                val elapsed = uiState.session?.stepElapsedSeconds ?: 0L
                
                TimerAdjustmentDialog(
                    open = showAdjustDialog,
                    onDismiss = { showAdjustDialog = false },
                    currentStep = uiState.currentStep!!,
                    currentStepIndex = currentIndex,
                    totalSteps = uiState.steps.size,
                    currentRemainingTime = (totalDur - elapsed).coerceAtLeast(0),
                    originalDuration = originalDur,
                    onAdjust = { adjustment ->
                        viewModel.handleTimerAdjust(adjustment)
                    }
                )
            }
        }
    }
}

@Composable
fun TimelineColumn(
    steps: List<LessonStep>,
    currentStepIndex: Int,
    onStepClick: (Int) -> Unit,
    
    totalDurationSeconds: Long,
    elapsedSeconds: Long,
    isRunning: Boolean,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onReset: () -> Unit,
    onAdjust: () -> Unit,
    originalDurationSeconds: Long? = null,
    
    isExpanded: Boolean,
    onToggleExpand: () -> Unit,
    
    modifier: Modifier = Modifier
) {
    if (!isExpanded) {
        // Collapsed State: Show expand button
        Column(
            modifier = modifier,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            IconButton(onClick = onToggleExpand) {
                Icon(Icons.Default.ChevronRight, contentDescription = "Expand Timeline")
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Timeline",
                style = MaterialTheme.typography.labelSmall,
                modifier = Modifier.vertical()
            )
        }
        return
    }

    // Expanded State
    LazyColumn(modifier = modifier) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Lesson Pacing",
                    style = MaterialTheme.typography.titleMedium
                )
                IconButton(onClick = onToggleExpand, modifier = Modifier.size(24.dp)) {
                    Icon(Icons.Default.ChevronLeft, contentDescription = "Collapse Timeline")
                }
            }
        }
        
        itemsIndexed(steps) { index, step ->
            val isCurrent = index == currentStepIndex
            val isCompleted = index < currentStepIndex
            
            if (isCurrent) {
                // Current Step Card with Timer
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                        .clickable { onStepClick(index) },
                    border = androidx.compose.foundation.BorderStroke(2.dp, MaterialTheme.colorScheme.primary)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(
                            text = "Step ${step.stepNumber}: ${step.stepName}",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Current Step",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        TimerDisplay(
                            totalDurationSeconds = totalDurationSeconds,
                            elapsedSeconds = elapsedSeconds,
                            isRunning = isRunning,
                            onStart = onStart,
                            onPause = onPause,
                            onReset = onReset,
                            onAdjust = onAdjust,
                            originalDurationSeconds = originalDurationSeconds,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            } else {
                // Other Steps (Completed or Upcoming)
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = if (isCompleted) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp)
                        .clickable { onStepClick(index) },
                    border = if (isCompleted) null else androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Row(
                        modifier = Modifier.padding(8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Step ${step.stepNumber}: ${step.stepName}",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = if (isCompleted) FontWeight.Normal else FontWeight.Medium,
                                color = if (isCompleted) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Text(
                                text = "${step.durationMinutes} min",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        
                        if (isCompleted) {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = "Completed",
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ContentColumn(
    step: LessonStep?,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.verticalScroll(rememberScrollState())) {
        if (step != null) {
            Text(
                text = step.stepName,
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(
                        text = "Instructions",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(bottom = 8.dp),
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = step.displayContent,
                        style = MaterialTheme.typography.bodyLarge,
                        lineHeight = 24.sp,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
            
            if (!step.hiddenContent.isNullOrEmpty()) {
                Spacer(modifier = Modifier.height(16.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(
                            text = "Teacher Notes",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                        Text(
                            text = step.hiddenContent,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                    }
                }
            }
        } else {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Select a step to begin", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun ResourcesColumn(
    step: LessonStep?,
    isExpanded: Boolean,
    onToggleExpand: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!isExpanded) {
        Column(
            modifier = modifier,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            IconButton(onClick = onToggleExpand) {
                Icon(Icons.Default.ChevronLeft, contentDescription = "Expand Resources")
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Resources",
                style = MaterialTheme.typography.labelSmall,
                modifier = Modifier.vertical()
            )
        }
        return
    }

    Column(modifier = modifier.verticalScroll(rememberScrollState())) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Resources",
                style = MaterialTheme.typography.titleMedium
            )
            IconButton(onClick = onToggleExpand, modifier = Modifier.size(24.dp)) {
                Icon(Icons.Default.ChevronRight, contentDescription = "Collapse Resources")
            }
        }
        
        if (step != null) {
            if (!step.vocabularyCognates.isNullOrEmpty()) {
                VocabularyDisplay(vocabularyJson = step.vocabularyCognates)
                Spacer(Modifier.height(16.dp))
            }
            
            if (!step.sentenceFrames.isNullOrEmpty()) {
                SentenceFramesDisplay(sentenceFramesJson = step.sentenceFrames)
                Spacer(Modifier.height(16.dp))
            }
            
            if (!step.materialsNeeded.isNullOrEmpty()) {
                MaterialsDisplay(materialsJson = step.materialsNeeded)
            }
        }
    }
}

// Helper modifier for vertical text rotation
fun Modifier.vertical() = this.then(
    layout { measurable, constraints ->
        val placeable = measurable.measure(constraints)
        layout(placeable.height, placeable.width) {
            placeable.place(
                x = -(placeable.width / 2 - placeable.height / 2),
                y = -(placeable.height / 2 - placeable.width / 2)
            )
        }
    }.rotate(-90f)
)
