from __future__ import annotations

from secrets import token_urlsafe
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

User = get_user_model()
USERNAME_FIELD = User.USERNAME_FIELD
PASSWORD_FIELD = "password"


def unique_username(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def auth_payload(username: str, password: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    payload[USERNAME_FIELD] = username
    payload[PASSWORD_FIELD] = password
    return payload


@pytest.fixture
def parent_credentials() -> dict[str, str]:
    return auth_payload(unique_username("parent"), token_urlsafe(24))


@pytest.fixture
def child_credentials() -> dict[str, str]:
    return auth_payload(unique_username("child"), token_urlsafe(24))


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    cache.clear()


@pytest.fixture
def parent_user(parent_credentials):
    return User.objects.create_user(
        username=parent_credentials[USERNAME_FIELD],
        password=parent_credentials[PASSWORD_FIELD],
        role=User.Role.PARENT,
    )


@pytest.fixture
def child_user(parent_user, child_credentials):
    return User.objects.create_user(
        username=child_credentials[USERNAME_FIELD],
        password=child_credentials[PASSWORD_FIELD],
        role=User.Role.CHILD,
        parent=parent_user,
        display_name="Nina",
    )


@pytest.fixture
def other_child(parent_user):
    return User.objects.create_user(
        username=unique_username("child"),
        password=token_urlsafe(24),
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
    assert response.status_code == 204
    return response.cookies["csrftoken"].value


@pytest.mark.django_db
def test_login_with_valid_credentials_starts_session(child_user, child_credentials) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)

    response = client.post(
        "/api/auth/login/",
        child_credentials,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 200
    assert response.data["user"]["username"] == child_user.username
    assert response.data["user"]["role"] == User.Role.CHILD
    assert "password" not in response.data["user"]
    assert "sessionid" in response.cookies
    assert response.cookies["sessionid"]["httponly"]


@pytest.mark.django_db
def test_login_with_invalid_credentials_uses_generic_error(child_user) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)
    credentials = auth_payload(unique_username("missing-user"), token_urlsafe(24))

    response = client.post(
        "/api/auth/login/",
        credentials,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 400
    assert response.data == {"detail": "Identifiant ou mot de passe incorrect."}


@pytest.mark.django_db
def test_login_requires_csrf_token(child_user, child_credentials) -> None:
    client = csrf_client()
    set_csrf_cookie(client)

    response = client.post(
        "/api/auth/login/",
        child_credentials,
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_invalidates_session(child_user, child_credentials) -> None:
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)
    client.post(
        "/api/auth/login/",
        child_credentials,
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
def test_parent_can_create_child_account(parent_user) -> None:
    client = csrf_client()
    client.force_login(parent_user)
    csrf_token = set_csrf_cookie(client)
    child_password = token_urlsafe(24)
    child_username = unique_username("new-child")
    child_payload = auth_payload(child_username, child_password)
    child_payload["display_name"] = "Malo"

    response = client.post(
        "/api/children/",
        child_payload,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    created = User.objects.get(username=child_username)
    assert response.status_code == 201
    assert response.data["username"] == child_username
    assert response.data["role"] == User.Role.CHILD
    assert created.parent == parent_user
    assert created.check_password(child_password)


@pytest.mark.django_db
def test_child_cannot_create_child_account(child_user) -> None:
    client = csrf_client()
    client.force_login(child_user)
    csrf_token = set_csrf_cookie(client)
    blocked_username = unique_username("blocked-child")
    blocked_payload = auth_payload(blocked_username, token_urlsafe(24))

    response = client.post(
        "/api/children/",
        blocked_payload,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 403
    assert not User.objects.filter(username=blocked_username).exists()


@pytest.mark.django_db
def test_user_cannot_access_another_players_progress(child_user, other_child) -> None:
    client = APIClient()
    client.force_login(child_user)

    own_response = client.get("/api/progress/me/")
    other_response = client.get(f"/api/progress/{other_child.id}/")

    assert own_response.status_code == 200
    assert own_response.data["username"] == child_user.username
    assert other_response.status_code == 404


@pytest.mark.django_db
def test_session_expiration_returns_forbidden(child_user) -> None:
    client = APIClient()
    client.force_login(child_user)

    assert client.get("/api/auth/me/").status_code == 200
    client.logout()

    assert client.get("/api/auth/me/").status_code == 403


@pytest.mark.django_db
def test_login_attempts_are_limited(child_user, child_credentials, settings) -> None:
    settings.LOGIN_RATE_LIMIT_ATTEMPTS = 2
    client = csrf_client()
    csrf_token = set_csrf_cookie(client)
    invalid_credentials = auth_payload(child_credentials[USERNAME_FIELD], token_urlsafe(24))

    for _ in range(2):
        response = client.post(
            "/api/auth/login/",
            invalid_credentials,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 400

    blocked_response = client.post(
        "/api/auth/login/",
        child_credentials,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert blocked_response.status_code == 429
    assert blocked_response.data == {"detail": "Trop de tentatives. Réessaie dans quelques minutes."}
