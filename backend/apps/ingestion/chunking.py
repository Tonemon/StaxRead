from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
)


def chunk_text(text: str) -> List[str]:
    """Split text into chunks using RecursiveCharacterTextSplitter."""
    return _splitter.split_text(text)


def chunk_pages(pages: List[Dict]) -> List[Dict]:
    """
    Chunk a list of page dicts into smaller pieces, preserving page metadata.

    Args:
        pages: List of dicts with keys: page_number, text

    Returns:
        List of dicts with keys: chunk_index, text, page_number
    """
    chunks = []
    idx = 0
    for page in pages:
        for chunk_text in _splitter.split_text(page["text"]):
            chunks.append({
                "chunk_index": idx,
                "text": chunk_text,
                "page_number": page["page_number"],
            })
            idx += 1
    return chunks
