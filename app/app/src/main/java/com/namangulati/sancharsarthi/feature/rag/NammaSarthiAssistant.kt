package com.namangulati.sancharsarthi.feature.rag

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Send
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.namangulati.sancharsarthi.R
import com.namangulati.sancharsarthi.core.network.RagSourceResponse
import com.namangulati.sancharsarthi.core.session.AccessLevel
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

private data class SuggestedQuestion(
    val label: String,
    val question: String,
)

@Composable
fun NammaSarthiAssistantOverlay(
    state: RagAssistantUiState,
    accessLevel: AccessLevel,
    modifier: Modifier = Modifier,
    onToggle: () -> Unit,
    onClose: () -> Unit,
    onSend: (String) -> Unit,
    onClear: () -> Unit,
) {
    BoxWithConstraints(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.BottomEnd,
    ) {
        val panelWidthModifier = if (maxWidth < 520.dp) {
            Modifier.fillMaxWidth()
        } else {
            Modifier.width(430.dp)
        }
        val panelMaxHeight = (maxHeight - 32.dp).coerceAtLeast(360.dp).coerceAtMost(680.dp)

        if (state.isOpen) {
            AssistantPanel(
                state = state,
                accessLevel = accessLevel,
                onClose = onClose,
                onSend = onSend,
                onClear = onClear,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp)
                    .then(panelWidthModifier)
                    .heightIn(min = 360.dp, max = panelMaxHeight),
            )
        } else {
            AssistantBubble(
                onClick = onToggle,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(20.dp),
            )
        }
    }
}

@Composable
private fun AssistantBubble(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        modifier = modifier
            .size(76.dp)
            .border(2.dp, Color(0xFF2563EB), CircleShape),
        shape = CircleShape,
        color = Color.White,
        shadowElevation = 12.dp,
    ) {
        Image(
            painter = painterResource(id = R.drawable.namma_sarthi),
            contentDescription = "Ask Namma Sarthi",
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxSize()
                .clip(CircleShape),
        )
    }
}

@Composable
private fun AssistantPanel(
    state: RagAssistantUiState,
    accessLevel: AccessLevel,
    onClose: () -> Unit,
    onSend: (String) -> Unit,
    onClear: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var draft by rememberSaveable { mutableStateOf("") }
    val messagesListState = rememberLazyListState()
    val lastMessage = state.messages.lastOrNull()

    LaunchedEffect(state.messages.size, lastMessage?.content?.length) {
        if (state.messages.isNotEmpty()) {
            messagesListState.scrollToItem(state.messages.lastIndex)
        }
    }

    Card(
        modifier = modifier.defaultMinSize(minHeight = 360.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        elevation = CardDefaults.cardElevation(defaultElevation = 12.dp),
    ) {
        Column(modifier = Modifier.fillMaxHeight()) {
            AssistantHeader(
                accessLevel = accessLevel,
                sessionActive = !state.sessionId.isNullOrBlank(),
                onClose = onClose,
            )

            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .background(MaterialTheme.colorScheme.background.copy(alpha = 0.45f)),
                state = messagesListState,
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 14.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (state.messages.isEmpty()) {
                    item {
                        AssistantEmptyState(
                            accessLevel = accessLevel,
                            disabled = state.isStreaming,
                            onSuggestionClick = { question ->
                                draft = ""
                                onSend(question)
                            },
                        )
                    }
                }

                items(state.messages, key = { it.id }) { message ->
                    ChatBubble(message = message)
                }
            }

            AssistantFooter(
                draft = draft,
                isStreaming = state.isStreaming,
                error = state.error,
                canClear = state.messages.isNotEmpty() || !state.sessionId.isNullOrBlank(),
                onDraftChange = { draft = it.take(1200) },
                onClear = onClear,
                onSubmit = {
                    val question = draft.trim()
                    if (question.isNotBlank()) {
                        draft = ""
                        onSend(question)
                    }
                },
            )
        }
    }
}

@Composable
private fun AssistantHeader(
    accessLevel: AccessLevel,
    sessionActive: Boolean,
    onClose: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(horizontal = 18.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.Top,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Image(
                painter = painterResource(id = R.drawable.namma_sarthi),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant, CircleShape),
            )
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Namma Sarthi Copilot",
                    color = Color(0xFF2563EB),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.sp,
                )
                Text(
                    text = "Namma Sarthi AI Assistant",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.ExtraBold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = accessNote(accessLevel),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 3,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            IconButton(onClick = onClose, modifier = Modifier.size(40.dp)) {
                Icon(Icons.Outlined.Close, contentDescription = "Close assistant")
            }
        }

        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item {
                AssistantMetaChip(text = "Role ${accessLevel.displayName}")
            }
            if (sessionActive) {
                item {
                    AssistantMetaChip(text = "Session active", accent = true)
                }
            }
        }
    }
}

@Composable
private fun AssistantMetaChip(
    text: String,
    accent: Boolean = false,
) {
    Surface(
        shape = RoundedCornerShape(100.dp),
        color = if (accent) Color(0xFFE8F7EF) else MaterialTheme.colorScheme.surfaceVariant,
        border = BorderStroke(1.dp, if (accent) Color(0xFFB7E4C7) else MaterialTheme.colorScheme.outlineVariant),
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            color = if (accent) Color(0xFF047857) else MaterialTheme.colorScheme.onSurfaceVariant,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun AssistantEmptyState(
    accessLevel: AccessLevel,
    disabled: Boolean,
    onSuggestionClick: (String) -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        shape = RoundedCornerShape(18.dp),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
                Icon(
                    Icons.Outlined.SupportAgent,
                    contentDescription = null,
                    tint = Color(0xFF2563EB),
                    modifier = Modifier.size(28.dp),
                )
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "Hello, I am Namma Sarthi.",
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Text(
                        text = "Ask me about active incidents, similar event memory, recommendations, hotspot risk, or public-safe summaries.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(suggestedQuestions(accessLevel)) { suggestion ->
                    AssistChip(
                        enabled = !disabled,
                        onClick = { onSuggestionClick(suggestion.question) },
                        label = {
                            Text(
                                text = suggestion.label,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun ChatBubble(message: RagChatMessage) {
    val isAssistant = message.role == RagMessageRole.Assistant
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isAssistant) Arrangement.Start else Arrangement.End,
    ) {
        Card(
            modifier = Modifier.widthIn(max = 340.dp),
            colors = CardDefaults.cardColors(
                containerColor = if (isAssistant) MaterialTheme.colorScheme.surface else MaterialTheme.colorScheme.primary,
            ),
            border = if (isAssistant) BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant) else null,
            shape = RoundedCornerShape(
                topStart = 18.dp,
                topEnd = 18.dp,
                bottomEnd = if (isAssistant) 18.dp else 4.dp,
                bottomStart = if (isAssistant) 4.dp else 18.dp,
            ),
        ) {
            Column(
                modifier = Modifier.padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = if (isAssistant) "Namma Sarthi" else "You",
                        color = if (isAssistant) Color(0xFF2563EB) else MaterialTheme.colorScheme.onPrimary,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        text = formatMessageTime(message.createdAt),
                        color = if (isAssistant) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.72f),
                        fontSize = 11.sp,
                    )
                }

                Text(
                    text = message.content.ifBlank { if (message.pending) "Thinking through live data..." else "No response yet." },
                    color = if (isAssistant) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onPrimary,
                    style = MaterialTheme.typography.bodyMedium,
                )

                if (message.pending) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                }

                if (message.error) {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Outlined.ErrorOutline,
                            contentDescription = null,
                            tint = Color(0xFFE11D48),
                            modifier = Modifier.size(16.dp),
                        )
                        Text(
                            text = "The assistant could not complete this answer cleanly.",
                            color = Color(0xFFE11D48),
                            style = MaterialTheme.typography.labelSmall,
                        )
                    }
                }

                if (isAssistant) {
                    SourceList(sources = message.sources)
                }
            }
        }
    }
}

@Composable
private fun SourceList(sources: List<RagSourceResponse>) {
    if (sources.isEmpty()) {
        return
    }

    var expanded by rememberSaveable { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        TextButton(
            onClick = { expanded = !expanded },
            contentPadding = PaddingValues(horizontal = 0.dp, vertical = 0.dp),
        ) {
            Icon(Icons.Outlined.Info, contentDescription = null, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("${sources.size} grounded sources")
        }

        if (expanded) {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(sources) { source ->
                    SourceChip(source = source)
                }
            }
        }
    }
}

@Composable
private fun SourceChip(source: RagSourceResponse) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp)) {
            Text(
                text = source.chunk_type.replace('_', ' ').uppercase(),
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
            )
            Text(
                text = source.source_id,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.widthIn(max = 170.dp),
            )
            Text(
                text = "${(source.similarity * 100).toInt()}% match",
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun AssistantFooter(
    draft: String,
    isStreaming: Boolean,
    error: String?,
    canClear: Boolean,
    onDraftChange: (String) -> Unit,
    onClear: () -> Unit,
    onSubmit: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (!error.isNullOrBlank()) {
            Text(
                text = error,
                color = Color(0xFFE11D48),
                style = MaterialTheme.typography.bodySmall,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
        }

        OutlinedTextField(
            value = draft,
            onValueChange = onDraftChange,
            modifier = Modifier.fillMaxWidth(),
            minLines = 2,
            maxLines = 4,
            enabled = !isStreaming,
            shape = RoundedCornerShape(18.dp),
            placeholder = {
                Text("Ask about current traffic, hotspots, or response plans...")
            },
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedButton(
                onClick = onClear,
                enabled = canClear,
                shape = RoundedCornerShape(100.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
            ) {
                Icon(Icons.Outlined.DeleteOutline, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Clear")
            }

            Button(
                onClick = onSubmit,
                enabled = !isStreaming && draft.trim().length >= 2,
                shape = RoundedCornerShape(100.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB), contentColor = Color.White),
            ) {
                Icon(Icons.Outlined.Send, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(if (isStreaming) "Streaming" else "Send")
            }
        }
    }
}

private fun suggestedQuestions(accessLevel: AccessLevel): List<SuggestedQuestion> {
    val publicQuestions = listOf(
        SuggestedQuestion("Active alerts", "What active traffic issues should the public know about right now?"),
        SuggestedQuestion("Reporting help", "How should a citizen submit a useful traffic or congestion report?"),
        SuggestedQuestion("Nearby pattern", "What kinds of public traffic issues are being reported most often today?"),
    )
    val operatorQuestions = listOf(
        SuggestedQuestion("Current status", "Summarize the latest operational status across active events."),
        SuggestedQuestion("Response plan", "What are the latest manpower and diversion recommendations across active events?"),
        SuggestedQuestion("Similar history", "Which historical event patterns are most relevant for current congestion management?"),
    )
    val adminQuestions = listOf(
        SuggestedQuestion("Model posture", "Summarize the current model, hotspot, and index posture for admins."),
        SuggestedQuestion("Audit trail", "What recent admin or control-room actions are visible in the operational audit trail?"),
    )

    return when (accessLevel) {
        AccessLevel.Admin -> operatorQuestions + adminQuestions
        AccessLevel.ControlRoom,
        AccessLevel.PoliceOfficer -> operatorQuestions
        AccessLevel.PublicCitizen,
        AccessLevel.Citizen -> publicQuestions
    }
}

private fun accessNote(accessLevel: AccessLevel): String {
    return when (accessLevel) {
        AccessLevel.Admin -> "Admin answers can include internal operations, audit, model, and after-action sources."
        AccessLevel.ControlRoom,
        AccessLevel.PoliceOfficer -> "Operational answers stay grounded in control-room data, live updates, hotspots, and stored plans."
        AccessLevel.PublicCitizen,
        AccessLevel.Citizen -> "Public answers stay grounded in citizen-visible reports and public-safe summaries only."
    }
}

private val messageTimeFormatter: DateTimeFormatter = DateTimeFormatter
    .ofPattern("HH:mm")
    .withZone(ZoneId.systemDefault())

private fun formatMessageTime(value: String): String {
    return runCatching { messageTimeFormatter.format(Instant.parse(value)) }.getOrDefault("")
}
