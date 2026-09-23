from django.urls import path

from accounts.views import ChildCreateView, CsrfTokenView, LoginView, LogoutView, MeView

urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("children/", ChildCreateView.as_view(), name="children-create"),
]
