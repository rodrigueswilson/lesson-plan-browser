package com.bilingual.lessonplanner

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bilingual.lessonplanner.data.datastore.UserPreferences
import com.bilingual.lessonplanner.ui.browser.BrowserScreen
import com.bilingual.lessonplanner.ui.browser.lesson.LessonDetailView
import com.bilingual.lessonplanner.ui.debug.DataDiagnosticsScreen
import com.bilingual.lessonplanner.ui.lessonmode.LessonModeScreen
import com.bilingual.lessonplanner.ui.theme.BilingualLessonPlannerTheme
import com.bilingual.lessonplanner.ui.userselector.UserSelectorScreen
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            BilingualLessonPlannerTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation()
                }
            }
        }
    }
}

@Composable
fun AppNavigation() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val userPreferences = remember { UserPreferences(context) }
    val mainViewModel: MainActivityViewModel = hiltViewModel()
    val navController = rememberNavController()
    var selectedUserId by remember { mutableStateOf<String?>(null) }
    var selectedPlanId by remember { mutableStateOf<String?>(null) }
    var selectedDay by remember { mutableStateOf<String?>(null) }
    var selectedSlot by remember { mutableStateOf<Int?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    
    // Check if user is already selected
    LaunchedEffect(Unit) {
        try {
            userPreferences.selectedUserId.collect { userId ->
                selectedUserId = userId
            }
        } catch (e: Exception) {
            error = "Failed to load user preferences: ${e.message}"
            android.util.Log.e("AppNavigation", "Error loading user preferences", e)
        }
    }
    
    // Show error if any
    error?.let {
        androidx.compose.material3.Surface(
            modifier = Modifier.fillMaxSize(),
            color = androidx.compose.material3.MaterialTheme.colorScheme.errorContainer
        ) {
            androidx.compose.foundation.layout.Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
            ) {
                androidx.compose.material3.Text(
                    text = "Error",
                    style = androidx.compose.material3.MaterialTheme.typography.headlineMedium,
                    color = androidx.compose.material3.MaterialTheme.colorScheme.onErrorContainer
                )
                androidx.compose.foundation.layout.Spacer(modifier = Modifier.height(16.dp))
                androidx.compose.material3.Text(
                    text = it,
                    style = androidx.compose.material3.MaterialTheme.typography.bodyMedium,
                    color = androidx.compose.material3.MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }
        return
    }
    
    NavHost(
        navController = navController,
        startDestination = if (selectedUserId != null) "browser" else "user_selector"
    ) {
        composable("user_selector") {
            UserSelectorScreen(
                onUserSelected = {
                    navController.navigate("browser") {
                        popUpTo("user_selector") { inclusive = true }
                    }
                }
            )
        }
        
        composable("browser") {
            selectedUserId?.let { userId ->
                BrowserScreen(
                    userId = userId,
                    onDaySelected = { day ->
                        selectedDay = day
                        // No navigation needed, BrowserScreen handles view switching
                    },
                    onLessonSelected = { day, entryId, slot ->
                        selectedDay = day
                        selectedSlot = slot
                        // Resolve plan ID from schedule entry
                        CoroutineScope(Dispatchers.Main).launch {
                            val result = mainViewModel.resolvePlanId(entryId, userId, day, slot)
                            selectedPlanId = result?.planId
                            if (selectedPlanId != null) {
                                navController.navigate("lesson_detail")
                            }
                        }
                    },
                    onNavigateToDiagnostics = {
                        navController.navigate("data_diagnostics")
                    }
                )
            } ?: run {
                navController.navigate("user_selector") {
                    popUpTo("browser") { inclusive = true }
                }
            }
        }
        
        composable("lesson_detail") {
            selectedUserId?.let { userId ->
                selectedPlanId?.let { planId ->
                    LessonDetailView(
                        planId = planId,
                        userId = userId,
                        dayOfWeek = selectedDay,
                        slotNumber = selectedSlot,
                        onBack = { navController.popBackStack() },
                        onStartLesson = {
                            navController.navigate("lesson_mode")
                        }
                    )
                }
            }
        }
        
        composable("lesson_mode") {
            selectedPlanId?.let { planId ->
                selectedDay?.let { day ->
                    selectedSlot?.let { slot ->
                        LessonModeScreen(
                            planId = planId,
                            dayOfWeek = day,
                            slotNumber = slot,
                            onBack = { navController.popBackStack() }
                        )
                    }
                }
            }
        }
        
        composable("data_diagnostics") {
            // Always show diagnostic screen, even if userId is null (will show error)
            DataDiagnosticsScreen(
                userId = selectedUserId ?: "unknown",
                onBack = { 
                    if (navController.previousBackStackEntry != null) {
                        navController.popBackStack()
                    } else {
                        navController.navigate("browser") {
                            popUpTo("data_diagnostics") { inclusive = true }
                        }
                    }
                }
            )
        }
    }
}
