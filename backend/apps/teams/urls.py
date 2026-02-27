from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from apps.teams.views import TeamViewSet, TeamMemberViewSet, TeamGitCredentialViewSet, TeamAPITokenViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")

members_router = nested_routers.NestedDefaultRouter(router, r"teams", lookup="team")
members_router.register(r"members", TeamMemberViewSet, basename="team-members")

credentials_router = nested_routers.NestedDefaultRouter(router, r"teams", lookup="team")
credentials_router.register(r"git-credentials", TeamGitCredentialViewSet, basename="team-git-credentials")

tokens_router = nested_routers.NestedDefaultRouter(router, r"teams", lookup="team")
tokens_router.register(r"api-tokens", TeamAPITokenViewSet, basename="team-api-tokens")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(members_router.urls)),
    path("", include(credentials_router.urls)),
    path("", include(tokens_router.urls)),
]
