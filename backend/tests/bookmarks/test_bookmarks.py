import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="bookmark_alice", password="pw")


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bookmark_bob", password="pw")


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def bob_client(bob):
    client = APIClient()
    client.force_authenticate(user=bob)
    return client


@pytest.fixture
def chunk(db):
    from apps.knowledge.models import KnowledgeBase, Source, Chunk
    user = User.objects.create_user(username="chunk_owner_bk", password="pw")
    kb = KnowledgeBase.objects.create(name="BK KB", owner=user)
    source = Source.objects.create(kb=kb, title="Doc", source_type="pdf")
    return Chunk.objects.create(kb=kb, source=source, text="Some text", chunk_index=0)


@pytest.mark.django_db
class TestBookmarkCategory:
    def test_create_category(self, alice_client):
        response = alice_client.post(
            reverse("bookmarkcategory-list"),
            {"name": "Research", "description": "Research notes"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["name"] == "Research"

    def test_user_only_sees_own_categories(self, alice_client, bob_client):
        alice_client.post(
            reverse("bookmarkcategory-list"),
            {"name": "Alice's Category"},
            format="json",
        )
        bob_client.post(
            reverse("bookmarkcategory-list"),
            {"name": "Bob's Category"},
            format="json",
        )
        response = alice_client.get(reverse("bookmarkcategory-list"))
        names = [c["name"] for c in response.data]
        assert "Alice's Category" in names
        assert "Bob's Category" not in names

    def test_unauthenticated_rejected(self, db):
        response = APIClient().get(reverse("bookmarkcategory-list"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestBookmark:
    def test_create_bookmark(self, alice_client, alice, chunk):
        from apps.bookmarks.models import BookmarkCategory
        cat = BookmarkCategory.objects.create(user=alice, name="Faves")
        response = alice_client.post(
            reverse("bookmark-list"),
            {
                "chunk": str(chunk.pk),
                "category": str(cat.pk),
                "note": "Very interesting!",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["note"] == "Very interesting!"

    def test_user_only_sees_own_bookmarks(self, alice_client, bob_client, alice, bob, chunk):
        from apps.bookmarks.models import BookmarkCategory, Bookmark
        alice_cat = BookmarkCategory.objects.create(user=alice, name="Alice Faves")
        bob_cat = BookmarkCategory.objects.create(user=bob, name="Bob Faves")
        Bookmark.objects.create(user=alice, chunk=chunk, category=alice_cat)
        Bookmark.objects.create(user=bob, chunk=chunk, category=bob_cat)

        response = alice_client.get(reverse("bookmark-list"))
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_create_bookmark_without_category(self, alice_client, chunk):
        response = alice_client.post(
            reverse("bookmark-list"),
            {"chunk": str(chunk.pk)},
            format="json",
        )
        assert response.status_code == 201

    def test_unauthenticated_rejected(self, db):
        response = APIClient().get(reverse("bookmark-list"))
        assert response.status_code == 401

    def test_filter_bookmarks_by_category(self, alice_client, alice, chunk):
        from apps.bookmarks.models import BookmarkCategory, Bookmark
        from apps.knowledge.models import KnowledgeBase, Source, Chunk
        user = User.objects.create_user(username="extra_user_bk", password="pw")
        kb = KnowledgeBase.objects.create(name="Extra KB", owner=user)
        source = Source.objects.create(kb=kb, title="Doc2", source_type="pdf")
        chunk2 = Chunk.objects.create(kb=kb, source=source, text="Other text", chunk_index=0)

        cat1 = BookmarkCategory.objects.create(user=alice, name="Cat 1")
        cat2 = BookmarkCategory.objects.create(user=alice, name="Cat 2")
        Bookmark.objects.create(user=alice, chunk=chunk, category=cat1)
        Bookmark.objects.create(user=alice, chunk=chunk2, category=cat2)

        response = alice_client.get(
            reverse("bookmark-list"), {"category": str(cat1.pk)}
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
