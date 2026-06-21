package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.data.remote.dto.OfficerAssignmentsDto
import com.namangulati.sancharsarthi.data.remote.dto.OfficerLoginResponseDto
import retrofit2.http.GET
import retrofit2.http.POST

import kotlinx.serialization.Serializable

@Serializable
data class AuthMeResponseDto(
    val role: String,
    val email: String? = null,
    val firebase_uid: String
)

interface AuthApi {
    @POST("officer/login")
    suspend fun officerLogin(): OfficerLoginResponseDto

    @GET("officer/assignments")
    suspend fun officerAssignments(): OfficerAssignmentsDto

    @GET("auth/me")
    suspend fun getMe(): AuthMeResponseDto
}
