from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "username", "display_name", "role", "current_level", "total_xp")
        read_only_fields = fields


class LoginSerializer(serializers.Serializer[dict[str, object]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=256, trim_whitespace=False, write_only=True)

    default_error_messages = {
        "invalid_credentials": "Identifiant ou mot de passe incorrect.",
    }

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=str(attrs["username"]),
            password=str(attrs["password"]),
        )
        if user is None:
            raise serializers.ValidationError(
                {"detail": self.error_messages["invalid_credentials"]},
                code="invalid_credentials",
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": self.error_messages["invalid_credentials"]},
                code="invalid_credentials",
            )
        attrs["user"] = user
        return attrs
