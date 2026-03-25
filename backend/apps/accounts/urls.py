from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    UserViewSet, MeView, PasswordChangeView,
    CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenBlacklistView, CSRFView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", CookieTokenBlacklistView.as_view(), name="token_blacklist"),
    path("csrf/", CSRFView.as_view(), name="csrf"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", PasswordChangeView.as_view(), name="change-password"),
    path("", include(router.urls)),
]
