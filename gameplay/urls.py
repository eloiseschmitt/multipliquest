from django.urls import path

from gameplay.views import (
    ActiveSessionView,
    GameProgressView,
    MyProgressView,
    PlayerProgressView,
    SessionSummaryView,
    SubmitAnswerView,
)

urlpatterns = [
    path("progress/me/", MyProgressView.as_view(), name="progress-me"),
    path("progress/<int:player_id>/", PlayerProgressView.as_view(), name="progress-detail"),
    path("game/progress/", GameProgressView.as_view(), name="game-progress"),
    path("game/session/", ActiveSessionView.as_view(), name="game-session-active"),
    path("game/session/<int:session_id>/summary/", SessionSummaryView.as_view(), name="game-session-summary"),
    path("game/answer/", SubmitAnswerView.as_view(), name="game-submit-answer"),
]
