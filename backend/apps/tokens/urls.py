from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tokens.views import APITokenViewSet
from apps.tokens.external_search import ExternalSearchView

router = DefaultRouter()
router.register(r"api-tokens", APITokenViewSet, basename="apitoken")

urlpatterns = router.urls + [
    path("external/search/", ExternalSearchView.as_view(), name="external-search"),
]
