package com.namangulati.sancharsarthi.core.network

import com.namangulati.sancharsarthi.data.remote.AdminApi
import com.namangulati.sancharsarthi.data.remote.AnalyticsApi
import com.namangulati.sancharsarthi.data.remote.AuthApi
import com.namangulati.sancharsarthi.data.remote.FoundationApi
import com.namangulati.sancharsarthi.data.remote.MapApi
import com.namangulati.sancharsarthi.data.remote.ReportApi
import com.namangulati.sancharsarthi.data.remote.OfficerApi
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType

object RetrofitClient {
    private val BASE_URL = "${com.namangulati.sancharsarthi.BuildConfig.BACKEND_BASE_URL}/api/"

    private val json = Json { ignoreUnknownKeys = true }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(AuthTokenInterceptor())
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    val authApi: AuthApi = retrofit.create(AuthApi::class.java)
    val reportApi: ReportApi = retrofit.create(ReportApi::class.java)
    val foundationApi: FoundationApi = retrofit.create(FoundationApi::class.java)
    val adminApi: AdminApi = retrofit.create(AdminApi::class.java)
    val mapApi: MapApi = retrofit.create(MapApi::class.java)
    val analyticsApi: AnalyticsApi = retrofit.create(AnalyticsApi::class.java)
    val officerApi: OfficerApi = retrofit.create(OfficerApi::class.java)
}
