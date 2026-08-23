package com.hanseo.noti.di

import com.hanseo.noti.ai.ActionabilityClassifierProvider
import com.hanseo.noti.ai.OnDeviceActionabilityClassifierProvider
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class AiModule {

    @Binds
    @Singleton
    abstract fun bindActionabilityClassifierProvider(
        implementation:
            OnDeviceActionabilityClassifierProvider
    ): ActionabilityClassifierProvider
}
