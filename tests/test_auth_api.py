from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    cache.clear()


@pytest.fixture
def parent_user():
    return User.objects.create_user(
        username="parent1",
        password="ParentPass123!",
        role=User.Role.PARENT,
    )


@pytest.fixture
def child_user(parent_user):
    return User.objects.create_user(
        username="child1",
        password="ChildPass123!",
        role=User.Role.CHILD,
        parent=parent_user,
        display_name="Nina",
    )


@pytest.fixture
def other_child(parent_user):
    return User.objects.create_user(
        username="child2",
        password="OtherPass123!",
        role=User.Role.CHILD,
        parent=parent_user,
        display_name="Lina",
        current_level=3,
        total_xp=120,
    )


def csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def set_csrf_cookie(client: APIClient) -> str:
    response = client.get("/api/auth/csrf/")
    assert response.status_code == 200
    assert response.data["csrfToken"]
    return response.cookies["csrftoken"].value


@pytest.mark.django_db
def test_login_with_valid_credentials_starts_session(child_user) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)

    response = client.post(
        "/api/auth/login/",
        {"username": "child1", "password": "ChildPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 200
    assert response.data["user"]["username"] == "child1"
    assert response.data["user"]["role"] == User.Role.CHILD
    assert "password" not in response.data["user"]
    assert "sessionid" in response.cookies
    assert response.cookies["sessionid"]["httponly"]


@pytest.mark.django_db
def test_login_with_invalid_credentials_uses_generic_error(child_user) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)

    response = client.post(
        "/api/auth/login/",
        {"username": "missing-user", "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 400
    assert response.data == {"detail": "Identifiant ou mot de passe incorrect."}


@pytest.mark.django_db
def test_login_requires_csrf_token(child_user) -> None:
    client = csrf_client()
    set_csrf_cookie(client)

    response = client.post(
        "/api/auth/login/",
        {"username": "child1", "password": "ChildPass123!"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_invalidates_session(child_user) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)
    client.post(
        "/api/auth/login/",
        {"username": "child1", "password": "ChildPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    csrf_token = client.cookies["csrftoken"].value

    response = client.post("/api/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=csrf_token)
    me_response = client.get("/api/auth/me/")

    assert response.status_code == 204
    assert me_response.status_code == 403


@pytest.mark.django_db
def test_protected_api_rejects_anonymous_user() -> None:
    response = APIClient().get("/api/auth/me/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_child_account_creation_is_admin_only(parent_user) -> None:
    client = csrf_client()
    client.force_login(parent_user)
    csrf_token = set_csrf_cookie(client)

    response = client.post(
        "/api/children/",
        {
            "username": "newchild",
            "password": "NewChildPass123!",
            "display_name": "Malo",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 404
    assert not User.objects.filter(username="newchild").exists()


@pytest.mark.django_db
def test_child_create_endpoint_is_not_available_to_children(child_user) -> None:
    client = csrf_client()
    client.force_login(child_user)
    csrf_token = set_csrf_cookie(client)

    response = client.post(
        "/api/children/",
        {"username": "blocked", "password": "BlockedPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 404
    assert not User.objects.filter(username="blocked").exists()


@pytest.mark.django_db
def test_user_cannot_access_another_players_progress(child_user, other_child) -> None:
    client = APIClient()
    client.force_login(child_user)

    own_response = client.get("/api/progress/me/")
    other_response = client.get(f"/api/progress/{other_child.id}/")

    assert own_response.status_code == 200
    assert own_response.data["username"] == "child1"
    assert other_response.status_code == 404


@pytest.mark.django_db
def test_session_expiration_returns_forbidden(child_user) -> None:
    client = APIClient()
    client.force_login(child_user)

    assert client.get("/api/auth/me/").status_code == 200
    client.logout()

    assert client.get("/api/auth/me/").status_code == 403


@pytest.mark.django_db
def test_login_attempts_are_limited(child_user, settings) -> None:
    settings.LOGIN_RATE_LIMIT_ATTEMPTS = 2
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)

    for _ in range(2):
        response = client.post(
            "/api/auth/login/",
            {"username": "child1", "password": "wrong"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 400

    blocked_response = client.post(
        "/api/auth/login/",
        {"username": "child1", "password": "ChildPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert blocked_response.status_code == 429
    assert blocked_response.data == {"detail": "Trop de tentatives. Réessaie dans quelques minutes."}


def test_health_check_exposes_no_sensitive_data() -> None:
    response = APIClient().get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
