"""
DeepFind Engine — Text Extraction Dispatcher

Routes files to the correct extractor based on extension.
Also provides text chunking for the file_chunks table.

Usage:
    from extractors.text_extractor_dispatcher import extract_file, chunk_text
"""

import logging
from pathlib import Path

from extractors.base_extractor import ExtractorError
from extractors.text_extractor import TextExtractor
from extractors.pdf_extractor import PdfExtractor
from extractors.docx_extractor import DocxExtractor
from config import SUPPORTED_TEXT_EXTENSIONS, CHUNK_SIZE_WORDS, MAX_CHUNKS_PER_FILE

log = logging.getLogger(__name__)

# ── Extractor instances (stateless — safe to reuse) ────────────────────────────
_TEXT_EXTRACTOR = TextExtractor()
_PDF_EXTRACTOR  = PdfExtractor()
_DOCX_EXTRACTOR = DocxExtractor()


def get_extractor(extension: str):
    """
    Return the correct extractor for the given file extension.
    Returns None if the extension is not supported.
    """
    ext = extension.lower()
    if ext == ".pdf":
        return _PDF_EXTRACTOR
    if ext == ".docx":
        return _DOCX_EXTRACTOR
    if ext in SUPPORTED_TEXT_EXTENSIONS:
        return _TEXT_EXTRACTOR
    return None


def extract_file(path: Path) -> tuple[str, str | None]:
    """
    Extract text from a file.

    Returns:
        (text, error_message)
        - On success: (cleaned_text, None)
        - On failure: ("", error_message)
    """
    ext = path.suffix.lower()
    extractor = get_extractor(ext)

    if extractor is None:
        return "", f"Unsupported extension: {ext}"

    try:
        text = extractor.extract(path)
        return text, None
    except ExtractorError as exc:
        return "", str(exc)
    except Exception as exc:
        return "", f"Unexpected error: {exc}"


# ── Chunking ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size_words: int = CHUNK_SIZE_WORDS,
               max_chunks: int = MAX_CHUNKS_PER_FILE) -> list[str]:
    """
    Split text into word-based chunks for future semantic embedding.

    Args:
        text:             Cleaned extracted text
        chunk_size_words: Target words per chunk (default from config)
        max_chunks:       Maximum chunks to produce (default from config)

    Returns:
        List of chunk strings.
    """
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    i = 0
    while i < len(words) and len(chunks) < max_chunks:
        chunk_words = words[i : i + chunk_size_words]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        i += chunk_size_words

    return chunks
