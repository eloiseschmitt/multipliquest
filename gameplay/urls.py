from django.urls import path

from gameplay.views import MyProgressView, PlayerProgressView

urlpatterns = [
    path("progress/me/", MyProgressView.as_view(), name="progress-me"),
    path("progress/<int:player_id>/", PlayerProgressView.as_view(), name="progress-detail"),
]
