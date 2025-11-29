package com.bilingual.lessonplanner.ui.userselector

import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BugReport
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bilingual.lessonplanner.data.remote.config.SupabaseConfigProvider
import com.bilingual.lessonplanner.ui.components.ConfigErrorDisplay
import com.bilingual.lessonplanner.utils.ConfigValidator

@Composable
fun UserSelectorScreen(
    onUserSelected: () -> Unit,
    viewModel: UserSelectorViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    
    // Check Supabase configuration
    val config = SupabaseConfigProvider.getConfig(context)
    val validation = ConfigValidator.validate(config)
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Select User",
            style = MaterialTheme.typography.headlineLarge,
            modifier = Modifier.padding(bottom = 32.dp)
        )
        
        // Show configuration errors if any
        if (!validation.isValid) {
            ConfigErrorDisplay(
                message = validation.errors.joinToString("\n") + 
                    "\n\nPlease configure Supabase credentials in android/local.properties. " +
                    "See SUPABASE_SETUP.md for instructions.",
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp)
            )
        }
        
        when {
            uiState.isLoading -> {
                CircularProgressIndicator()
            }
            uiState.error != null -> {
                Text(
                    text = "Error: ${uiState.error}",
                    color = MaterialTheme.colorScheme.error,
                    textAlign = TextAlign.Center
                )
            }
            uiState.users.isEmpty() -> {
                Text(
                    text = "No users available",
                    textAlign = TextAlign.Center
                )
            }
            else -> {
                LazyColumn(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(uiState.users) { user ->
                        UserItem(
                            user = user,
                            onClick = {
                                viewModel.selectUser(user)
                                onUserSelected()
                            }
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UserItem(
    user: com.bilingual.lessonplanner.domain.model.User,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = user.name,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(16.dp)
        )
    }
}

