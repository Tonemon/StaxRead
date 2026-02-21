import uuid
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="searcher", password="pw")


@pytest.fixture
def alice_client(alice):
    client = APIClient()
    client.force_authenticate(user=alice)
    return client


@pytest.fixture
def kb(alice):
    from apps.knowledge.models import KnowledgeBase
    return KnowledgeBase.objects.create(name="Search KB", owner=alice)


@pytest.fixture
def source(kb):
    from apps.knowledge.models import Source
    return Source.objects.create(
        kb=kb,
        title="Test Doc",
        source_type="pdf",
        status="ready",
    )


@pytest.fixture
def chunk(kb, source):
    from apps.knowledge.models import Chunk
    return Chunk.objects.create(
        kb=kb,
        source=source,
        text="The quick brown fox jumps over the lazy dog.",
        chunk_index=0,
    )


def make_sparse():
    v = MagicMock()
    v.indices = np.array([1, 5], dtype=np.int32)
    v.values = np.array([0.5, 0.3], dtype=np.float32)
    return v


def make_qdrant_result(chunk_id, score=0.85):
    result = MagicMock()
    result.id = str(chunk_id)
    result.score = score
    result.payload = {"kb_id": "some-kb-id", "text": "The quick brown fox..."}
    return result


@pytest.mark.django_db
class TestSearchEndpoint:
    def test_requires_authentication(self, db):
        response = APIClient().post(
            reverse("search"),
            {"query": "foxes", "kb_ids": []},
            format="json",
        )
        assert response.status_code == 401

    def test_returns_results_with_relevance_score(self, alice_client, kb, chunk):
        mock_qdrant = MagicMock()
        qdrant_result = make_qdrant_result(chunk.pk)
        mock_qdrant.query_points.return_value.points = [qdrant_result]

        with patch("apps.search.views.embed_query", return_value=(np.zeros(768), make_sparse())), \
             patch("apps.search.views.get_qdrant_client", return_value=mock_qdrant):
            response = alice_client.post(
                reverse("search"),
                {"query": "quick brown fox", "kb_ids": [str(kb.pk)]},
                format="json",
            )

        assert response.status_code == 200
        assert "results" in response.data
        assert len(response.data["results"]) == 1
        result = response.data["results"][0]
        assert "relevance_score" in result
        assert "text" in result

    def test_relevance_score_is_percentage(self, alice_client, kb, chunk):
        mock_qdrant = MagicMock()
        qdrant_result = make_qdrant_result(chunk.pk, score=0.75)
        mock_qdrant.query_points.return_value.points = [qdrant_result]

        with patch("apps.search.views.embed_query", return_value=(np.zeros(768), make_sparse())), \
             patch("apps.search.views.get_qdrant_client", return_value=mock_qdrant):
            response = alice_client.post(
                reverse("search"),
                {"query": "fox", "kb_ids": [str(kb.pk)]},
                format="json",
            )

        assert response.status_code == 200
        # Relevance score is cosine similarity 0-1 (displayed as percentage)
        score = response.data["results"][0]["relevance_score"]
        assert 0 <= score <= 1

    def test_rejects_unauthorized_kb_ids(self, alice_client, alice):
        from apps.knowledge.models import KnowledgeBase
        other_user = User.objects.create_user(username="bob_search", password="pw")
        bobs_kb = KnowledgeBase.objects.create(name="Bob's KB", owner=other_user)

        mock_qdrant = MagicMock()
        mock_qdrant.query_points.return_value.points = []

        with patch("apps.search.views.embed_query", return_value=(np.zeros(768), make_sparse())), \
             patch("apps.search.views.get_qdrant_client", return_value=mock_qdrant):
            response = alice_client.post(
                reverse("search"),
                {"query": "test", "kb_ids": [str(bobs_kb.pk)]},
                format="json",
            )

        # Should still return 200 but with no results (unauthorized KB is filtered out)
        assert response.status_code == 200
        # Qdrant should be called with empty kb filter (or authorized kb_ids only)
        # Since alice has no access to bob's KB, effective kb_ids is empty
        assert response.data["results"] == []

    def test_saves_search_to_history(self, alice_client, kb):
        from apps.search.models import SearchHistory
        mock_qdrant = MagicMock()
        mock_qdrant.query_points.return_value.points = []

        with patch("apps.search.views.embed_query", return_value=(np.zeros(768), make_sparse())), \
             patch("apps.search.views.get_qdrant_client", return_value=mock_qdrant):
            alice_client.post(
                reverse("search"),
                {"query": "saved query", "kb_ids": [str(kb.pk)]},
                format="json",
            )

        assert SearchHistory.objects.filter(query="saved query").exists()

    def test_empty_query_returns_400(self, alice_client, kb):
        response = alice_client.post(
            reverse("search"),
            {"query": "", "kb_ids": [str(kb.pk)]},
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestSearchHistory:
    def test_user_can_list_own_history(self, alice_client, alice, kb):
        from apps.search.models import SearchHistory
        SearchHistory.objects.create(user=alice, query="my search", kb_ids=[str(kb.pk)])

        response = alice_client.get(reverse("search-history"))
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["query"] == "my search"

    def test_user_cannot_see_others_history(self, alice_client, kb):
        from apps.search.models import SearchHistory
        other = User.objects.create_user(username="other_hist", password="pw")
        SearchHistory.objects.create(user=other, query="other query", kb_ids=[])

        response = alice_client.get(reverse("search-history"))
        assert response.status_code == 200
        queries = [h["query"] for h in response.data["results"]]
        assert "other query" not in queries
