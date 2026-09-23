from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PARENT = "PARENT", "Parent"
        CHILD = "CHILD", "Child"

    role = models.CharField(max_length=10, choices=Role, default=Role.CHILD)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        blank=True,
        null=True,
        limit_choices_to={"role": Role.PARENT},
    )
    display_name = models.CharField(max_length=80, blank=True)
    current_level = models.PositiveSmallIntegerField(default=1)
    total_xp = models.PositiveIntegerField(default=0)

    def clean(self) -> None:
        super().clean()
        if self.role == self.Role.PARENT:
            self.parent = None

    @property
    def is_parent(self) -> bool:
        return self.role == self.Role.PARENT

    @property
    def is_child(self) -> bool:
        return self.role == self.Role.CHILD
