package com.bilingual.lessonplanner.ui.lessonmode

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.bilingual.lessonplanner.domain.model.LessonStep
import com.bilingual.lessonplanner.utils.TimerAdjustment
import kotlin.math.abs

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll

@Composable
fun TimerAdjustmentDialog(
    open: Boolean,
    onDismiss: () -> Unit,
    currentStep: LessonStep,
    currentStepIndex: Int,
    totalSteps: Int,
    currentRemainingTime: Long, // seconds
    originalDuration: Long, // seconds
    onAdjust: (TimerAdjustment) -> Unit
) {
    if (!open) return

    var pendingAdjustmentMinutes by remember { mutableIntStateOf(0) }
    val scrollState = rememberScrollState()

    // Calculate preview values
    val currentMinutes = (currentRemainingTime / 60).toInt()
    val previewMinutes = currentMinutes + pendingAdjustmentMinutes
    val previewSeconds = currentRemainingTime % 60
    val previewTotalSeconds = previewMinutes * 60 + previewSeconds

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier
                    .padding(24.dp)
                    .verticalScroll(scrollState)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Adjust Timer",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Close")
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Step Info
                Text(
                    text = "Current Step: ${currentStep.stepName} (Step ${currentStepIndex + 1} of $totalSteps)",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Stats Grid
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    StatItem(
                        label = "Original",
                        value = formatTime(originalDuration)
                    )
                    StatItem(
                        label = "Remaining",
                        value = formatTime(currentRemainingTime)
                    )
                    StatItem(
                        label = "New Time",
                        value = formatTime(previewTotalSeconds),
                        highlight = pendingAdjustmentMinutes != 0,
                        subValue = if (pendingAdjustmentMinutes != 0) {
                            "${if (pendingAdjustmentMinutes > 0) "+" else ""}$pendingAdjustmentMinutes min"
                        } else null
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Adjust Time Controls
                Text(
                    text = "Adjust Time",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Decrease Button
                    OutlinedButton(
                        onClick = { 
                            // Prevent going below 1 minute
                            if (previewMinutes > 1) {
                                pendingAdjustmentMinutes--
                            }
                        },
                        enabled = previewMinutes > 1,
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.size(64.dp),
                        contentPadding = PaddingValues(0.dp)
                    ) {
                        Icon(Icons.Default.Remove, contentDescription = "Decrease", modifier = Modifier.size(32.dp))
                    }

                    // Value
                    Column(
                        modifier = Modifier.width(120.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = previewMinutes.toString(),
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "minutes",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    // Increase Button
                    OutlinedButton(
                        onClick = { pendingAdjustmentMinutes++ },
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.size(64.dp),
                        contentPadding = PaddingValues(0.dp)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Increase", modifier = Modifier.size(32.dp))
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Other Options
                Text(
                    text = "Other Options",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = { 
                            onAdjust(TimerAdjustment.Reset)
                            onDismiss()
                        },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Reset Original")
                    }
                    
                    if (currentStepIndex < totalSteps - 1) {
                        OutlinedButton(
                            onClick = { 
                                onAdjust(TimerAdjustment.Skip(currentStepIndex + 1))
                                onDismiss()
                            },
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Default.SkipNext, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("Skip Step")
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))
                Divider()
                Spacer(modifier = Modifier.height(16.dp))

                // Warning
                Text(
                    text = "⚠️ Warning: Adjusting will affect remaining steps. Remaining steps will be recalculated proportionally.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedButton(onClick = onDismiss) {
                        Text("Cancel")
                    }
                    Spacer(Modifier.width(8.dp))
                    Button(
                        onClick = { 
                            if (pendingAdjustmentMinutes > 0) {
                                onAdjust(TimerAdjustment.Add(pendingAdjustmentMinutes))
                            } else if (pendingAdjustmentMinutes < 0) {
                                onAdjust(TimerAdjustment.Subtract(abs(pendingAdjustmentMinutes)))
                            }
                            onDismiss()
                        },
                        enabled = pendingAdjustmentMinutes != 0
                    ) {
                        Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("OK")
                    }
                }
            }
        }
    }
}

@Composable
fun StatItem(
    label: String,
    value: String,
    highlight: Boolean = false,
    subValue: String? = null
) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = if (highlight) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
        )
        if (subValue != null) {
            Text(
                text = subValue,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary
            )
        }
    }
}

private fun formatTime(seconds: Long): String {
    val mins = seconds / 60
    val secs = seconds % 60
    return "%02d:%02d".format(mins, secs)
}

