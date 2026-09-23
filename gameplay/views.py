from __future__ import annotations

from typing import cast

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer


class MyProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(cast(User, request.user)).data)


class PlayerProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, player_id: int) -> Response:
        user = get_object_or_404(User, id=player_id, pk=request.user.pk)
        return Response(UserSerializer(user).data)
