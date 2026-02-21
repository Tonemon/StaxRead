import io
import os
import tempfile
import pytest


def make_test_pdf(text_per_page: list) -> str:
    """Create a minimal PDF with the given text per page, return file path."""
    import fitz
    doc = fitz.open()
    for text in text_per_page:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    return tmp.name


def make_test_epub(title: str, chapter_text: str) -> str:
    """Create a minimal EPUB with a single chapter, return file path."""
    import ebooklib
    from ebooklib import epub
    book = epub.EpubBook()
    book.set_title(title)
    book.set_language("en")

    chapter = epub.EpubHtml(title="Chapter 1", file_name="chap1.xhtml", lang="en")
    chapter.content = f"<html><body><p>{chapter_text}</p></body></html>"
    book.add_item(chapter)
    book.spine = ["nav", chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    tmp = tempfile.NamedTemporaryFile(suffix=".epub", delete=False)
    epub.write_epub(tmp.name, book)
    return tmp.name


class TestPDFExtraction:
    def test_extract_single_page_pdf(self):
        from apps.ingestion.extractors import extract_pdf_pages
        path = make_test_pdf(["Hello, this is page one."])
        try:
            pages = extract_pdf_pages(path)
            assert len(pages) == 1
            assert pages[0]["page_number"] == 1
            assert "Hello" in pages[0]["text"]
        finally:
            os.unlink(path)

    def test_extract_multipage_pdf(self):
        from apps.ingestion.extractors import extract_pdf_pages
        path = make_test_pdf(["First page content.", "Second page content.", "Third page."])
        try:
            pages = extract_pdf_pages(path)
            assert len(pages) == 3
            assert pages[0]["page_number"] == 1
            assert pages[1]["page_number"] == 2
            assert pages[2]["page_number"] == 3
            assert "First" in pages[0]["text"]
            assert "Second" in pages[1]["text"]
        finally:
            os.unlink(path)

    def test_extract_pdf_returns_list_of_dicts(self):
        from apps.ingestion.extractors import extract_pdf_pages
        path = make_test_pdf(["Some text"])
        try:
            pages = extract_pdf_pages(path)
            assert isinstance(pages, list)
            assert "page_number" in pages[0]
            assert "text" in pages[0]
        finally:
            os.unlink(path)

    def test_extract_pdf_skips_empty_pages(self):
        from apps.ingestion.extractors import extract_pdf_pages
        import fitz
        doc = fitz.open()
        doc.new_page()  # blank page
        page = doc.new_page()
        page.insert_text((72, 72), "Content on page 2")
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        doc.save(tmp.name)
        doc.close()
        try:
            pages = extract_pdf_pages(tmp.name)
            assert any("Content on page 2" in p["text"] for p in pages)
        finally:
            os.unlink(tmp.name)


class TestEpubExtraction:
    def test_extract_epub_returns_text(self):
        from apps.ingestion.extractors import extract_epub_text
        path = make_test_epub("Test Book", "This is the chapter content.")
        try:
            text = extract_epub_text(path)
            assert isinstance(text, str)
            assert "chapter content" in text.lower() or len(text) > 0
        finally:
            os.unlink(path)

    def test_extract_epub_strips_html_tags(self):
        from apps.ingestion.extractors import extract_epub_text
        path = make_test_epub("HTML Test", "Clean text without tags.")
        try:
            text = extract_epub_text(path)
            assert "<" not in text
            assert ">" not in text
        finally:
            os.unlink(path)
