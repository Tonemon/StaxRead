import pytest
from unittest.mock import patch, call


@pytest.fixture
def git_sources(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source

    User = get_user_model()
    user = User.objects.create_user(username="syncuser", password="pw")
    kb = KnowledgeBase.objects.create(name="Sync KB", owner=user)

    ready = Source.objects.create(
        kb=kb,
        title="Ready Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/a/b.git",
        status=Source.Status.READY,
    )
    pending = Source.objects.create(
        kb=kb,
        title="Pending Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/c/d.git",
        status=Source.Status.PENDING,
    )
    processing = Source.objects.create(
        kb=kb,
        title="Processing Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/e/f.git",
        status=Source.Status.PROCESSING,
    )
    pdf_source = Source.objects.create(
        kb=kb,
        title="A PDF",
        source_type=Source.SourceType.PDF,
        status=Source.Status.READY,
    )
    return {"ready": ready, "pending": pending, "processing": processing, "pdf": pdf_source}


@pytest.mark.django_db
def test_sync_dispatches_task_for_ready_git_sources(git_sources):
    with patch("apps.ingestion.tasks.sync.ingest_git.delay") as mock_delay:
        from apps.ingestion.tasks.sync import sync_all_git_sources
        sync_all_git_sources()

    mock_delay.assert_called_once_with(str(git_sources["ready"].pk))


@pytest.mark.django_db
def test_sync_skips_non_ready_git_sources(git_sources):
    with patch("apps.ingestion.tasks.sync.ingest_git.delay") as mock_delay:
        from apps.ingestion.tasks.sync import sync_all_git_sources
        sync_all_git_sources()

    called_ids = {c.args[0] for c in mock_delay.call_args_list}
    assert str(git_sources["pending"].pk) not in called_ids
    assert str(git_sources["processing"].pk) not in called_ids


@pytest.mark.django_db
def test_sync_skips_pdf_sources(git_sources):
    with patch("apps.ingestion.tasks.sync.ingest_git.delay") as mock_delay:
        from apps.ingestion.tasks.sync import sync_all_git_sources
        sync_all_git_sources()

    called_ids = {c.args[0] for c in mock_delay.call_args_list}
    assert str(git_sources["pdf"].pk) not in called_ids


@pytest.mark.django_db
def test_sync_dispatches_multiple_ready_repos(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source

    User = get_user_model()
    user = User.objects.create_user(username="multisync", password="pw")
    kb = KnowledgeBase.objects.create(name="Multi KB", owner=user)

    sources = [
        Source.objects.create(
            kb=kb,
            title=f"Repo {i}",
            source_type=Source.SourceType.GIT,
            git_url=f"https://github.com/x/y{i}.git",
            status=Source.Status.READY,
        )
        for i in range(3)
    ]

    with patch("apps.ingestion.tasks.sync.ingest_git.delay") as mock_delay:
        from apps.ingestion.tasks.sync import sync_all_git_sources
        sync_all_git_sources()

    assert mock_delay.call_count == 3
