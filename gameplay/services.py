from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from accounts.models import User
from gameplay.models import GameSession, QuestionAttempt

MIN_LEVEL = 1
MAX_LEVEL = 9
FINAL_TABLE = 12
SESSION_QUESTION_COUNT = 20
PASSING_SCORE = 19
XP_PER_CORRECT_ANSWER = 10
SESSION_BONUS_XP = 20


class RandomLike(Protocol):
    def randint(self, a: int, b: int) -> int: ...

    def shuffle(self, x: list[tuple[int, int]]) -> None: ...


@dataclass(frozen=True)
class ProgressStats:
    current_level: int
    available_tables: list[int]
    newest_table: int
    total_xp: int
    best_score: int
    global_success: bool
    mastery_attempts: int
    mastery_correct: int
    mastery_evaluable: bool
    mastery_success: bool
    completed_sessions: int


def available_tables(level: int) -> list[int]:
    if level < MIN_LEVEL or level > MAX_LEVEL:
        raise ValueError("Level must be between 1 and 9.")
    if level == 1:
        return [2, 3, 4]
    return list(range(2, min(level + 3, FINAL_TABLE) + 1))


def newest_table(level: int) -> int:
    if level == 1:
        return 4
    return min(level + 3, FINAL_TABLE)


def _balanced_counts(tables: list[int], total: int) -> list[int]:
    base, remainder = divmod(total, len(tables))
    return [base + (1 if index < remainder else 0) for index, _table in enumerate(tables)]


def generate_questions(level: int, rng: RandomLike | None = None) -> list[tuple[int, int]]:
    generator = rng or random.SystemRandom()
    tables = available_tables(level)
    questions: list[tuple[int, int]] = []

    if level == 1:
        counts = _balanced_counts(tables, SESSION_QUESTION_COUNT)
        source_tables = tables
    else:
        latest = newest_table(level)
        previous_tables = [table for table in tables if table != latest]
        counts = [10, *_balanced_counts(previous_tables, 10)]
        source_tables = [latest, *previous_tables]

    for table, count in zip(source_tables, counts, strict=True):
        for _ in range(count):
            questions.append((table, generator.randint(1, 12)))

    generator.shuffle(questions)
    return questions


def table_distribution(level: int, rng: RandomLike | None = None) -> Counter[int]:
    return Counter(table for table, _multiplier in generate_questions(level, rng))


def get_progress(player: User) -> ProgressStats:
    level = player.current_level
    table = newest_table(level)
    completed = GameSession.objects.filter(player=player, level=level, status=GameSession.Status.COMPLETED)
    best_score = completed.aggregate(best=Max("score"))["best"] or 0

    latest_attempts = list(
        QuestionAttempt.objects.filter(
            session__player=player,
            session__level=level,
            session__status=GameSession.Status.COMPLETED,
            table=table,
            is_correct__isnull=False,
        ).order_by("-answered_at", "-id")[:SESSION_QUESTION_COUNT]
    )
    mastery_correct = sum(1 for attempt in latest_attempts if attempt.is_correct)
    mastery_attempts = len(latest_attempts)
    mastery_evaluable = mastery_attempts == SESSION_QUESTION_COUNT

    return ProgressStats(
        current_level=level,
        available_tables=available_tables(level),
        newest_table=table,
        total_xp=player.total_xp,
        best_score=best_score,
        global_success=best_score >= PASSING_SCORE,
        mastery_attempts=mastery_attempts,
        mastery_correct=mastery_correct,
        mastery_evaluable=mastery_evaluable,
        mastery_success=mastery_evaluable and mastery_correct >= PASSING_SCORE,
        completed_sessions=GameSession.objects.filter(player=player, status=GameSession.Status.COMPLETED).count(),
    )


def start_or_resume_session(player: User) -> GameSession:
    active = GameSession.objects.filter(player=player, status=GameSession.Status.ACTIVE).first()
    if active is not None:
        return active

    with transaction.atomic():
        session = GameSession.objects.create(player=player, level=player.current_level)
        QuestionAttempt.objects.bulk_create(
            QuestionAttempt(session=session, position=index, table=table, multiplier=multiplier)
            for index, (table, multiplier) in enumerate(generate_questions(player.current_level), start=1)
        )
        return session


def current_question(session: GameSession) -> QuestionAttempt | None:
    if session.status != GameSession.Status.ACTIVE:
        return None
    return session.attempts.filter(submitted_answer__isnull=True).order_by("position").first()


def complete_if_needed(session: GameSession) -> None:
    if session.status == GameSession.Status.COMPLETED:
        return
    if session.attempts.filter(submitted_answer__isnull=True).exists():
        return

    score = session.attempts.filter(is_correct=True).count()
    xp_awarded = score * XP_PER_CORRECT_ANSWER + (SESSION_BONUS_XP if score >= PASSING_SCORE else 0)
    session.status = GameSession.Status.COMPLETED
    session.score = score
    session.xp_awarded = xp_awarded
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "score", "xp_awarded", "completed_at"])

    player = User.objects.select_for_update().get(pk=session.player_id)
    player.total_xp += xp_awarded
    player.save(update_fields=["total_xp"])

    maybe_unlock_level(player, session)


def maybe_unlock_level(player: User, session: GameSession) -> None:
    stats = get_progress(player)
    if not stats.global_success:
        return
    if player.current_level > MIN_LEVEL and not stats.mastery_success:
        return
    if player.current_level >= MAX_LEVEL:
        return

    player.current_level += 1
    player.save(update_fields=["current_level"])
    session.unlocked_level = player.current_level
    session.save(update_fields=["unlocked_level"])


@transaction.atomic
def submit_answer(player: User, attempt_id: int, answer: int) -> QuestionAttempt:
    attempt = (
        QuestionAttempt.objects.select_for_update()
        .select_related("session")
        .filter(id=attempt_id, session__player=player)
        .first()
    )
    if attempt is None:
        raise NotFound("Question introuvable.")

    session = GameSession.objects.select_for_update().get(pk=attempt.session_id, player=player)
    if session.status != GameSession.Status.ACTIVE:
        raise ValidationError({"detail": "Cette session est déjà terminée."})
    if attempt.submitted_answer is not None:
        raise ValidationError({"detail": "Cette question a déjà été validée."})

    expected = current_question(session)
    if expected is None or expected.id != attempt.id:
        raise ValidationError({"detail": "Réponds d'abord à la question en cours."})

    attempt.submitted_answer = answer
    attempt.is_correct = answer == attempt.correct_answer
    attempt.answered_at = timezone.now()
    attempt.save(update_fields=["submitted_answer", "is_correct", "answered_at"])
    complete_if_needed(session)
    return attempt


def session_stats(session: GameSession) -> dict[int, dict[str, int]]:
    rows = (
        session.attempts.values("table")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
        .order_by("table")
    )
    return {int(row["table"]): {"total": int(row["total"]), "correct": int(row["correct"])} for row in rows}
