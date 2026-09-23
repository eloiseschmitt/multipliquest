from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q


class GameSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_sessions")
    level = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=12, choices=Status, default=Status.ACTIVE)
    total_questions = models.PositiveSmallIntegerField(default=20)
    score = models.PositiveSmallIntegerField(default=0)
    xp_awarded = models.PositiveIntegerField(default=0)
    unlocked_level = models.PositiveSmallIntegerField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["player"],
                condition=Q(status="ACTIVE"),
                name="one_active_game_session_per_player",
            ),
        ]
        ordering = ["-started_at", "-id"]


class QuestionAttempt(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="attempts")
    position = models.PositiveSmallIntegerField()
    table = models.PositiveSmallIntegerField()
    multiplier = models.PositiveSmallIntegerField()
    submitted_answer = models.IntegerField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "position"], name="unique_attempt_position_per_session"),
        ]
        ordering = ["position"]

    @property
    def correct_answer(self) -> int:
        return self.table * self.multiplier
