"""
DeepFind Engine — Base Extractor

Abstract base class for all file text extractors.
Every extractor must implement extract(path) -> str.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

log = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Abstract extractor. Subclasses implement _extract_raw(path).
    The public extract() wraps it with error handling.
    """

    @abstractmethod
    def _extract_raw(self, path: Path) -> str:
        """Return raw extracted text. May raise on failure."""
        ...

    def extract(self, path: Path) -> str:
        """
        Public entry point. Returns cleaned text string.
        Raises ExtractorError on failure.
        """
        try:
            raw = self._extract_raw(path)
            return clean_text(raw)
        except ExtractorError:
            raise
        except PermissionError as exc:
            raise ExtractorError(f"Permission denied: {exc}") from exc
        except FileNotFoundError as exc:
            raise ExtractorError(f"File not found: {exc}") from exc
        except Exception as exc:
            raise ExtractorError(f"Extraction failed: {exc}") from exc


class ExtractorError(Exception):
    """Raised when a file cannot be extracted."""


# ── Text cleaning ──────────────────────────────────────────────────────────────

MAX_EXTRACTED_CHARS = 100_000   # hard cap on stored text


def clean_text(raw: str) -> str:
    """
    Normalize extracted text:
      - Remove null characters
      - Collapse excessive blank lines (max 2 consecutive)
      - Normalize Windows/Mac line endings to Unix
      - Strip leading/trailing whitespace
      - Hard-cap at MAX_EXTRACTED_CHARS
    """
    if not raw:
        return ""

    # Remove null bytes
    text = raw.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse 3+ blank lines into 2
    import re
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip overall
    text = text.strip()

    # Hard cap
    if len(text) > MAX_EXTRACTED_CHARS:
        text = text[:MAX_EXTRACTED_CHARS]

    return text
