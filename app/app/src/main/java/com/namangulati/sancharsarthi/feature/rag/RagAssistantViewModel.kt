package com.namangulati.sancharsarthi.feature.rag

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RagChatRequest
import com.namangulati.sancharsarthi.core.network.RagSourceResponse
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.data.remote.RagApi
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.decodeFromJsonElement
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.ResponseBody
import java.time.Instant
import kotlin.random.Random

enum class RagMessageRole {
    User,
    Assistant,
}

data class RagChatMessage(
    val id: String,
    val role: RagMessageRole,
    val content: String,
    val createdAt: String,
    val sources: List<RagSourceResponse> = emptyList(),
    val pending: Boolean = false,
    val error: Boolean = false,
)

data class RagAssistantUiState(
    val isOpen: Boolean = false,
    val isStreaming: Boolean = false,
    val error: String? = null,
    val sessionId: String? = null,
    val messages: List<RagChatMessage> = emptyList(),
)

class RagAssistantViewModel(
    private val ragApi: RagApi = RetrofitClient.ragApi,
) : ViewModel() {
    private val _uiState = MutableStateFlow(RagAssistantUiState())
    val uiState: StateFlow<RagAssistantUiState> = _uiState.asStateFlow()

    private var streamingJob: Job? = null

    fun openPanel() {
        _uiState.update { it.copy(isOpen = true) }
    }

    fun closePanel() {
        _uiState.update { it.copy(isOpen = false) }
    }

    fun togglePanel() {
        _uiState.update { it.copy(isOpen = !it.isOpen) }
    }

    fun sendQuestion(question: String, eventId: String? = null) {
        val trimmed = question.trim()
        if (trimmed.length < 2 || _uiState.value.isStreaming) {
            return
        }

        val userMessage = RagChatMessage(
            id = createMessageId(),
            role = RagMessageRole.User,
            content = trimmed,
            createdAt = Instant.now().toString(),
        )
        val assistantId = createMessageId()
        val assistantMessage = RagChatMessage(
            id = assistantId,
            role = RagMessageRole.Assistant,
            content = "",
            createdAt = Instant.now().toString(),
            pending = true,
        )

        _uiState.update {
            it.copy(
                isOpen = true,
                isStreaming = true,
                error = null,
                messages = it.messages + userMessage + assistantMessage,
            )
        }

        streamingJob = viewModelScope.launch {
            try {
                val response = ragApi.chat(
                    RagChatRequest(
                        question = trimmed,
                        session_id = _uiState.value.sessionId,
                        event_id = eventId?.trim()?.takeIf { it.isNotBlank() },
                    )
                )

                if (!response.isSuccessful) {
                    val message = response.errorBody()?.string()?.let(::extractApiErrorMessage)
                        ?: "RAG chat failed with status ${response.code()}"
                    throw IllegalStateException(message)
                }

                val body = response.body() ?: throw IllegalStateException("Streaming response body is not available.")
                streamSseBody(body) { event ->
                    handleStreamEvent(event, assistantId)
                }
            } catch (cancelled: CancellationException) {
                return@launch
            } catch (caught: Exception) {
                val message = caught.localizedMessage ?: "RAG chat failed."
                _uiState.update {
                    it.copy(
                        error = message,
                        messages = it.messages.map { chatMessage ->
                            if (chatMessage.id == assistantId) {
                                chatMessage.copy(
                                    content = chatMessage.content.ifBlank { message },
                                    pending = false,
                                    error = true,
                                )
                            } else {
                                chatMessage
                            }
                        },
                    )
                }
            } finally {
                _uiState.update {
                    it.copy(
                        isStreaming = false,
                        messages = it.messages.map { chatMessage ->
                            if (chatMessage.id == assistantId && chatMessage.pending) {
                                chatMessage.copy(
                                    content = chatMessage.content.ifBlank { "No grounded answer was returned." },
                                    pending = false,
                                )
                            } else {
                                chatMessage
                            }
                        },
                    )
                }
                streamingJob = null
            }
        }
    }

    fun clearConversation() {
        val activeSessionId = _uiState.value.sessionId
        streamingJob?.cancel()
        streamingJob = null
        _uiState.update {
            it.copy(
                isStreaming = false,
                error = null,
                sessionId = null,
                messages = emptyList(),
            )
        }

        if (!activeSessionId.isNullOrBlank()) {
            viewModelScope.launch {
                runCatching { ragApi.deleteHistory(activeSessionId) }
            }
        }
    }

    private fun handleStreamEvent(event: RagStreamEvent, assistantId: String) {
        when (event) {
            is RagStreamEvent.Token -> {
                _uiState.update {
                    it.copy(
                        messages = it.messages.map { message ->
                            if (message.id == assistantId) {
                                message.copy(content = message.content + event.content)
                            } else {
                                message
                            }
                        },
                    )
                }
            }
            is RagStreamEvent.Done -> {
                _uiState.update {
                    it.copy(
                        sessionId = event.sessionId,
                        messages = it.messages.map { message ->
                            if (message.id == assistantId) {
                                message.copy(
                                    content = message.content.ifBlank { "No grounded answer was returned." },
                                    sources = event.sources,
                                    pending = false,
                                )
                            } else {
                                message
                            }
                        },
                    )
                }
            }
            is RagStreamEvent.Error -> {
                _uiState.update {
                    it.copy(
                        error = event.message,
                        messages = it.messages.map { message ->
                            if (message.id == assistantId) {
                                message.copy(
                                    content = message.content.ifBlank { event.message },
                                    pending = false,
                                    error = true,
                                )
                            } else {
                                message
                            }
                        },
                    )
                }
            }
        }
    }
}

private sealed class RagStreamEvent {
    data class Token(val content: String) : RagStreamEvent()
    data class Done(val sessionId: String, val sources: List<RagSourceResponse>) : RagStreamEvent()
    data class Error(val message: String) : RagStreamEvent()
}

private val ragJson = Json { ignoreUnknownKeys = true }

private fun createMessageId(): String {
    return "rag-${System.currentTimeMillis()}-${Random.nextInt().toUInt().toString(16)}"
}

private suspend fun streamSseBody(
    responseBody: ResponseBody,
    onEvent: (RagStreamEvent) -> Unit,
) {
    withContext(Dispatchers.IO) {
        responseBody.use { body ->
            body.byteStream().bufferedReader(Charsets.UTF_8).use { reader ->
                val block = StringBuilder()
                while (true) {
                    val line = reader.readLine() ?: break
                    if (line.isBlank()) {
                        parseEventBlock(block.toString())?.let(onEvent)
                        block.clear()
                    } else {
                        block.append(line).append('\n')
                    }
                }
                parseEventBlock(block.toString())?.let(onEvent)
            }
        }
    }
}

private fun parseEventBlock(block: String): RagStreamEvent? {
    val data = block
        .lineSequence()
        .filter { it.startsWith("data:") }
        .joinToString(separator = "\n") { it.removePrefix("data:").trim() }

    if (data.isBlank()) {
        return null
    }

    val payload = runCatching { ragJson.parseToJsonElement(data).jsonObject }.getOrNull() ?: return null
    return when (payload["type"]?.jsonPrimitive?.contentOrNull) {
        "token" -> RagStreamEvent.Token(payload["content"]?.jsonPrimitive?.contentOrNull.orEmpty())
        "done" -> RagStreamEvent.Done(
            sessionId = payload["session_id"]?.jsonPrimitive?.contentOrNull.orEmpty(),
            sources = payload["sources"]?.let { ragJson.decodeFromJsonElement<List<RagSourceResponse>>(it) }.orEmpty(),
        )
        "error" -> RagStreamEvent.Error(payload["message"]?.jsonPrimitive?.contentOrNull ?: "RAG chat failed.")
        else -> null
    }
}

private fun extractApiErrorMessage(body: String): String {
    return runCatching {
        val payload = ragJson.parseToJsonElement(body).jsonObject
        payload["error"]
            ?.jsonObject
            ?.get("message")
            ?.jsonPrimitive
            ?.contentOrNull
            ?: body
    }.getOrDefault(body)
}
