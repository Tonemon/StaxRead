from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.knowledge.views import GitCredentialViewSet, KnowledgeBaseViewSet, SourceViewSet

router = DefaultRouter()
router.register(r"knowledge-bases", KnowledgeBaseViewSet, basename="knowledgebase")
router.register(r"git-credentials", GitCredentialViewSet, basename="gitcredential")
router.register(r"sources", SourceViewSet, basename="source")

urlpatterns = [
    path("", include(router.urls)),
]
