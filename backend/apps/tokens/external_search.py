import logging

from django.conf import settings
from qdrant_client.models import (
    Filter, FieldCondition, MatchAny,
    Prefetch, FusionQuery, Fusion, SparseVector,
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ingestion.embeddings import embed_query
from apps.ingestion.qdrant_client import get_qdrant_client
from apps.knowledge.models import KnowledgeBase, Chunk
from apps.search.models import SearchHistory
from apps.tokens.authentication import APITokenAuthentication

logger = logging.getLogger(__name__)


class ExternalSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1)
    kb_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list,
        help_text="Optional. Limit search to specific KB IDs within the token's scope.",
    )
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)


class ExternalSearchView(APIView):
    """
    POST /api/external/search/

    Perform a hybrid semantic search using an API token.
    Header: Authorization: Bearer stax_<token>

    Token scope determines accessible KBs. Empty scope = all user's KBs.
    """
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ExternalSearchRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        query = ser.validated_data["query"]
        requested_kb_ids = [str(uid) for uid in ser.validated_data["kb_ids"]]
        limit = ser.validated_data["limit"]

        token = request.auth

        if token.team_id:
            # Team token: scope to this team's KBs only
            from apps.knowledge.models import KnowledgeBase as KB
            all_team_kb_ids = set(
                str(pk) for pk in KB.objects.filter(team_id=token.team_id).values_list("id", flat=True)
            )
            scoped_kbs = token.knowledge_bases.values_list("id", flat=True)
            if scoped_kbs:
                token_kb_ids = {str(pk) for pk in scoped_kbs} & all_team_kb_ids
            else:
                token_kb_ids = all_team_kb_ids
        else:
            # Personal token: use user-based access
            from apps.teams.access import get_accessible_kbs
            accessible_kb_ids = set(
                str(pk) for pk in get_accessible_kbs(request.user).values_list("id", flat=True)
            )
            scoped_kbs = token.knowledge_bases.values_list("id", flat=True)
            if scoped_kbs:
                token_kb_ids = {str(pk) for pk in scoped_kbs} & accessible_kb_ids
            else:
                token_kb_ids = accessible_kb_ids

        if requested_kb_ids:
            effective_kb_ids = [kid for kid in requested_kb_ids if kid in token_kb_ids]
        else:
            effective_kb_ids = list(token_kb_ids)

        if not effective_kb_ids:
            return Response({"results": [], "query": query})

        dense_vec, sparse_vec = embed_query(query)

        kb_filter = Filter(
            must=[FieldCondition(key="kb_id", match=MatchAny(any=effective_kb_ids))]
        )

        qdrant = get_qdrant_client()
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
            })

        SearchHistory.objects.create(
            user=request.user,
            query=query,
            kb_ids=effective_kb_ids,
        )

        return Response({"results": results, "query": query})
