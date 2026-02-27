from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from apps.teams.views import TeamViewSet, TeamMemberViewSet

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")

members_router = nested_routers.NestedDefaultRouter(router, r"teams", lookup="team")
members_router.register(r"members", TeamMemberViewSet, basename="team-members")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(members_router.urls)),
]
