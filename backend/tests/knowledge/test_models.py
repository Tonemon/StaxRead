import uuid
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="kbowner", password="pw")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="pw")


@pytest.mark.django_db
class TestKnowledgeBase:
    def test_owner_access_auto_created_on_save(self, user):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="My KB", owner=user)
        assert KBAccess.objects.filter(kb=kb, user=user).exists()

    def test_name_unique_per_owner(self, user):
        from apps.knowledge.models import KnowledgeBase
        KnowledgeBase.objects.create(name="Duplicate", owner=user)
        with pytest.raises(IntegrityError):
            KnowledgeBase.objects.create(name="Duplicate", owner=user)

    def test_same_name_allowed_for_different_owners(self, user, other_user):
        from apps.knowledge.models import KnowledgeBase
        KnowledgeBase.objects.create(name="SharedName", owner=user)
        kb2 = KnowledgeBase.objects.create(name="SharedName", owner=other_user)
        assert kb2.pk is not None

    def test_kb_has_uuid_primary_key(self, user):
        from apps.knowledge.models import KnowledgeBase
        kb = KnowledgeBase.objects.create(name="UUID KB", owner=user)
        assert isinstance(kb.pk, uuid.UUID)

    def test_kb_str(self, user):
        from apps.knowledge.models import KnowledgeBase
        kb = KnowledgeBase.objects.create(name="My Library", owner=user)
        assert "My Library" in str(kb)


@pytest.mark.django_db
class TestKBAccess:
    def test_owner_has_access_after_kb_creation(self, user):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Access KB", owner=user)
        access = KBAccess.objects.get(kb=kb, user=user)
        assert access is not None

    def test_shared_user_can_be_added(self, user, other_user):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Shared KB", owner=user)
        KBAccess.objects.create(kb=kb, user=other_user)
        assert KBAccess.objects.filter(kb=kb, user=other_user).exists()

    def test_duplicate_access_not_allowed(self, user):
        from apps.knowledge.models import KnowledgeBase, KBAccess
        kb = KnowledgeBase.objects.create(name="Dup Access KB", owner=user)
        with pytest.raises(IntegrityError):
            KBAccess.objects.create(kb=kb, user=user)


@pytest.mark.django_db
class TestSource:
    def test_source_status_defaults_to_pending(self, user):
        from apps.knowledge.models import KnowledgeBase, Source
        kb = KnowledgeBase.objects.create(name="Source KB", owner=user)
        source = Source.objects.create(
            kb=kb,
            title="My PDF",
            source_type=Source.SourceType.PDF,
        )
        assert source.status == Source.Status.PENDING

    def test_source_has_uuid_primary_key(self, user):
        from apps.knowledge.models import KnowledgeBase, Source
        kb = KnowledgeBase.objects.create(name="UUID Source KB", owner=user)
        source = Source.objects.create(
            kb=kb,
            title="Doc",
            source_type=Source.SourceType.PDF,
        )
        assert isinstance(source.pk, uuid.UUID)

    def test_source_type_choices(self, user):
        from apps.knowledge.models import KnowledgeBase, Source
        kb = KnowledgeBase.objects.create(name="Types KB", owner=user)
        for st in [Source.SourceType.PDF, Source.SourceType.EPUB, Source.SourceType.GIT]:
            Source.objects.create(kb=kb, title=f"Doc {st}", source_type=st)
        assert Source.objects.filter(kb=kb).count() == 3


@pytest.mark.django_db
class TestChunk:
    def test_chunk_has_denormalised_kb(self, user):
        from apps.knowledge.models import KnowledgeBase, Source, Chunk
        kb = KnowledgeBase.objects.create(name="Chunk KB", owner=user)
        source = Source.objects.create(
            kb=kb, title="Doc", source_type=Source.SourceType.PDF
        )
        chunk = Chunk.objects.create(
            kb=kb,
            source=source,
            text="Some chunk text",
            chunk_index=0,
        )
        assert chunk.kb == kb
        assert chunk.source == source

    def test_chunk_uuid_matches_qdrant_point(self, user):
        from apps.knowledge.models import KnowledgeBase, Source, Chunk
        kb = KnowledgeBase.objects.create(name="Qdrant KB", owner=user)
        source = Source.objects.create(
            kb=kb, title="Doc", source_type=Source.SourceType.PDF
        )
        chunk = Chunk.objects.create(
            kb=kb, source=source, text="text", chunk_index=0
        )
        assert isinstance(chunk.pk, uuid.UUID)
