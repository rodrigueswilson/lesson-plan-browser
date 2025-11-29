package com.bilingual.lessonplanner.ui.browser.week

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.ui.browser.components.PlanCard
import com.bilingual.lessonplanner.ui.theme.ScheduleColors

@Composable
fun WeekView(
    userId: String,
    onLessonClick: (String, String, Int) -> Unit, // day, entryId, slot
    onDayClick: (String) -> Unit = {},
    viewModel: WeekViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(userId) {
        viewModel.loadWeekSchedule(userId)
    }
    
    val days = listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    
    // Combine all lessons to find unique time slots
    val allLessons = remember(uiState) {
        uiState.mondayLessons + uiState.tuesdayLessons + uiState.wednesdayLessons + 
        uiState.thursdayLessons + uiState.fridayLessons
    }
    
    val timeSlots = remember(allLessons) {
        allLessons
            .map { "${it.startTime}-${it.endTime}" }
            .distinct()
            .sorted()
    }
    
    Column(modifier = Modifier.fillMaxSize()) {
        // Header Row
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(40.dp)
                .border(BorderStroke(0.5.dp, Color.LightGray))
        ) {
            // Time Header
            Box(
                modifier = Modifier
                    .width(80.dp)
                    .fillMaxHeight()
                    .border(BorderStroke(0.5.dp, Color.LightGray)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Time",
                    style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold)
                )
            }
            
            // Day Headers
            days.forEach { day ->
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .border(BorderStroke(0.5.dp, Color.LightGray))
                        .clickable { onDayClick(day) },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = day,
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold)
                    )
                }
            }
        }
        
        // Grid Content
        LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(timeSlots) { timeSlot ->
                val (start, end) = timeSlot.split("-")
                
                // Find max row height needed (e.g. based on content) 
                // For now, fixed height or intrinsic could work, but let's let Compose layout handles it naturally 
                // by using IntrinsicSize.Min on Row is expensive in LazyColumn.
                // We'll use a fixed height for non-class periods and flexible for lessons if possible,
                // or just let the PlanCard define height.
                // To simplify, we render a Row where cells expand.
                
                Row(modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
                    // Time Column
                    Box(
                        modifier = Modifier
                            .width(80.dp)
                            .fillMaxHeight()
                            .background(Color(0xFFF9FAFB)) // Light gray
                            .border(BorderStroke(0.5.dp, Color.LightGray))
                            .padding(horizontal = 4.dp),
                        contentAlignment = Alignment.CenterEnd
                    ) {
                        Text(
                            text = "$start - $end",
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontSize = 10.sp,
                                color = Color.Gray
                            ),
                            textAlign = TextAlign.End
                        )
                    }
                    
                    // Days Columns
                    days.forEach { day ->
                        val lessonsForDay = when(day) {
                            "Monday" -> uiState.mondayLessons
                            "Tuesday" -> uiState.tuesdayLessons
                            "Wednesday" -> uiState.wednesdayLessons
                            "Thursday" -> uiState.thursdayLessons
                            "Friday" -> uiState.fridayLessons
                            else -> emptyList()
                        }
                        
                        val entry = lessonsForDay.find { it.startTime == start && it.endTime == end }
                        
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxHeight()
                                .border(BorderStroke(0.5.dp, Color(0xFFE5E7EB))) // border-gray-200
                        ) {
                            if (entry != null) {
                                if (ScheduleColors.isNonClassPeriod(entry.subject)) {
                                    NonClassPeriodCell(entry)
                                } else {
                                    PlanCard(
                                        scheduleEntry = entry,
                                        onClick = { onLessonClick(day, entry.id, entry.slotNumber) },
                                        modifier = Modifier.fillMaxSize()
                                    )
                                }
                            }
                        }
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
            .padding(vertical = 4.dp, horizontal = 2.dp),
        contentAlignment = Alignment.CenterStart
    ) {
        Text(
            text = entry.subject,
            style = MaterialTheme.typography.bodySmall.copy(
                fontSize = 10.sp,
                color = colors.text
            ),
            maxLines = 1
        )
    }
}
