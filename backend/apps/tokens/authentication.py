from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.tokens.models import APIToken


class APITokenAuthentication(BaseAuthentication):
    """
    Authenticate requests using a Bearer token issued via the API token system.
    Header format:  Authorization: Bearer stax_<hex>
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None  # Let the next auth class try

        raw_token = auth_header[len("Bearer "):].strip()
        if not raw_token.startswith("stax_"):
            return None  # Not our token format

        token = APIToken.authenticate(raw_token)
        if token is None:
            raise AuthenticationFailed("Invalid or expired API token.")

        # Record usage
        ip = self._get_client_ip(request)
        APIToken.objects.filter(pk=token.pk).update(
            last_used_at=timezone.now(),
            last_used_ip=ip,
        )

        return (token.user, token)  # (user, auth) — DRF standard

    def _get_client_ip(self, request) -> str | None:
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
