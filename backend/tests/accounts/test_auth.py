import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="securepassword123",
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
    )


@pytest.mark.django_db
class TestLogin:
    def test_login_sets_auth_cookies(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data == {"detail": "Login successful."}
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_login_wrong_password_rejected(self, api_client, user):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_rejected(self, api_client, db):
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "nobody", "password": "whatever"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_rotates_access_cookie(self, api_client, user):
        # Login stores the refresh_token cookie in the client's cookie jar.
        api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        response = api_client.post(reverse("token_refresh"))
        assert response.status_code == 200
        assert response.data == {"detail": "Token refreshed."}
        assert "access_token" in response.cookies

    def test_invalid_refresh_token_rejected(self, api_client, db):
        api_client.cookies["refresh_token"] = "notarealtoken"
        response = api_client.post(reverse("token_refresh"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, user):
        api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "securepassword123"},
            format="json",
        )
        response = api_client.post(reverse("token_blacklist"))
        assert response.status_code == 204

        # Blacklisted token must be rejected on next refresh attempt.
        retry = api_client.post(reverse("token_refresh"))
        assert retry.status_code == 401


@pytest.mark.django_db
class TestMeEndpoint:
    def test_me_returns_user_info(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("me"))
        assert response.status_code == 200
        assert response.data["username"] == "testuser"
        assert response.data["is_superuser"] is False
        assert "id" in response.data

    def test_me_unauthenticated_rejected(self, api_client):
        response = api_client.get(reverse("me"))
        assert response.status_code == 401

    def test_me_superuser_flag(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        response = api_client.get(reverse("me"))
        assert response.status_code == 200
        assert response.data["is_superuser"] is True


@pytest.mark.django_db
class TestUserModel:
    def test_user_has_uuid_primary_key(self, user):
        import uuid
        assert isinstance(user.pk, uuid.UUID)

    def test_user_is_not_superuser_by_default(self, user):
        assert not user.is_superuser

    def test_superuser_has_is_superuser_flag(self, superuser):
        assert superuser.is_superuser
