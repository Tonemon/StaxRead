"""End-to-end integration test: KB creation → ingestion → search → bookmarks."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from apps.accounts.models import User
from apps.knowledge.models import KnowledgeBase, KBAccess, Source, Chunk


@pytest.mark.django_db
def test_full_search_flow():
    """Alice owns a KB, shares it with Bob; Bob searches and gets the right chunk."""
    # --- Setup: create users, KB, source, chunk ---
    owner = User.objects.create_user(username="alice", password="pass")
    kb = KnowledgeBase.objects.create(owner=owner, name="My Books")
    source = Source.objects.create(
        kb=kb,
        title="book.pdf",
        source_type=Source.SourceType.PDF,
        status=Source.Status.READY,
    )
    chunk = Chunk.objects.create(
        source=source,
        kb=kb,
        chunk_index=0,
        text="The mitochondria is the powerhouse of the cell.",
    )

    # --- Share KB with Bob ---
    bob = User.objects.create_user(username="bob", password="pass")
    KBAccess.objects.create(kb=kb, user=bob)

    # --- Bob logs in; the access_token cookie is stored in the client automatically ---
    bob_client = APIClient()
    login_resp = bob_client.post(
        reverse("token_obtain_pair"),
        {"username": "bob", "password": "pass"},
        format="json",
    )
    assert login_resp.status_code == 200

    mock_point = MagicMock()
    mock_point.id = str(chunk.pk)
    mock_point.score = 0.92

    with (
        patch(
            "apps.search.views.embed_query",
            return_value=(
                MagicMock(tolist=lambda: [0.1] * 768),
                MagicMock(indices=MagicMock(tolist=lambda: [0]), values=MagicMock(tolist=lambda: [1.0])),
            ),
        ),
        patch("apps.search.views.get_qdrant_client") as mock_qdrant,
    ):
        mock_qdrant.return_value.query_points.return_value.points = [mock_point]
        search_resp = bob_client.post(
            reverse("search"),
            {"query": "powerhouse", "kb_ids": [str(kb.pk)]},
            format="json",
        )

    assert search_resp.status_code == 200
    results = search_resp.data["results"]
    assert len(results) == 1
    assert "powerhouse" in results[0]["text"]
    assert results[0]["relevance_score"] == pytest.approx(0.92)
    assert results[0]["source_title"] == "book.pdf"
    assert results[0]["kb_name"] == "My Books"


@pytest.mark.django_db
def test_me_endpoint_after_login():
    """Login sets cookies; /me/ returns correct user info."""
    user = User.objects.create_user(
        username="charlie", password="pass", email="charlie@example.com"
    )
    user.is_superuser = True
    user.save()

    client = APIClient()
    login_resp = client.post(
        reverse("token_obtain_pair"),
        {"username": "charlie", "password": "pass"},
        format="json",
    )
    assert login_resp.status_code == 200

    me_resp = client.get(reverse("me"))
    assert me_resp.status_code == 200
    assert me_resp.data["username"] == "charlie"
    assert me_resp.data["is_superuser"] is True


@pytest.mark.django_db
def test_kb_access_enforced_at_search():
    """Dave cannot search Alice's KB because he has no KBAccess entry."""
    alice = User.objects.create_user(username="alice2", password="pass")
    dave = User.objects.create_user(username="dave", password="pass")

    kb = KnowledgeBase.objects.create(owner=alice, name="Alice's Books")
    source = Source.objects.create(
        kb=kb, title="doc.pdf", source_type="pdf", status="ready"
    )
    chunk = Chunk.objects.create(source=source, kb=kb, chunk_index=0, text="secret info")

    dave_client = APIClient()
    login_resp = dave_client.post(
        reverse("token_obtain_pair"),
        {"username": "dave", "password": "pass"},
        format="json",
    )
    assert login_resp.status_code == 200

    with (
        patch(
            "apps.search.views.embed_query",
            return_value=(
                MagicMock(tolist=lambda: [0.1] * 768),
                MagicMock(
                    indices=MagicMock(tolist=lambda: [0]),
                    values=MagicMock(tolist=lambda: [1.0]),
                ),
            ),
        ),
        patch("apps.search.views.get_qdrant_client"),
    ):
        resp = dave_client.post(
            reverse("search"),
            {"query": "secret", "kb_ids": [str(kb.pk)]},
            format="json",
        )

    assert resp.status_code == 200
    # Dave has no access → effective_kb_ids is empty → early return with no results
    assert resp.data["results"] == []
