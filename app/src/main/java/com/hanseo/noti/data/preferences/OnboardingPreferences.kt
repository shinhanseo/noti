package com.hanseo.noti.data.preferences

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

private const val ONBOARDING_DATASTORE_NAME =
    "onboarding_preferences"

private val Context.onboardingDataStore by preferencesDataStore(
    name = ONBOARDING_DATASTORE_NAME
)

@Singleton
class OnboardingPreferences @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {
    private companion object {
        val IS_ONBOARDING_COMPLETED =
            booleanPreferencesKey("is_onboarding_completed")
    }

    val isOnboardingCompleted: Flow<Boolean> =
        context.onboardingDataStore.data
            .catch { exception ->
                if (exception is IOException) {
                    emit(emptyPreferences())
                } else {
                    throw exception
                }
            }
            .map { preferences ->
                preferences[IS_ONBOARDING_COMPLETED] ?: false
            }

    suspend fun setOnboardingCompleted(
        isCompleted: Boolean
    ) {
        context.onboardingDataStore.edit { preferences ->
            preferences[IS_ONBOARDING_COMPLETED] = isCompleted
        }
    }
}