from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.common.permissions import IsSuperuser
from apps.accounts.serializers import UserSerializer, ProfileSerializer, PasswordChangeSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsSuperuser]

    def perform_update(self, serializer):
        user = self.get_object()
        was_superuser = user.is_superuser
        updated = serializer.save()
        if was_superuser and not updated.is_superuser:
            self._blacklist_all_tokens(updated)

    @staticmethod
    def _blacklist_all_tokens(user):
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        tokens = OutstandingToken.objects.filter(user=user)
        BlacklistedToken.objects.bulk_create(
            [BlacklistedToken(token=t) for t in tokens],
            ignore_conflicts=True,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
