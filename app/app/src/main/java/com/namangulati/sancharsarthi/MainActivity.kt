package com.namangulati.sancharsarthi

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.design.EventFlowTheme
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationViewModel
import com.namangulati.sancharsarthi.navigation.EventFlowApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()
        setContent {
            EventFlowTheme {
                val viewModel: PlatformFoundationViewModel = viewModel(
                    factory = PlatformFoundationViewModel.Factory,
                )
                EventFlowApp(viewModel = viewModel)
            }
        }
    }
}

