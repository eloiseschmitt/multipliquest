# Generated manually for the gameplay engine.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.PositiveSmallIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Active"), ("COMPLETED", "Completed")], default="ACTIVE", max_length=12
                    ),
                ),
                ("total_questions", models.PositiveSmallIntegerField(default=20)),
                ("score", models.PositiveSmallIntegerField(default=0)),
                ("xp_awarded", models.PositiveIntegerField(default=0)),
                ("unlocked_level", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="game_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-started_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="QuestionAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveSmallIntegerField()),
                ("table", models.PositiveSmallIntegerField()),
                ("multiplier", models.PositiveSmallIntegerField()),
                ("submitted_answer", models.IntegerField(blank=True, null=True)),
                ("is_correct", models.BooleanField(blank=True, null=True)),
                ("answered_at", models.DateTimeField(blank=True, null=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="gameplay.gamesession"
                    ),
                ),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.AddConstraint(
            model_name="gamesession",
            constraint=models.UniqueConstraint(
                condition=Q(("status", "ACTIVE")), fields=("player",), name="one_active_game_session_per_player"
            ),
        ),
        migrations.AddConstraint(
            model_name="questionattempt",
            constraint=models.UniqueConstraint(
                fields=("session", "position"), name="unique_attempt_position_per_session"
            ),
        ),
    ]
