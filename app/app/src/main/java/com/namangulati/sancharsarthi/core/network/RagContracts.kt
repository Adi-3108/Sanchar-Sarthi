package com.namangulati.sancharsarthi.core.network

import kotlinx.serialization.Serializable

@Serializable
data class RagChatRequest(
    val question: String,
    val session_id: String? = null,
    val event_id: String? = null,
)

@Serializable
data class RagSourceResponse(
    val chunk_type: String,
    val source_id: String,
    val similarity: Double,
)

@Serializable
data class RagHistoryMessageResponse(
    val role: String,
    val content: String,
    val created_at: String,
    val sources: List<RagSourceResponse> = emptyList(),
)

@Serializable
data class RagHistoryResponse(
    val session_id: String,
    val role: String,
    val expires_at: String,
    val messages: List<RagHistoryMessageResponse> = emptyList(),
)

@Serializable
data class RagDeleteHistoryResponse(
    val status: String,
    val session_id: String,
)
