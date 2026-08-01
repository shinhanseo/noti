package com.hanseo.noti.data.preferences

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.hanseo.noti.domain.importance.ImportanceSettings
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

private const val IMPORTANCE_SETTINGS_DATASTORE_NAME =
    "importance_settings"

private val Context.importanceSettingsDataStore by preferencesDataStore(
    name = IMPORTANCE_SETTINGS_DATASTORE_NAME
)

@Singleton
class ImportanceSettingsPreferences @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {
    private companion object {
        val IMPORTANT_APP_PACKAGES =
            stringSetPreferencesKey(
                "important_app_packages"
            )

        val GLOBAL_IMPORTANT_KEYWORDS =
            stringSetPreferencesKey(
                "global_important_keywords"
            )
    }

    val settings: Flow<ImportanceSettings> =
        context.importanceSettingsDataStore.data
            .catch { exception ->
                if (exception is IOException) {
                    emit(emptyPreferences())
                } else {
                    throw exception
                }
            }
            .map { preferences ->
                ImportanceSettings(
                    importantApps =
                        preferences[
                            IMPORTANT_APP_PACKAGES
                        ]?.toSet() ?: emptySet(),

                    globalImportantKeywords =
                        preferences[
                            GLOBAL_IMPORTANT_KEYWORDS
                        ]?.toSet() ?: emptySet(),

                    exclusionKeywordsByPackage =
                        emptyMap()
                )
            }

    suspend fun getSettings(): ImportanceSettings {
        return settings.first()
    }

    suspend fun saveInitialSettings(
        importantAppPackages: Set<String>,
        globalImportantKeywords: Set<String>
    ) {
        val sanitizedPackages =
            importantAppPackages
                .map { packageName ->
                    packageName.trim()
                }
                .filter { packageName ->
                    packageName.isNotEmpty()
                }
                .toSet()

        val sanitizedKeywords =
            globalImportantKeywords
                .map { keyword ->
                    keyword.trim()
                }
                .filter { keyword ->
                    keyword.isNotEmpty()
                }
                .toSet()

        context.importanceSettingsDataStore.edit { preferences ->
            preferences[IMPORTANT_APP_PACKAGES] =
                sanitizedPackages

            preferences[GLOBAL_IMPORTANT_KEYWORDS] =
                sanitizedKeywords
        }
    }
}