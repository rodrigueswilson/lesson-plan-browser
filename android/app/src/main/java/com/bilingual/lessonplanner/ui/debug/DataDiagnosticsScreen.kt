package com.bilingual.lessonplanner.ui.debug

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.ui.debug.DataDiagnosticsViewModel
import com.bilingual.lessonplanner.utils.Logger

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DataDiagnosticsScreen(
    userId: String,
    onBack: () -> Unit,
    viewModel: DataDiagnosticsViewModel = hiltViewModel()
) {
    // Always render something immediately - even if userId is invalid
    // This helps debug if the screen is being called at all
    var diagnosticData by remember { mutableStateOf<DiagnosticData?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    // Only load data if userId is valid
    LaunchedEffect(userId) {
        if (userId.isBlank() || userId == "unknown") {
            isLoading = false
            error = "No user ID provided"
            return@LaunchedEffect
        }
        
        try {
            isLoading = true
            error = null
            diagnosticData = null
            diagnosticData = viewModel.getDiagnosticData(userId)
        } catch (e: Exception) {
            error = "${e.javaClass.simpleName}: ${e.message ?: "Unknown error"}"
            android.util.Log.e("DataDiagnostics", "Error loading diagnostic data", e)
        } finally {
            isLoading = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Data Diagnostics") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
        ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Debug: Always show this to confirm screen is loading
            Text(
                text = "Data Diagnostics Screen",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.primary
            )
            
            Text(
                text = "User ID: $userId",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Divider()

            if (isLoading) {
                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (error != null) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Text(
                        text = "Error: $error",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer
                    )
                }
            } else if (diagnosticData != null) {
                val data = diagnosticData!!
                
                // Show message if all counts are zero
                if (data.userCount == 0 && data.planCount == 0 && data.scheduleCount == 0 && data.stepCount == 0) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                    ) {
                        Column(Modifier.padding(16.dp)) {
                            Text(
                                text = "No Data Found",
                                style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(Modifier.height(8.dp))
                            Text(
                                text = "All tables appear to be empty. This could mean:\n" +
                                        "1. Supabase tables have no data\n" +
                                        "2. RLS policies are blocking access\n" +
                                        "3. Network connection issue\n\n" +
                                        "Check logs for detailed error messages.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                }
                
                // Summary
                Card {
                    Column(Modifier.padding(16.dp)) {
                        Text("Summary", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(8.dp))
                        DataRow("Users", data.userCount.toString())
                        DataRow("Weekly Plans", data.planCount.toString())
                        DataRow("Schedule Entries", data.scheduleCount.toString())
                        DataRow("Lesson Steps", data.stepCount.toString())
                    }
                }

                // Sample Plan
                if (data.samplePlan != null) {
                    Card {
                        Column(Modifier.padding(16.dp)) {
                            Text("Sample Plan", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            DataRow("ID", data.samplePlan.id)
                            DataRow("Week Of", data.samplePlan.weekOf ?: "N/A")
                            DataRow("Status", data.samplePlan.status)
                            data.samplePlan.lessonJson?.let { json ->
                                DataRow("Has lesson_json", "Yes (${json.length} chars)")
                                Spacer(Modifier.height(8.dp))
                                Text(
                                    text = "lesson_json Preview (first 200 chars):",
                                    style = MaterialTheme.typography.bodySmall
                                )
                                Text(
                                    text = json.take(200),
                                    style = MaterialTheme.typography.bodySmall,
                                    modifier = Modifier.padding(top = 4.dp)
                                )
                            } ?: run {
                                DataRow("Has lesson_json", "No")
                            }
                        }
                    }
                }

                // Sample Steps
                if (data.sampleSteps.isNotEmpty()) {
                    Card {
                        Column(Modifier.padding(16.dp)) {
                            Text("Sample Lesson Steps", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            data.sampleSteps.forEach { step ->
                                Text(
                                    text = "Step ${step.stepNumber}: ${step.stepName} (${step.durationMinutes} min)",
                                    style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.padding(vertical = 4.dp)
                                )
                            }
                        }
                    }
                }

                // Sample Schedule
                if (data.sampleSchedule.isNotEmpty()) {
                    Card {
                        Column(Modifier.padding(16.dp)) {
                            Text("Sample Schedule Entries", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            data.sampleSchedule.forEach { entry ->
                                Text(
                                    text = "${entry.dayOfWeek}: ${entry.subject} (${entry.startTime}-${entry.endTime})",
                                    style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.padding(vertical = 4.dp)
                                )
                            }
                        }
                    }
                }
            } else {
                // No data, no error, not loading - shouldn't happen, but show message
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Text(
                        text = "No diagnostic data available. Please check logs.",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun DataRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
    }
}


