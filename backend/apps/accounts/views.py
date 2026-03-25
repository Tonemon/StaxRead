from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError

from apps.common.permissions import IsSuperuser
from apps.accounts.serializers import UserSerializer, ProfileSerializer, PasswordChangeSerializer

User = get_user_model()


def _set_auth_cookies(response, access, refresh=None):
    response.set_cookie(
        'access_token', access,
        max_age=15 * 60, httponly=True, secure=True, samesite='Lax', path='/',
    )
    if refresh is not None:
        response.set_cookie(
            'refresh_token', refresh,
            max_age=7 * 24 * 3600, httponly=True, secure=True, samesite='Lax', path='/api/auth/',
        )


def _clear_auth_cookies(response):
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/api/auth/')


class StaxReadTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Check before simplejwt so we can return a specific message for disabled accounts.
        username = attrs.get(self.username_field, "")
        password = attrs.get("password", "")
        try:
            user = User.objects.get(**{self.username_field: username})
            if user.check_password(password) and not user.is_active:
                raise AuthenticationFailed(
                    "This account is disabled. Please contact an administrator.",
                    "account_disabled",
                )
        except User.DoesNotExist:
            pass
        return super().validate(attrs)


@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenObtainPairView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = StaxReadTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = Response({'detail': 'Login successful.'})
        _set_auth_cookies(response, str(data['access']), str(data['refresh']))
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get('refresh_token')
        if not raw_refresh:
            return Response({'detail': 'No refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={'refresh': raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            response = Response({'detail': 'Refresh token is invalid or expired.'}, status=status.HTTP_401_UNAUTHORIZED)
            _clear_auth_cookies(response)
            return response
        data = serializer.validated_data
        response = Response({'detail': 'Token refreshed.'})
        refresh_to_set = str(data['refresh']) if 'refresh' in data else None
        _set_auth_cookies(response, str(data['access']), refresh_to_set)
        return response


@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenBlacklistView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get('refresh_token')
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_auth_cookies(response)
        return response


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({'detail': 'CSRF cookie set.'})


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
