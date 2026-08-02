package com.hanseo.noti.data.apps

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.graphics.Bitmap
import android.os.Build
import androidx.core.graphics.drawable.toBitmap
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.roundToInt

@Singleton
class InstalledAppProvider @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {
    suspend fun getLaunchableApps(): List<InstalledApp> {
        return withContext(Dispatchers.IO) {
            val packageManager =
                context.packageManager

            val launcherIntent =
                Intent(Intent.ACTION_MAIN).apply {
                    addCategory(Intent.CATEGORY_LAUNCHER)
                }

            val resolveInfos =
                queryLaunchableActivities(
                    packageManager = packageManager,
                    intent = launcherIntent
                )

            val iconSizePx =
                (
                        APP_ICON_SIZE_DP *
                                context.resources
                                    .displayMetrics
                                    .density
                        ).roundToInt()

            resolveInfos
                .mapNotNull { resolveInfo ->
                    resolveInfo.toInstalledApp(
                        packageManager = packageManager,
                        iconSizePx = iconSizePx
                    )
                }
                .filter { installedApp ->
                    installedApp.packageName !=
                            context.packageName
                }
                .distinctBy { installedApp ->
                    installedApp.packageName
                }
                .sortedBy { installedApp ->
                    installedApp.displayName
                        .lowercase(Locale.getDefault())
                }
        }
    }

    private fun queryLaunchableActivities(
        packageManager: PackageManager,
        intent: Intent
    ): List<ResolveInfo> {
        return if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.TIRAMISU
        ) {
            packageManager.queryIntentActivities(
                intent,
                PackageManager.ResolveInfoFlags.of(
                    PackageManager.MATCH_ALL.toLong()
                )
            )
        } else {
            @Suppress("DEPRECATION")
            packageManager.queryIntentActivities(
                intent,
                PackageManager.MATCH_ALL
            )
        }
    }

    private fun ResolveInfo.toInstalledApp(
        packageManager: PackageManager,
        iconSizePx: Int
    ): InstalledApp? {
        val appPackageName =
            activityInfo?.packageName
                ?: return null

        val appDisplayName =
            loadLabel(packageManager)
                .toString()
                .trim()
                .ifEmpty {
                    appPackageName
                }

        val appIcon: Bitmap? =
            runCatching {
                loadIcon(packageManager)
                    .toBitmap(
                        width = iconSizePx,
                        height = iconSizePx,
                        config =
                            Bitmap.Config.ARGB_8888
                    )
            }.getOrNull()

        return InstalledApp(
            packageName = appPackageName,
            displayName = appDisplayName,
            icon = appIcon
        )
    }

    private companion object {
        const val APP_ICON_SIZE_DP = 48
    }
}