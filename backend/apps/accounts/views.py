from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsSuperuser
from apps.accounts.serializers import UserSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsSuperuser]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": str(request.user.id),
            "username": request.user.username,
            "email": request.user.email,
            "is_superuser": request.user.is_superuser,
        })
