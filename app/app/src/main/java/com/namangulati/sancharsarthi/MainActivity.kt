package com.namangulati.sancharsarthi

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.design.EventFlowTheme
import com.namangulati.sancharsarthi.feature.common.NoInternetScreen
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationViewModel
import com.namangulati.sancharsarthi.navigation.EventFlowApp
import com.namangulati.sancharsarthi.util.NetworkMonitor

class MainActivity : ComponentActivity() {
    private lateinit var networkMonitor: NetworkMonitor

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        networkMonitor = NetworkMonitor(this)

        enableEdgeToEdge()
        setContent {
            EventFlowTheme {
                val isConnected by networkMonitor.isConnected.collectAsState()

                if (isConnected) {
                    val viewModel: PlatformFoundationViewModel = viewModel(
                        factory = PlatformFoundationViewModel.Factory,
                    )
                    EventFlowApp(viewModel = viewModel)
                } else {
                    NoInternetScreen(
                        onTryAgain = { networkMonitor.checkConnectivity() }
                    )
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::networkMonitor.isInitialized) {
            networkMonitor.unregister()
        }
    }
}
