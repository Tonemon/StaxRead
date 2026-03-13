import logging
from collections import defaultdict

from rest_framework import serializers, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.knowledge.models import Chunk
from apps.search.models import SearchHistory
from apps.ingestion.embeddings import embed_query
from apps.ingestion.qdrant_client import get_qdrant_client
from apps.teams.access import get_accessible_kbs

logger = logging.getLogger(__name__)


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1)
    kb_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "query", "kb_ids", "created_at"]


class SearchView(APIView):
    def post(self, request):
        ser = SearchRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        query = ser.validated_data["query"]
        requested_kb_ids = [str(uid) for uid in ser.validated_data["kb_ids"]]
        limit = ser.validated_data["limit"]

        # Intersect with accessible KBs
        accessible_kb_ids = set(
            str(pk) for pk in get_accessible_kbs(request.user).values_list("id", flat=True)
        )

        if requested_kb_ids:
            effective_kb_ids = [kid for kid in requested_kb_ids if kid in accessible_kb_ids]
        else:
            effective_kb_ids = list(accessible_kb_ids)

        if not effective_kb_ids:
            return Response({"results": [], "query": query})

        # Embed query
        dense_vec, sparse_vec = embed_query(query)

        # Hybrid search via Qdrant RRF
        from qdrant_client.models import (
            Filter, FieldCondition, MatchAny,
            Prefetch, FusionQuery, Fusion,
            SparseVector, NamedSparseVector, NamedVector,
            QueryRequest,
        )

        kb_filter = Filter(
            must=[FieldCondition(key="kb_id", match=MatchAny(any=effective_kb_ids))]
        )

        qdrant = get_qdrant_client()
        from django.conf import settings

        search_result = qdrant.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            prefetch=[
                Prefetch(
                    query=dense_vec.tolist(),
                    using="dense",
                    filter=kb_filter,
                    limit=limit * 2,
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist(),
                    ),
                    using="sparse",
                    filter=kb_filter,
                    limit=limit * 2,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
        )

        # Enrich from PostgreSQL
        point_ids = [p.id for p in search_result.points]
        chunks_map = {
            str(c.pk): c
            for c in Chunk.objects.filter(pk__in=point_ids).select_related("source", "kb")
        }

        results = []
        for point in search_result.points:
            chunk = chunks_map.get(str(point.id))
            if chunk is None:
                continue
            results.append({
                "chunk_id": str(chunk.pk),
                "text": chunk.text,
                "relevance_score": round(point.score, 4),
                "source_title": chunk.source.title,
                "source_id": str(chunk.source_id),
                "kb_id": str(chunk.kb_id),
                "kb_name": chunk.kb.name,
                "metadata": chunk.metadata,
                "context_before": [],
                "context_after": [],
            })

        # Fetch adjacent context chunks
        context_n = getattr(request.user, "context_chunks", 1)
        if context_n > 0 and results:
            from django.db.models import Q
            context_q = Q()
            for r in results:
                chunk = chunks_map.get(r["chunk_id"])
                if chunk:
                    context_q |= Q(
                        source_id=chunk.source_id,
                        chunk_index__gte=chunk.chunk_index - context_n,
                        chunk_index__lte=chunk.chunk_index + context_n,
                    )

            ctx_by_source: dict = defaultdict(dict)
            for c in Chunk.objects.filter(context_q).only("id", "source_id", "chunk_index", "text", "metadata"):
                ctx_by_source[str(c.source_id)][c.chunk_index] = c

            for r in results:
                chunk = chunks_map.get(r["chunk_id"])
                if not chunk:
                    continue
                src = ctx_by_source[str(chunk.source_id)]
                idx = chunk.chunk_index
                r["context_before"] = [
                    {"chunk_id": str(src[idx - i].pk), "text": src[idx - i].text, "metadata": src[idx - i].metadata}
                    for i in range(1, context_n + 1)
                    if (idx - i) in src
                ]
                r["context_after"] = [
                    {"chunk_id": str(src[idx + i].pk), "text": src[idx + i].text, "metadata": src[idx + i].metadata}
                    for i in range(1, context_n + 1)
                    if (idx + i) in src
                ]

        # Save to history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            kb_ids=effective_kb_ids,
        )

        return Response({"results": results, "query": query})


class SearchHistoryView(ListAPIView):
    serializer_class = SearchHistorySerializer

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)
