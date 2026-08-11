package com.hanseo.noti.data.preferences

import android.content.Context
import android.net.Uri
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

        val EXCLUSION_KEYWORDS =
            stringSetPreferencesKey(
                "exclusion_keywords"
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
                        decodeExclusionKeywords(
                            preferences[EXCLUSION_KEYWORDS]
                                ?: emptySet()
                        )
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

    suspend fun updateImportantApps(
        importantAppPackages: Set<String>
    ) {
        val sanitizedPackages =
            sanitizeValues(importantAppPackages)

        context.importanceSettingsDataStore.edit { preferences ->
            preferences[IMPORTANT_APP_PACKAGES] =
                sanitizedPackages

            val currentExclusions =
                decodeExclusionKeywords(
                    preferences[EXCLUSION_KEYWORDS]
                        ?: emptySet()
                )
                    .filterKeys { packageName ->
                        packageName in sanitizedPackages
                    }

            preferences[EXCLUSION_KEYWORDS] =
                encodeExclusionKeywords(
                    currentExclusions
                )
        }
    }

    suspend fun updateGlobalImportantKeywords(
        keywords: Set<String>
    ) {
        context.importanceSettingsDataStore.edit { preferences ->
            preferences[GLOBAL_IMPORTANT_KEYWORDS] =
                sanitizeValues(keywords)
        }
    }

    suspend fun updateExclusionKeywords(
        packageName: String,
        keywords: Set<String>
    ) {
        val sanitizedPackageName =
            packageName.trim()

        if (sanitizedPackageName.isEmpty()) {
            return
        }

        context.importanceSettingsDataStore.edit { preferences ->
            val updatedExclusions =
                decodeExclusionKeywords(
                    preferences[EXCLUSION_KEYWORDS]
                        ?: emptySet()
                )
                    .toMutableMap()

            val sanitizedKeywords =
                sanitizeValues(keywords)

            if (sanitizedKeywords.isEmpty()) {
                updatedExclusions.remove(
                    sanitizedPackageName
                )
            } else {
                updatedExclusions[sanitizedPackageName] =
                    sanitizedKeywords
            }

            preferences[EXCLUSION_KEYWORDS] =
                encodeExclusionKeywords(
                    updatedExclusions
                )
        }
    }

    private fun sanitizeValues(
        values: Set<String>
    ): Set<String> {
        return values
            .map { value -> value.trim() }
            .filter { value -> value.isNotEmpty() }
            .toSet()
    }

    private fun encodeExclusionKeywords(
        exclusions: Map<String, Set<String>>
    ): Set<String> {
        return exclusions.flatMap { (packageName, keywords) ->
            keywords.map { keyword ->
                "$packageName|${Uri.encode(keyword)}"
            }
        }.toSet()
    }

    private fun decodeExclusionKeywords(
        entries: Set<String>
    ): Map<String, Set<String>> {
        return entries
            .mapNotNull { entry ->
                val separatorIndex =
                    entry.indexOf('|')

                if (
                    separatorIndex <= 0 ||
                    separatorIndex == entry.lastIndex
                ) {
                    return@mapNotNull null
                }

                val packageName =
                    entry.substring(
                        startIndex = 0,
                        endIndex = separatorIndex
                    )

                val keyword =
                    Uri.decode(
                        entry.substring(
                            startIndex = separatorIndex + 1
                        )
                    ).trim()

                if (keyword.isEmpty()) {
                    null
                } else {
                    packageName to keyword
                }
            }
            .groupBy(
                keySelector = { (packageName, _) ->
                    packageName
                },
                valueTransform = { (_, keyword) ->
                    keyword
                }
            )
            .mapValues { (_, keywords) ->
                keywords.toSet()
            }
    }
}
