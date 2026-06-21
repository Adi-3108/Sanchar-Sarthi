package com.namangulati.sancharsarthi.core.auth

import com.google.firebase.auth.FirebaseAuth
import kotlinx.coroutines.tasks.await

class FirebaseAuthManager(
    private val firebaseAuth: FirebaseAuth = FirebaseAuth.getInstance()
) {
    suspend fun login(email: String, password: String): FirebaseLoginResult {
        val credential = firebaseAuth.signInWithEmailAndPassword(email, password).await()
        val user = requireNotNull(credential.user)
        
        if (!user.isEmailVerified) {
            throw Exception("UNVERIFIED_EMAIL")
        }
        
        val token = user.getIdToken(false).await().token.orEmpty()
        return FirebaseLoginResult(
            uid = user.uid,
            email = user.email,
            idToken = token,
        )
    }

    suspend fun register(email: String, password: String) {
        val credential = firebaseAuth.createUserWithEmailAndPassword(email, password).await()
        val user = requireNotNull(credential.user)
        user.sendEmailVerification().await()
    }

    suspend fun resendVerificationEmail(email: String, password: String) {
        val credential = firebaseAuth.signInWithEmailAndPassword(email, password).await()
        val user = requireNotNull(credential.user)
        user.sendEmailVerification().await()
    }

    suspend fun currentToken(forceRefresh: Boolean = false): String? {
        val user = firebaseAuth.currentUser ?: return null
        return user.getIdToken(forceRefresh).await().token
    }

    fun logout() {
        firebaseAuth.signOut()
    }
}

data class FirebaseLoginResult(
    val uid: String,
    val email: String?,
    val idToken: String,
)
