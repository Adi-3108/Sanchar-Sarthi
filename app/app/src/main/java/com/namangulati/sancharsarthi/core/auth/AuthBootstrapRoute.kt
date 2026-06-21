package com.namangulati.sancharsarthi.core.auth

import com.namangulati.sancharsarthi.core.session.AccessLevel

data class AuthBootstrapRoute(
    val accessLevel: AccessLevel,
    val method: String,
    val path: String?,
    val tokenRequired: Boolean,
    val purpose: String,
)

data class AuthBootstrapPolicy(
    val routes: List<AuthBootstrapRoute>,
    val rules: List<String>,
)
