from __future__ import annotations

from typing import cast

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.rate_limit import LoginRateLimiter
from accounts.serializers import LoginSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def post(self, request: Request) -> Response:
        request_data = request.data if isinstance(request.data, dict) else {}
        username = str(request_data.get("username", ""))
        limiter = LoginRateLimiter(request, username)
        if limiter.is_blocked():
            return Response(
                {"detail": "Trop de tentatives. Réessaie dans quelques minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            limiter.record_failure()
            return Response(
                {"detail": "Identifiant ou mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = cast(User, serializer.validated_data["user"])
        login(request, user)
        limiter.reset()
        return Response({"user": UserSerializer(user).data})


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"user": UserSerializer(cast(User, request.user)).data})
