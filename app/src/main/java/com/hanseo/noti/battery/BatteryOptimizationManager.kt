package com.hanseo.noti.battery

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.PowerManager
import android.provider.Settings
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BatteryOptimizationManager @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {
    private val powerManager: PowerManager =
        context.getSystemService(
            Context.POWER_SERVICE
        ) as PowerManager

    fun isBatteryOptimizationExempt(): Boolean {
        return powerManager
            .isIgnoringBatteryOptimizations(
                context.packageName
            )
    }

    fun createBatterySettingsIntent(): Intent {
        return Intent(
            Settings.ACTION_APPLICATION_DETAILS_SETTINGS
        ).apply {
            data = Uri.fromParts(
                "package",
                context.packageName,
                null
            )
        }
    }
}

