package com.bilingual.lessonplanner.ui.browser

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BugReport
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Today
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.ui.browser.components.WeekSelector
import com.bilingual.lessonplanner.ui.browser.day.DayView
import com.bilingual.lessonplanner.ui.browser.week.WeekView

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BrowserScreen(
    userId: String,
    onViewModeChange: (ViewMode) -> Unit = {},
    onDaySelected: (String) -> Unit = {},
    onLessonSelected: (String, String, Int) -> Unit = { _, _, _ -> },
    onNavigateToDiagnostics: () -> Unit = {},
    viewModel: BrowserViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val availableWeeks by viewModel.availableWeeks.collectAsState()
    
    LaunchedEffect(userId) {
        viewModel.loadWeeksForUser(userId)
    }
    
    // Handle back button press to navigate up the hierarchy
    BackHandler(enabled = uiState.currentViewMode != ViewMode.WEEK) {
        if (uiState.currentViewMode == ViewMode.DAY) {
            viewModel.setViewMode(ViewMode.WEEK)
            onViewModeChange(ViewMode.WEEK)
        } else if (uiState.currentViewMode == ViewMode.LESSON) {
            viewModel.setViewMode(ViewMode.DAY)
            onViewModeChange(ViewMode.DAY)
        }
    }
    
    Scaffold(
        topBar = {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.surface,
                shadowElevation = 2.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 24.dp, vertical = 12.dp), // Match PC px-6 py-3
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Left: View Mode Buttons
                    Row(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant)
                            .padding(4.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        ViewModeButton(
                            text = "Week",
                            isSelected = uiState.currentViewMode == ViewMode.WEEK,
                            onClick = {
                                viewModel.setViewMode(ViewMode.WEEK)
                                onViewModeChange(ViewMode.WEEK)
                            }
                        )
                        ViewModeButton(
                            text = "Day",
                            isSelected = uiState.currentViewMode == ViewMode.DAY,
                            onClick = {
                                viewModel.setViewMode(ViewMode.DAY)
                                onViewModeChange(ViewMode.DAY)
                            }
                        )
                        ViewModeButton(
                            text = "Lesson",
                            isSelected = uiState.currentViewMode == ViewMode.LESSON,
                            enabled = false, 
                            onClick = {
                                // viewModel.setViewMode(ViewMode.LESSON)
                                // onViewModeChange(ViewMode.LESSON)
                            }
                        )
                    }

                    // Right: Week Selector, Today Button & Refresh
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        if (availableWeeks.isNotEmpty()) {
                            Text(
                                text = "Week:",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            WeekSelector(
                                weeks = availableWeeks,
                                selectedWeek = uiState.selectedWeek,
                                onWeekSelected = { week ->
                                    viewModel.setSelectedWeek(week)
                                },
                                modifier = Modifier.width(200.dp)
                            )
                            
                            // Today Button
                            TextButton(
                                onClick = { viewModel.jumpToToday() },
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)
                            ) {
                                Icon(
                                    Icons.Default.Today,
                                    contentDescription = "Jump to Today",
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(Modifier.width(4.dp))
                                Text("Today", style = MaterialTheme.typography.labelMedium)
                            }
                        }
                        
                        // Diagnostics Button (Debug)
                        IconButton(onClick = onNavigateToDiagnostics) {
                            Icon(Icons.Default.BugReport, contentDescription = "Data Diagnostics")
                        }
                        
                        if (uiState.isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            IconButton(onClick = { viewModel.refresh(userId) }) {
                                Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                            }
                        }
                    }
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // Loading State
            if (uiState.isLoading && availableWeeks.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        CircularProgressIndicator()
                        Text(
                            text = "Loading lesson plans...",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            // Empty State: No weeks available
            else if (availableWeeks.isEmpty() && !uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "No weeks available",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = "Generate a lesson plan to get started",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else {
                when (uiState.currentViewMode) {
                    ViewMode.WEEK -> {
                        WeekView(
                            userId = userId,
                            onLessonClick = { day, entryId, slot ->
                                onLessonSelected(day, entryId, slot)
                            },
                            onDayClick = { day ->
                                 viewModel.setViewMode(ViewMode.DAY)
                                 viewModel.setSelectedDay(day)
                                 onViewModeChange(ViewMode.DAY)
                                 onDaySelected(day)
                            }
                        )
                    }
                    ViewMode.DAY -> {
                        DayView(
                            userId = userId,
                            day = uiState.selectedDay ?: "Monday", // Fallback
                            onDayChange = { newDay ->
                                viewModel.setSelectedDay(newDay)
                                onDaySelected(newDay)
                            },
                            onLessonClick = { day, entryId, slot ->
                                onLessonSelected(day, entryId, slot)
                            }
                        )
                    }
                    ViewMode.LESSON -> {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Text(
                                    text = "Select a lesson",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = "Choose a lesson from Week or Day view",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ViewModeButton(
    text: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.background else Color.Transparent,
            contentColor = if (isSelected) MaterialTheme.colorScheme.onBackground else MaterialTheme.colorScheme.onSurfaceVariant,
            disabledContainerColor = Color.Transparent,
            disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.38f)
        ),
        shape = RoundedCornerShape(4.dp),
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
        elevation = if (isSelected) ButtonDefaults.buttonElevation(defaultElevation = 2.dp) else null,
        modifier = Modifier.height(32.dp)
    ) {
        Text(text = text, style = MaterialTheme.typography.labelMedium)
    }
}
