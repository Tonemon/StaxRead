import pytest


LONG_TEXT = " ".join(["word"] * 300)  # ~1500 chars, will split at 512


class TestChunkText:
    def test_long_text_splits_into_multiple_chunks(self):
        from apps.ingestion.chunking import chunk_text
        chunks = chunk_text(LONG_TEXT)
        assert len(chunks) > 1

    def test_short_text_stays_single_chunk(self):
        from apps.ingestion.chunking import chunk_text
        short = "This is a short paragraph."
        chunks = chunk_text(short)
        assert len(chunks) == 1
        assert chunks[0] == short

    def test_chunks_are_strings(self):
        from apps.ingestion.chunking import chunk_text
        chunks = chunk_text(LONG_TEXT)
        assert all(isinstance(c, str) for c in chunks)

    def test_chunks_not_empty(self):
        from apps.ingestion.chunking import chunk_text
        chunks = chunk_text(LONG_TEXT)
        assert all(len(c) > 0 for c in chunks)

    def test_chunk_size_respected(self):
        from apps.ingestion.chunking import chunk_text
        chunks = chunk_text(LONG_TEXT)
        # All chunks should be at or under the 512-char limit
        assert all(len(c) <= 600 for c in chunks)  # some tolerance for overlap


class TestChunkPages:
    def test_chunk_pages_assigns_sequential_indices(self):
        from apps.ingestion.chunking import chunk_pages
        pages = [
            {"page_number": 1, "text": LONG_TEXT},
        ]
        chunks = chunk_pages(pages)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_pages_preserves_page_number(self):
        from apps.ingestion.chunking import chunk_pages
        pages = [
            {"page_number": 3, "text": "Content from page three."},
        ]
        chunks = chunk_pages(pages)
        assert chunks[0]["page_number"] == 3

    def test_chunk_pages_across_multiple_pages(self):
        from apps.ingestion.chunking import chunk_pages
        pages = [
            {"page_number": 1, "text": "Page one content."},
            {"page_number": 2, "text": "Page two content."},
        ]
        chunks = chunk_pages(pages)
        assert len(chunks) >= 2
        page_numbers = {c["page_number"] for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_chunk_pages_returns_list_of_dicts(self):
        from apps.ingestion.chunking import chunk_pages
        pages = [{"page_number": 1, "text": "Some text."}]
        chunks = chunk_pages(pages)
        assert isinstance(chunks, list)
        for chunk in chunks:
            assert "chunk_index" in chunk
            assert "text" in chunk
            assert "page_number" in chunk

    def test_chunk_pages_indices_are_sequential_across_pages(self):
        from apps.ingestion.chunking import chunk_pages
        pages = [
            {"page_number": 1, "text": LONG_TEXT},
            {"page_number": 2, "text": LONG_TEXT},
        ]
        chunks = chunk_pages(pages)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))
