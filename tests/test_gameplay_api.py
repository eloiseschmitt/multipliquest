from __future__ import annotations

from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from gameplay.models import GameSession

User = get_user_model()


@pytest.fixture
def player():
    return User.objects.create_user(username=f"player-{uuid4().hex}", password=None, role=User.Role.CHILD)


@pytest.fixture
def other_player():
    return User.objects.create_user(username=f"player-{uuid4().hex}", password=None, role=User.Role.CHILD)


@pytest.mark.django_db
def test_game_progress_requires_authentication() -> None:
    response = APIClient().get("/api/game/progress/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_start_session_returns_question_without_correct_answer(player) -> None:
    client = APIClient()
    client.force_login(player)

    response = client.post("/api/game/session/", {}, format="json")

    assert response.status_code == 200
    question = response.data["session"]["current_question"]
    assert question["table"] in [2, 3, 4]
    assert "correct_answer" not in question
    assert response.data["session"]["total_questions"] == 20


@pytest.mark.django_db
def test_active_session_can_be_resumed(player) -> None:
    client = APIClient()
    client.force_login(player)
    created = client.post("/api/game/session/", {}, format="json").data["session"]

    response = client.get("/api/game/session/")

    assert response.status_code == 200
    assert response.data["session"]["id"] == created["id"]


@pytest.mark.django_db
def test_submit_answer_returns_immediate_correction(player) -> None:
    client = APIClient()
    client.force_login(player)
    session = client.post("/api/game/session/", {}, format="json").data["session"]
    question = session["current_question"]

    response = client.post(
        "/api/game/answer/",
        {"question_id": question["id"], "answer": question["table"] * question["multiplier"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["correction"]["is_correct"] is True
    assert response.data["correction"]["correct_answer"] == question["table"] * question["multiplier"]
    assert response.data["session"]["answered_count"] == 1


@pytest.mark.django_db
def test_duplicate_submission_is_rejected(player) -> None:
    client = APIClient()
    client.force_login(player)
    question = client.post("/api/game/session/", {}, format="json").data["session"]["current_question"]

    first_response = client.post("/api/game/answer/", {"question_id": question["id"], "answer": 0}, format="json")
    duplicate_response = client.post("/api/game/answer/", {"question_id": question["id"], "answer": 0}, format="json")

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400


@pytest.mark.django_db
def test_user_cannot_submit_another_players_question(player, other_player) -> None:
    owner = APIClient()
    owner.force_login(other_player)
    question = owner.post("/api/game/session/", {}, format="json").data["session"]["current_question"]

    client = APIClient()
    client.force_login(player)
    response = client.post("/api/game/answer/", {"question_id": question["id"], "answer": 12}, format="json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_completed_session_summary_contains_table_stats(player) -> None:
    client = APIClient()
    client.force_login(player)
    session_payload = client.post("/api/game/session/", {}, format="json").data["session"]
    session = GameSession.objects.get(id=session_payload["id"])

    for attempt in session.attempts.order_by("position"):
        response = client.post(
            "/api/game/answer/",
            {"question_id": attempt.id, "answer": attempt.correct_answer},
            format="json",
        )

    assert response.data["summary"]["score"] == 20
    assert response.data["summary"]["table_stats"]
    assert response.data["summary"]["progress"]["total_xp"] == 220


@pytest.mark.django_db
def test_summary_is_isolated_between_players(player, other_player) -> None:
    owner = APIClient()
    owner.force_login(other_player)
    session = owner.post("/api/game/session/", {}, format="json").data["session"]

    client = APIClient()
    client.force_login(player)
    response = client.get(f"/api/game/session/{session['id']}/summary/")

    assert response.status_code == 404
