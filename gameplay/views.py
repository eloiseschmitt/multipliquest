from __future__ import annotations

from typing import cast

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer
from gameplay.models import GameSession
from gameplay.serializers import (
    CorrectionSerializer,
    ProgressSerializer,
    SessionSerializer,
    SessionSummarySerializer,
    SubmitAnswerSerializer,
)
from gameplay.services import get_progress, start_or_resume_session, submit_answer


class MyProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(cast(User, request.user)).data)


class PlayerProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, player_id: int) -> Response:
        user = get_object_or_404(User, id=player_id, pk=request.user.pk)
        return Response(UserSerializer(user).data)


class GameProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        player = cast(User, request.user)
        return Response(ProgressSerializer.from_stats(get_progress(player)))


@method_decorator(csrf_protect, name="dispatch")
class ActiveSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        player = cast(User, request.user)
        session = GameSession.objects.filter(player=player, status=GameSession.Status.ACTIVE).first()
        if session is None:
            return Response({"session": None})
        return Response({"session": SessionSerializer(session).data})

    def post(self, request: Request) -> Response:
        player = cast(User, request.user)
        session = start_or_resume_session(player)
        return Response({"session": SessionSerializer(session).data})


class SessionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: int) -> Response:
        player = cast(User, request.user)
        session = get_object_or_404(GameSession, id=session_id, player=player)
        progress = ProgressSerializer.from_stats(get_progress(player))
        return Response({"session": SessionSummarySerializer(session, context={"progress": progress}).data})


@method_decorator(csrf_protect, name="dispatch")
class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        player = cast(User, request.user)
        attempt = submit_answer(
            player=player,
            attempt_id=serializer.validated_data["question_id"],
            answer=serializer.validated_data["answer"],
        )
        attempt.session.refresh_from_db()
        player.refresh_from_db()
        progress = ProgressSerializer.from_stats(get_progress(player))
        return Response(
            {
                "correction": CorrectionSerializer(attempt).data,
                "session": SessionSerializer(attempt.session).data,
                "summary": (
                    SessionSummarySerializer(attempt.session, context={"progress": progress}).data
                    if attempt.session.status == GameSession.Status.COMPLETED
                    else None
                ),
            }
        )
