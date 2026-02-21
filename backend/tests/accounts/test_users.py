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
        username="regularuser",
        email="user@example.com",
        password="password123",
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
    )


@pytest.fixture
def superuser_client(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def user_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestUserListCreate:
    def test_superuser_can_list_users(self, superuser_client, user):
        response = superuser_client.get(reverse("user-list"))
        assert response.status_code == 200
        assert response.data["count"] >= 2  # superuser + regular user

    def test_regular_user_cannot_list_users(self, user_client):
        response = user_client.get(reverse("user-list"))
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_users(self, api_client, db):
        response = api_client.get(reverse("user-list"))
        assert response.status_code == 401

    def test_superuser_can_create_user(self, superuser_client, db):
        response = superuser_client.post(
            reverse("user-list"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpassword123",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["username"] == "newuser"
        assert "password" not in response.data

    def test_regular_user_cannot_create_user(self, user_client):
        response = user_client.post(
            reverse("user-list"),
            {"username": "hacker", "email": "h@h.com", "password": "pw"},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserDetail:
    def test_superuser_can_retrieve_user(self, superuser_client, user):
        response = superuser_client.get(reverse("user-detail", kwargs={"pk": user.pk}))
        assert response.status_code == 200
        assert response.data["username"] == "regularuser"

    def test_superuser_can_deactivate_user(self, superuser_client, user):
        response = superuser_client.patch(
            reverse("user-detail", kwargs={"pk": user.pk}),
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert not user.is_active

    def test_regular_user_cannot_access_user_detail(self, user_client, superuser):
        response = user_client.get(
            reverse("user-detail", kwargs={"pk": superuser.pk})
        )
        assert response.status_code == 403

    def test_password_not_exposed_in_response(self, superuser_client, user):
        response = superuser_client.get(reverse("user-detail", kwargs={"pk": user.pk}))
        assert response.status_code == 200
        assert "password" not in response.data
