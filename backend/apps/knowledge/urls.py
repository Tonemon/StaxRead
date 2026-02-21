from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.knowledge.views import KnowledgeBaseViewSet

router = DefaultRouter()
router.register(r"knowledge-bases", KnowledgeBaseViewSet, basename="knowledgebase")

urlpatterns = [
    path("", include(router.urls)),
]
