package com.namangulati.sancharsarthi.core.network

data class ApiEnvironment(
    val localEmulatorBaseUrl: String,
    val transportRule: String,
    val forbiddenLinks: List<String>,
)

