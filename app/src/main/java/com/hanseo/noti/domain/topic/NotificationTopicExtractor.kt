package com.hanseo.noti.domain.topic

import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType

class NotificationTopicExtractor {

    fun extract(
        reasons: List<ImportanceReason>
    ): NotificationTopicResult {
        val topics =
            reasons
                .asSequence()
                .filter { reason ->
                    reason.type ==
                            ImportanceReasonType.AUTOMATIC_RULE
                }
                .mapNotNull { reason ->
                    reason.ruleId
                }
                .mapNotNull { ruleId ->
                    TOPIC_BY_RULE_ID[ruleId]
                }
                .toSet()

        if (topics.isEmpty()) {
            return NotificationTopicResult.unknown(
                policyVersion = POLICY_VERSION
            )
        }

        val primaryTopic =
            PRIMARY_TOPIC_PRIORITY
                .firstOrNull { topic ->
                    topic in topics
                }
                ?: topics.first()

        return NotificationTopicResult(
            primaryTopic = primaryTopic,
            topics = topics,
            policyVersion = POLICY_VERSION
        )
    }

    private companion object {

        const val POLICY_VERSION = "1"

        val TOPIC_BY_RULE_ID =
            mapOf(
                "call_or_alarm" to
                        NotificationTopic.CALL_ALARM,

                "event_or_reminder" to
                        NotificationTopic.SCHEDULE,

                "message_or_email" to
                        NotificationTopic.COMMUNICATION,

                "security_authentication" to
                        NotificationTopic.FINANCE_SECURITY,

                "critical_status_change" to
                        NotificationTopic.FINANCE_SECURITY,

                "urgent_attention" to
                        NotificationTopic.ACTION_REQUEST,

                "date_or_time" to
                        NotificationTopic.SCHEDULE,

                "action_request" to
                        NotificationTopic.ACTION_REQUEST,

                "delivery_status_change" to
                        NotificationTopic.DELIVERY,

                "schedule_context" to
                        NotificationTopic.SCHEDULE,

                "promotional_content" to
                        NotificationTopic.PROMOTIONAL,

                "ongoing_progress" to
                        NotificationTopic.INFORMATIONAL,

                "passive_status" to
                        NotificationTopic.INFORMATIONAL
            )

        val PRIMARY_TOPIC_PRIORITY =
            listOf(
                NotificationTopic.PROMOTIONAL,
                NotificationTopic.CALL_ALARM,
                NotificationTopic.FINANCE_SECURITY,
                NotificationTopic.ACTION_REQUEST,
                NotificationTopic.DELIVERY,
                NotificationTopic.RESERVATION,
                NotificationTopic.SCHEDULE,
                NotificationTopic.COMMUNICATION,
                NotificationTopic.INFORMATIONAL
            )
    }
}
