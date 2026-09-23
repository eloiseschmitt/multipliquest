from __future__ import annotations

from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from gameplay.models import GameSession, QuestionAttempt
from gameplay.services import (
    available_tables,
    generate_questions,
    get_progress,
    newest_table,
    start_or_resume_session,
    submit_answer,
)

User = get_user_model()


class DeterministicRandom:
    def __init__(self) -> None:
        self.next_value = 0

    def randint(self, a: int, b: int) -> int:
        value = a + (self.next_value % (b - a + 1))
        self.next_value += 1
        return value

    def shuffle(self, x: list[tuple[int, int]]) -> None:
        x.reverse()


@pytest.fixture
def player():
    return User.objects.create_user(username=f"player-{uuid4().hex}", password=None, role=User.Role.CHILD)


@pytest.mark.django_db
def test_available_tables_stop_at_table_12() -> None:
    assert available_tables(1) == [2, 3, 4]
    assert available_tables(9) == list(range(2, 13))
    assert newest_table(9) == 12


def test_level_1_question_distribution_is_balanced() -> None:
    questions = generate_questions(1, DeterministicRandom())
    counts = {table: sum(1 for question in questions if question[0] == table) for table in [2, 3, 4]}

    assert len(questions) == 20
    assert sorted(counts.values()) == [6, 7, 7]
    assert all(1 <= multiplier <= 12 for _table, multiplier in questions)


def test_unlocked_level_distribution_uses_half_new_table() -> None:
    questions = generate_questions(3, DeterministicRandom())
    counts = {table: sum(1 for question in questions if question[0] == table) for table in range(2, 7)}

    assert len(questions) == 20
    assert counts[6] == 10
    assert sum(counts[table] for table in [2, 3, 4, 5]) == 10
    assert all(counts[table] >= 2 for table in [2, 3, 4, 5])


@pytest.mark.django_db
def test_start_or_resume_session_reuses_active_session(player) -> None:
    first = start_or_resume_session(player)
    second = start_or_resume_session(player)

    assert first.id == second.id
    assert first.attempts.count() == 20
    assert GameSession.objects.filter(player=player, status=GameSession.Status.ACTIVE).count() == 1


def make_completed_session(player, level: int, score: int, table_results: list[bool]) -> GameSession:
    session = GameSession.objects.create(
        player=player,
        level=level,
        status=GameSession.Status.COMPLETED,
        score=score,
        xp_awarded=score * 10,
    )
    rows = []
    for index in range(1, 21):
        table = newest_table(level) if index <= len(table_results) else 2
        is_correct = table_results[index - 1] if index <= len(table_results) else index <= score
        rows.append(
            QuestionAttempt(
                session=session,
                position=index,
                table=table,
                multiplier=1,
                submitted_answer=table if is_correct else 0,
                is_correct=is_correct,
            )
        )
    QuestionAttempt.objects.bulk_create(rows)
    return session


@pytest.mark.django_db
def test_level_1_global_success_unlocks_table_5_without_table_4_mastery(player) -> None:
    session = make_completed_session(player, level=1, score=19, table_results=[False] * 7)

    from gameplay.services import maybe_unlock_level

    maybe_unlock_level(player, session)
    player.refresh_from_db()
    session.refresh_from_db()

    assert player.current_level == 2
    assert session.unlocked_level == 2


@pytest.mark.django_db
def test_mastery_alone_does_not_unlock(player) -> None:
    player.current_level = 2
    player.save(update_fields=["current_level"])
    make_completed_session(player, level=2, score=18, table_results=[True] * 20)

    stats = get_progress(player)

    assert not stats.global_success
    assert stats.mastery_success


@pytest.mark.django_db
def test_both_conditions_can_unlock_across_sessions(player) -> None:
    player.current_level = 2
    player.save(update_fields=["current_level"])
    make_completed_session(player, level=2, score=19, table_results=[False] + [True] * 9)
    session = make_completed_session(player, level=2, score=18, table_results=[True] * 10)

    from gameplay.services import maybe_unlock_level

    maybe_unlock_level(player, session)
    player.refresh_from_db()

    assert player.current_level == 3
    session.refresh_from_db()
    assert session.unlocked_level == 3


@pytest.mark.django_db
def test_rolling_mastery_window_uses_latest_20_attempts(player) -> None:
    player.current_level = 2
    player.save(update_fields=["current_level"])
    make_completed_session(player, level=2, score=19, table_results=[True] * 20)
    make_completed_session(player, level=2, score=19, table_results=[False, True])

    stats = get_progress(player)

    assert stats.mastery_attempts == 20
    assert stats.mastery_correct == 19
    assert stats.mastery_success


@pytest.mark.django_db
def test_incomplete_sessions_do_not_count_for_mastery(player) -> None:
    session = GameSession.objects.create(player=player, level=1)
    QuestionAttempt.objects.bulk_create(
        QuestionAttempt(
            session=session,
            position=index,
            table=4,
            multiplier=1,
            submitted_answer=4,
            is_correct=True,
        )
        for index in range(1, 21)
    )

    stats = get_progress(player)

    assert stats.mastery_attempts == 0


@pytest.mark.django_db
def test_submitting_final_answer_completes_session_once(player) -> None:
    session = start_or_resume_session(player)
    for attempt in session.attempts.order_by("position"):
        submit_answer(player, attempt.id, attempt.correct_answer)

    session.refresh_from_db()
    player.refresh_from_db()

    assert session.status == GameSession.Status.COMPLETED
    assert session.score == 20
    assert player.total_xp == 220

    with pytest.raises(ValidationError):
        submit_answer(player, session.attempts.first().id, 0)
    player.refresh_from_db()
    assert player.total_xp == 220


@pytest.mark.django_db
def test_final_level_never_creates_level_10(player) -> None:
    player.current_level = 9
    player.save(update_fields=["current_level"])
    session = make_completed_session(player, level=9, score=20, table_results=[True] * 20)

    from gameplay.services import maybe_unlock_level

    maybe_unlock_level(player, session)
    player.refresh_from_db()

    assert player.current_level == 9
