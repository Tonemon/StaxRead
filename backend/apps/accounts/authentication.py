from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

_csrf_check = CsrfViewMiddleware(get_response=lambda request: None)


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            raise InvalidToken('Access token is invalid or expired.')
        self.enforce_csrf(request)
        return self.get_user(validated_token), validated_token

    def enforce_csrf(self, request):
        reason = _csrf_check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
