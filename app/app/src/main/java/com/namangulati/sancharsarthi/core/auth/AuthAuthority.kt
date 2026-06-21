package com.namangulati.sancharsarthi.core.auth

data class AuthAuthority(
    val identityProvider: String,
    val finalAuthority: String,
    val notes: List<String>,
)

