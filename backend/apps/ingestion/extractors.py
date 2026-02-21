from typing import List, Dict


def extract_pdf_pages(file_path: str) -> List[Dict]:
    """
    Extract text from each page of a PDF.

    Returns:
        List of dicts with keys: page_number (1-indexed), text
    """
    import fitz

    pages = []
    doc = fitz.open(file_path)
    try:
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if text:
                pages.append({"page_number": i + 1, "text": text})
    finally:
        doc.close()
    return pages


def extract_epub_text(file_path: str) -> str:
    """
    Extract all text from an EPUB file, stripping HTML tags.

    Returns:
        Plain text string of the entire book.
    """
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(file_path, options={"ignore_ncx": True})
    parts = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "lxml")
        text = soup.get_text(separator="\n")
        text = text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)
