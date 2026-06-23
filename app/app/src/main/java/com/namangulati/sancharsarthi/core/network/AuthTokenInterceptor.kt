package com.namangulati.sancharsarthi.core.network

import com.namangulati.sancharsarthi.core.auth.FirebaseAuthManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AuthTokenInterceptor(
    private val firebaseAuthManager: FirebaseAuthManager = FirebaseAuthManager()
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        // Always force-refresh so expired tokens (1h lifetime) don't silently block API calls
        val token = runBlocking { firebaseAuthManager.currentToken(forceRefresh = true) }
        val request = if (token.isNullOrBlank()) {
            original
        } else {
            original.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        }
        return chain.proceed(request)
    }
}
