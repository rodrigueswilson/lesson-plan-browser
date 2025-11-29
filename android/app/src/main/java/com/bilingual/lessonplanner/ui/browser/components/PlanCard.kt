package com.bilingual.lessonplanner.ui.browser.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.bilingual.lessonplanner.domain.model.ScheduleEntry
import com.bilingual.lessonplanner.ui.theme.ScheduleColors
import com.bilingual.lessonplanner.ui.theme.SubjectColor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlanCard(
    scheduleEntry: ScheduleEntry,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    widaObjective: String? = null
) {
    val colors = ScheduleColors.getSubjectColors(
        scheduleEntry.subject,
        scheduleEntry.grade,
        scheduleEntry.homeroom
    )

    Card(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(0.dp),
        colors = CardDefaults.cardColors(
            containerColor = colors.bg
        ),
        border = BorderStroke(1.dp, colors.border)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp)
        ) {
            Text(
                text = scheduleEntry.subject,
                style = MaterialTheme.typography.titleSmall.copy(
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 12.sp,
                    lineHeight = 14.sp
                ),
                color = colors.text
            )
            
            Spacer(modifier = Modifier.height(2.dp))
            
            if (scheduleEntry.grade != null) {
                Text(
                    text = "Grade ${scheduleEntry.grade}",
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontSize = 10.sp,
                        lineHeight = 12.sp
                    ),
                    color = colors.text.copy(alpha = 0.8f)
                )
            }
            
            if (scheduleEntry.homeroom != null) {
                Text(
                    text = scheduleEntry.homeroom,
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontSize = 10.sp,
                        lineHeight = 12.sp
                    ),
                    color = colors.text.copy(alpha = 0.8f)
                )
            }

            if (widaObjective != null) {
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = widaObjective,
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontSize = 10.sp,
                        lineHeight = 12.sp
                    ),
                    color = colors.text.copy(alpha = 0.8f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}
