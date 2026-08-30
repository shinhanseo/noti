package com.hanseo.noti.data.mapper

import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.domain.model.NotificationItem
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity
import com.hanseo.noti.data.local.relation.NotificationWithReasons
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.importance.AiImportanceLabel
import com.hanseo.noti.domain.importance.AiImportancePrediction
import com.hanseo.noti.domain.topic.NotificationTopic
import com.hanseo.noti.domain.topic.NotificationTopicResult

fun NotificationEntity.toDomain(): NotificationItem {
    return NotificationItem(
        key = notificationKey,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        channelId = channelId,
        isOngoing = isOngoing,
        isGroupSummary = false,
        isRemoved = isRemoved,
        removedAt = removedAt,
        readAt = readAt
    )
}

fun ClassifiedNotification.toEntity(): NotificationEntity {
    return NotificationEntity(
        notificationKey = notification.key,
        packageName = notification.packageName,
        title = notification.title,
        body = notification.body,
        postedAt = notification.postedAt,
        category = notification.category,
        channelId = notification.channelId,
        isOngoing = notification.isOngoing,
        isRemoved = notification.isRemoved,
        removedAt = notification.removedAt,
        readAt = notification.readAt,

        importanceScore = importance.score,
        importanceLevel = importance.level.name,
        importanceForced = importance.isForced,
        importancePolicyVersion = importance.policyVersion,
        importanceEvaluatedAt = importance.evaluatedAtMillis,

        aiPredictionLabel = aiPrediction?.label?.name,
        aiImportantProbability = aiPrediction?.importantProbability,
        aiScoreDelta = aiPrediction?.scoreDelta,
        aiModelVersion = aiPrediction?.modelVersion,
        aiEvaluatedAt = aiPrediction?.evaluatedAtMillis,

        primaryTopic = topicResult.primaryTopic.name,
        topicNames = topicResult.topics
            .sortedBy { topic -> topic.name }
            .joinToString(",") { topic -> topic.name },
        topicPolicyVersion = topicResult.policyVersion
    )
}

fun ClassifiedNotification.toReasonEntities(): List<ImportanceReasonEntity> {
    return importance.reasons.mapIndexed { index, reason ->
        ImportanceReasonEntity(
            notificationKey = notification.key,
            reasonOrder = index,
            type = reason.type.name,
            scoreDelta = reason.scoreDelta,
            ruleId = reason.ruleId,
            description = reason.description
        )
    }
}

private fun ImportanceReasonEntity.toDomain(): ImportanceReason {
    return ImportanceReason(
        type = ImportanceReasonType.valueOf(type),
        scoreDelta = scoreDelta,
        ruleId = ruleId,
        description = description
    )
}

fun NotificationWithReasons.toClassifiedNotification():
        ClassifiedNotification? {

    val score = notification.importanceScore
        ?: return null

    val levelName = notification.importanceLevel
        ?: return null

    val forced = notification.importanceForced
        ?: return null

    val policyVersion = notification.importancePolicyVersion
        ?: return null

    val evaluatedAt = notification.importanceEvaluatedAt
        ?: return null

    val level = ImportanceLevel.valueOf(levelName)

    val importanceResult = ImportanceResult(
        score = score,
        level = level,
        reasons = reasons
            .sortedBy { reason -> reason.reasonOrder }
            .map { reason -> reason.toDomain() },
        isForced = forced,
        policyVersion = policyVersion,
        evaluatedAtMillis = evaluatedAt
    )

    return ClassifiedNotification(
        notification = notification.toDomain(),
        importance = importanceResult,
        aiPrediction = notification.toAiPrediction(),
        topicResult = notification.toTopicResult()
    )
}

private fun NotificationEntity.toTopicResult():
        NotificationTopicResult {

    val policyVersion =
        topicPolicyVersion ?: LEGACY_TOPIC_POLICY_VERSION

    val storedTopics =
        topicNames
            ?.split(",")
            ?.mapNotNull { topicName ->
                NotificationTopic.entries
                    .firstOrNull { topic ->
                        topic.name == topicName
                    }
            }
            ?.toSet()
            .orEmpty()

    val storedPrimaryTopic =
        primaryTopic?.let { topicName ->
            NotificationTopic.entries
                .firstOrNull { topic ->
                    topic.name == topicName
                }
        }

    if (
        storedPrimaryTopic == null &&
        storedTopics.isEmpty()
    ) {
        return NotificationTopicResult.unknown(
            policyVersion = policyVersion
        )
    }

    val resolvedPrimaryTopic =
        storedPrimaryTopic
            ?: storedTopics.first()

    return NotificationTopicResult(
        primaryTopic = resolvedPrimaryTopic,
        topics = storedTopics + resolvedPrimaryTopic,
        policyVersion = policyVersion
    )
}

private fun NotificationEntity.toAiPrediction():
        AiImportancePrediction? {

    val labelName = aiPredictionLabel
        ?: return null

    val importantProbability = aiImportantProbability
        ?: return null

    val scoreDelta = aiScoreDelta
        ?: return null

    val modelVersion = aiModelVersion
        ?: return null

    val evaluatedAtMillis = aiEvaluatedAt
        ?: return null

    return AiImportancePrediction(
        label = AiImportanceLabel.valueOf(labelName),
        importantProbability = importantProbability,
        scoreDelta = scoreDelta,
        modelVersion = modelVersion,
        evaluatedAtMillis = evaluatedAtMillis
    )
}

private const val LEGACY_TOPIC_POLICY_VERSION = "legacy"
