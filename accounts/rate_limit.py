from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


class LoginRateLimiter:
    cache_prefix = "login-attempt"

    def __init__(self, request: HttpRequest, username: str) -> None:
        self.request = request
        self.username = username.strip().lower()

    @property
    def limit(self) -> int:
        return int(getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5))

    @property
    def window_seconds(self) -> int:
        return int(getattr(settings, "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300))

    def is_blocked(self) -> bool:
        return int(cache.get(self.cache_key, 0)) >= self.limit

    def record_failure(self) -> None:
        attempts = int(cache.get(self.cache_key, 0)) + 1
        cache.set(self.cache_key, attempts, timeout=self.window_seconds)

    def reset(self) -> None:
        cache.delete(self.cache_key)

    @property
    def cache_key(self) -> str:
        identity = f"{self.client_ip}|{self.username}".encode()
        digest = hashlib.sha256(identity).hexdigest()
        return f"{self.cache_prefix}:{digest}"

    @property
    def client_ip(self) -> str:
        forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return str(forwarded_for).split(",")[0].strip()
        return str(self.request.META.get("REMOTE_ADDR", ""))
