package com.hanseo.noti.domain.personalization

data class PersonalizationContribution(
    val scope: PersonalizationScope,
    val packageName: String,
    val channelKey: String,
    val topicKey: String,
    val importantDelta: Int,
    val generalDelta: Int,
    val feedbackAt: Long,
    val profileVersion: String
)