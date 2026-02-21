import pytest
from django.test import override_settings

FERNET_KEY = "lGOZ0YVpK6Q4TqrPFZQgI_XOGB85bZ9RxP0TLrH_RiA="


@pytest.fixture(autouse=True)
def set_fernet_key(settings):
    settings.STAXREAD_FERNET_KEY = FERNET_KEY


def test_encrypt_returns_string():
    from apps.knowledge.encryption import encrypt
    result = encrypt("my-secret-token")
    assert isinstance(result, str)
    assert result != "my-secret-token"


def test_decrypt_recovers_original():
    from apps.knowledge.encryption import encrypt, decrypt
    plaintext = "ghp_MyPersonalAccessToken12345"
    ciphertext = encrypt(plaintext)
    assert decrypt(ciphertext) == plaintext


def test_same_input_produces_different_ciphertext():
    from apps.knowledge.encryption import encrypt
    plaintext = "same-token"
    ct1 = encrypt(plaintext)
    ct2 = encrypt(plaintext)
    # Fernet uses random IV, so ciphertexts should differ
    assert ct1 != ct2


@pytest.mark.django_db
def test_git_credential_set_and_get_pat():
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import GitCredential

    User = get_user_model()
    user = User.objects.create_user(username="repoowner", password="pw")
    cred = GitCredential(user=user, label="My GitHub")
    cred.set_pat("ghp_SomeToken123")
    cred.save()

    fetched = GitCredential.objects.get(pk=cred.pk)
    assert fetched.get_pat() == "ghp_SomeToken123"
    assert fetched.pat_encrypted != "ghp_SomeToken123"


@pytest.mark.django_db
def test_git_credential_has_uuid_primary_key():
    import uuid
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import GitCredential

    User = get_user_model()
    user = User.objects.create_user(username="owner2", password="pw")
    cred = GitCredential(user=user, label="Cred")
    cred.set_pat("token")
    cred.save()
    assert isinstance(cred.pk, uuid.UUID)
