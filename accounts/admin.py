from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class MultipliQuestUserAdmin(UserAdmin):  # type: ignore[type-arg]
    fieldsets = UserAdmin.fieldsets + (  # type: ignore[operator]
        (
            "MultipliQuest",
            {
                "fields": (
                    "role",
                    "parent",
                    "display_name",
                    "current_level",
                    "total_xp",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "MultipliQuest",
            {
                "fields": (
                    "role",
                    "parent",
                    "display_name",
                )
            },
        ),
    )
    list_display = ("username", "display_name", "role", "parent", "current_level", "total_xp", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "display_name")
