package com.namangulati.sancharsarthi.feature.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val loading: Boolean = false,
    val error: String? = null,
    val isSignUp: Boolean = false,
    val isUnverified: Boolean = false,
    val resendSuccess: Boolean = false,
    val selectedRole: com.namangulati.sancharsarthi.core.session.AccessLevel = com.namangulati.sancharsarthi.core.session.AccessLevel.Admin,
)

@Composable
fun LoginScreen(
    state: LoginUiState,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onLoginClick: () -> Unit,
    onToggleMode: () -> Unit,
    onResendVerification: () -> Unit,
    onRoleChange: (com.namangulati.sancharsarthi.core.session.AccessLevel) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        com.namangulati.sancharsarthi.core.translation.AutoTranslatedText("Sanchar Sarthi", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(20.dp))
        OutlinedTextField(
            value = state.email,
            onValueChange = onEmailChange,
            label = { com.namangulati.sancharsarthi.core.translation.AutoTranslatedText("Email") }
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = state.password,
            onValueChange = onPasswordChange,
            label = { com.namangulati.sancharsarthi.core.translation.AutoTranslatedText("Password") },
            visualTransformation = PasswordVisualTransformation(),
        )
        if (state.error != null) {
            Spacer(Modifier.height(8.dp))
            com.namangulati.sancharsarthi.core.translation.AutoTranslatedText(
                text = state.error, 
                color = if (state.resendSuccess) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
            )
        }
        Spacer(Modifier.height(12.dp))
        var expanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
        @OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)
        androidx.compose.material3.ExposedDropdownMenuBox(
            expanded = expanded,
            onExpandedChange = { expanded = !expanded }
        ) {
            OutlinedTextField(
                value = state.selectedRole.displayName,
                onValueChange = {},
                readOnly = true,
                label = { com.namangulati.sancharsarthi.core.translation.AutoTranslatedText("UI role hint") },
                trailingIcon = { androidx.compose.material3.ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                modifier = Modifier.fillMaxWidth().menuAnchor(androidx.compose.material3.MenuAnchorType.PrimaryNotEditable, true),
                colors = androidx.compose.material3.ExposedDropdownMenuDefaults.outlinedTextFieldColors()
            )
            ExposedDropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false }
            ) {
                com.namangulati.sancharsarthi.core.session.AccessLevel.entries.filter { it != com.namangulati.sancharsarthi.core.session.AccessLevel.PublicCitizen }.forEach { role ->
                    androidx.compose.material3.DropdownMenuItem(
                        text = { com.namangulati.sancharsarthi.core.translation.AutoTranslatedText(role.displayName) },
                        onClick = {
                            onRoleChange(role)
                            expanded = false
                        }
                    )
                }
            }
        }
        Spacer(Modifier.height(20.dp))
        Button(onClick = onLoginClick, enabled = !state.loading) {
            com.namangulati.sancharsarthi.core.translation.AutoTranslatedText(
                if (state.loading) (if (state.isSignUp) "Creating account..." else "Signing in...") 
                else (if (state.isSignUp) "Create Account" else "Sign In")
            )
        }
        TextButton(onClick = onToggleMode) {
            com.namangulati.sancharsarthi.core.translation.AutoTranslatedText(
                if (state.isSignUp) "Already have an account? Sign in" else "Don't have an account? Sign up"
            )
        }
        if (state.isUnverified && !state.resendSuccess) {
            TextButton(onClick = onResendVerification, enabled = !state.loading) {
                com.namangulati.sancharsarthi.core.translation.AutoTranslatedText("Resend Verification Email")
            }
        }
    }
}
