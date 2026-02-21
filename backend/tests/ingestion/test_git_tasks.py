import os
import uuid
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def git_source(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source, GitCredential

    User = get_user_model()
    user = User.objects.create_user(username="gituser", password="pw")
    kb = KnowledgeBase.objects.create(name="Git KB", owner=user)

    cred = GitCredential(user=user, label="My Repo")
    cred.set_pat("ghp_TestToken123")
    cred.save()

    source = Source.objects.create(
        kb=kb,
        title="My Git Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/example/repo.git",
        git_credential=cred,
        git_branch="main",
    )
    return source


@pytest.fixture
def git_source_no_cred(db):
    from django.contrib.auth import get_user_model
    from apps.knowledge.models import KnowledgeBase, Source

    User = get_user_model()
    user = User.objects.create_user(username="gituser2", password="pw")
    kb = KnowledgeBase.objects.create(name="Public KB", owner=user)
    source = Source.objects.create(
        kb=kb,
        title="Public Repo",
        source_type=Source.SourceType.GIT,
        git_url="https://github.com/example/public.git",
        git_branch="main",
    )
    return source


@pytest.mark.django_db
def test_clone_uses_pat_in_url(git_source):
    from apps.ingestion.tasks.git import _build_auth_url
    url = _build_auth_url(git_source)
    assert "ghp_TestToken123" in url
    assert "github.com" in url


@pytest.mark.django_db
def test_clone_without_credentials_uses_plain_url(git_source_no_cred):
    from apps.ingestion.tasks.git import _build_auth_url
    url = _build_auth_url(git_source_no_cred)
    assert url == git_source_no_cred.git_url


@pytest.mark.django_db
def test_discover_files_finds_markdown_and_pdf(tmp_path):
    from apps.ingestion.tasks.git import _discover_files
    (tmp_path / "README.md").write_text("# Hello")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF")
    (tmp_path / "skip.txt").write_text("skip")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "notes.md").write_text("# Notes")

    files = _discover_files(str(tmp_path))
    extensions = {os.path.splitext(f)[1] for f in files}
    assert ".md" in extensions
    assert ".pdf" in extensions
    assert ".txt" not in extensions
    assert len(files) == 3


@pytest.mark.django_db
def test_extract_markdown_returns_text_and_heading(tmp_path):
    from apps.ingestion.tasks.git import extract_markdown
    md_file = tmp_path / "doc.md"
    md_file.write_text("# My Heading\n\nSome body text here.\n")

    result = extract_markdown(str(md_file))
    assert result["text"] != ""
    assert result["heading"] == "My Heading"


@pytest.mark.django_db
def test_ingest_git_sets_status_ready(git_source):
    from apps.knowledge.models import Source

    def make_sparse():
        v = MagicMock()
        v.indices = np.array([1], dtype=np.int32)
        v.values = np.array([0.5], dtype=np.float32)
        return v

    mock_qdrant = MagicMock()
    with patch("apps.ingestion.tasks.git.subprocess.run"), \
         patch("apps.ingestion.tasks.git._discover_files", return_value=["/repo/README.md"]), \
         patch("apps.ingestion.tasks.git.extract_markdown", return_value={"text": "Some readme text.", "heading": "README"}), \
         patch("apps.ingestion.tasks.git.chunk_text", return_value=["Some readme text."]), \
         patch("apps.ingestion.tasks.git.embed_documents", return_value=(np.zeros((1, 768)), [make_sparse()])), \
         patch("apps.ingestion.tasks.common.get_qdrant_client", return_value=mock_qdrant), \
         patch("os.path.exists", return_value=False):
        from apps.ingestion.tasks.git import ingest_git
        ingest_git(str(git_source.pk))

    git_source.refresh_from_db()
    assert git_source.status == Source.Status.READY


@pytest.mark.django_db
def test_ingest_git_sets_error_on_failure(git_source):
    from apps.knowledge.models import Source

    with patch("apps.ingestion.tasks.git.subprocess.run", side_effect=Exception("git clone failed")):
        from apps.ingestion.tasks.git import ingest_git
        ingest_git(str(git_source.pk))

    git_source.refresh_from_db()
    assert git_source.status == Source.Status.ERROR
    assert "git clone failed" in git_source.error_message
