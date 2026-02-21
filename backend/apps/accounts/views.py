from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsSuperuser
from apps.accounts.serializers import UserSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsSuperuser]
