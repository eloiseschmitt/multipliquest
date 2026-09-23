from __future__ import annotations

from rest_framework import serializers

from gameplay.models import GameSession, QuestionAttempt
from gameplay.services import ProgressStats, current_question, session_stats


class ProgressSerializer(serializers.Serializer[dict[str, object]]):
    current_level = serializers.IntegerField()
    available_tables = serializers.ListField(child=serializers.IntegerField())
    newest_table = serializers.IntegerField()
    total_xp = serializers.IntegerField()
    best_score = serializers.IntegerField()
    global_success = serializers.BooleanField()
    mastery_attempts = serializers.IntegerField()
    mastery_correct = serializers.IntegerField()
    mastery_evaluable = serializers.BooleanField()
    mastery_success = serializers.BooleanField()
    completed_sessions = serializers.IntegerField()

    @classmethod
    def from_stats(cls, stats: ProgressStats) -> dict[str, object]:
        return {
            "current_level": stats.current_level,
            "available_tables": stats.available_tables,
            "newest_table": stats.newest_table,
            "total_xp": stats.total_xp,
            "best_score": stats.best_score,
            "global_success": stats.global_success,
            "mastery_attempts": stats.mastery_attempts,
            "mastery_correct": stats.mastery_correct,
            "mastery_evaluable": stats.mastery_evaluable,
            "mastery_success": stats.mastery_success,
            "completed_sessions": stats.completed_sessions,
        }


class QuestionSerializer(serializers.ModelSerializer[QuestionAttempt]):
    class Meta:
        model = QuestionAttempt
        fields = ("id", "position", "table", "multiplier")
        read_only_fields = fields


class CorrectionSerializer(serializers.ModelSerializer[QuestionAttempt]):
    correct_answer = serializers.IntegerField(read_only=True)

    class Meta:
        model = QuestionAttempt
        fields = ("id", "position", "table", "multiplier", "submitted_answer", "is_correct", "correct_answer")
        read_only_fields = fields


class SessionSerializer(serializers.ModelSerializer[GameSession]):
    current_question = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = (
            "id",
            "level",
            "status",
            "total_questions",
            "score",
            "xp_awarded",
            "unlocked_level",
            "answered_count",
            "current_question",
        )
        read_only_fields = fields

    def get_current_question(self, session: GameSession) -> dict[str, object] | None:
        question = current_question(session)
        if question is None:
            return None
        return QuestionSerializer(question).data

    def get_answered_count(self, session: GameSession) -> int:
        return session.attempts.filter(submitted_answer__isnull=False).count()


class SessionSummarySerializer(serializers.ModelSerializer[GameSession]):
    table_stats = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = (
            "id",
            "level",
            "status",
            "total_questions",
            "score",
            "xp_awarded",
            "unlocked_level",
            "table_stats",
            "progress",
        )
        read_only_fields = fields

    def get_table_stats(self, session: GameSession) -> dict[str, dict[str, int]]:
        return {str(table): stats for table, stats in session_stats(session).items()}

    def get_progress(self, _session: GameSession) -> dict[str, object]:
        progress = self.context["progress"]
        if not isinstance(progress, dict):
            return {}
        return progress


class SubmitAnswerSerializer(serializers.Serializer[dict[str, int]]):
    question_id = serializers.IntegerField(min_value=1)
    answer = serializers.IntegerField(min_value=0, max_value=144)
