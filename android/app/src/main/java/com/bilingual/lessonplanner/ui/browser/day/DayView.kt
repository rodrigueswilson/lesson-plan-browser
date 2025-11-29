package com.bilingual.lessonplanner.ui.browser.day

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.ui.browser.components.PlanCard
import com.bilingual.lessonplanner.ui.theme.ScheduleColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DayView(
    userId: String,
    day: String,
    onDayChange: (String) -> Unit,
    onLessonClick: (String, String, Int) -> Unit,
    viewModel: DayViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(userId, day) {
        viewModel.loadDaySchedule(userId, day)
    }
    
    val days = listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    val currentDayIndex = days.indexOfFirst { it.equals(day, ignoreCase = true) }
    
    Column(modifier = Modifier.fillMaxSize()) {
        // Header with Navigation
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Previous/Next Arrows & Title
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(
                    onClick = { 
                        if (currentDayIndex > 0) onDayChange(days[currentDayIndex - 1]) 
                    },
                    enabled = currentDayIndex > 0
                ) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Previous Day")
                }
                
                Text(
                    text = day,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 8.dp)
                )
                
                IconButton(
                    onClick = { 
                        if (currentDayIndex < days.size - 1) onDayChange(days[currentDayIndex + 1]) 
                    },
                    enabled = currentDayIndex < days.size - 1
                ) {
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Next Day")
                }
            }
            
            // Day Selector Buttons
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                days.forEach { d ->
                    val isSelected = d.equals(day, ignoreCase = true)
                    OutlinedButton(
                        onClick = { onDayChange(d) },
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else Color.Transparent,
                            contentColor = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.primary
                        ),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 0.dp),
                        modifier = Modifier.height(32.dp)
                    ) {
                        Text(d.take(3), fontSize = 12.sp)
                    }
                }
            }
        }
        
        Divider()
        
        // List Content
        LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(uiState.lessons) { entry ->
                Row(modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
                    // Time Column
                    Box(
                        modifier = Modifier
                            .width(80.dp)
                            .fillMaxHeight()
                            .background(Color(0xFFF9FAFB))
                            .border(BorderStroke(0.5.dp, Color.LightGray))
                            .padding(horizontal = 4.dp),
                        contentAlignment = Alignment.CenterEnd
                    ) {
                        Text(
                            text = "${entry.startTime} - ${entry.endTime}",
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontSize = 10.sp,
                                color = Color.Gray
                            ),
                            textAlign = TextAlign.End
                        )
                    }
                    
                    // Content Column
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                            .border(BorderStroke(0.5.dp, Color(0xFFE5E7EB)))
                    ) {
                        if (ScheduleColors.isNonClassPeriod(entry.subject)) {
                            NonClassPeriodCell(entry)
                        } else {
                            PlanCard(
                                scheduleEntry = entry,
                                onClick = { onLessonClick(day, entry.id, entry.slotNumber) },
                                modifier = Modifier.fillMaxSize(),
                                // TODO: Pass extra details if we fetch them (Student Goal, etc.)
                                widaObjective = null 
                            )
                        }
                    }
                }
            }
            
            if (uiState.lessons.isEmpty() && !uiState.isLoading) {
                item {
                    Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                        Text("No lessons scheduled for this day", color = Color.Gray)
                    }
                }
            }
        }
    }
}

@Composable
fun NonClassPeriodCell(entry: ScheduleEntry) {
    val colors = ScheduleColors.getSubjectColors(entry.subject, entry.grade, entry.homeroom)
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(colors.bg)
            .padding(horizontal = 12.dp, vertical = 8.dp), // More padding in Day view
        contentAlignment = Alignment.CenterStart
    ) {
        Text(
            text = entry.subject,
            style = MaterialTheme.typography.bodyMedium.copy(
                color = colors.text
            )
        )
    }
}
