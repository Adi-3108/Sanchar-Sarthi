package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.network.RagChatRequest
import com.namangulati.sancharsarthi.core.network.RagDeleteHistoryResponse
import com.namangulati.sancharsarthi.core.network.RagHistoryResponse
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Streaming

interface RagApi {
    @Streaming
    @POST("rag/chat")
    suspend fun chat(@Body request: RagChatRequest): Response<ResponseBody>

    @GET("rag/history/{sessionId}")
    suspend fun getHistory(@Path("sessionId") sessionId: String): RagHistoryResponse

    @DELETE("rag/history/{sessionId}")
    suspend fun deleteHistory(@Path("sessionId") sessionId: String): RagDeleteHistoryResponse
}
