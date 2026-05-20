"""
DeepFind Engine — PDF Text Extractor

Uses pypdf for local, offline PDF text extraction.
No cloud APIs. No OCR (Step 9 scope).

Handles:
  - Normal PDFs with embedded text
  - Password-protected PDFs (skips gracefully)
  - Corrupted/truncated PDFs (skips gracefully)
"""

import logging
from pathlib import Path

from extractors.base_extractor import BaseExtractor, ExtractorError

log = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):
    """
    Extracts text from PDF files using pypdf.

    pypdf extracts embedded text only — no OCR.
    If a PDF has no embedded text (e.g. scanned image),
    an empty string is returned (not an error).
    """

    def _extract_raw(self, path: Path) -> str:
        try:
            import pypdf  # type: ignore
        except ImportError:
            raise ExtractorError(
                "pypdf is not installed. Run: pip install pypdf"
            )

        try:
            reader = pypdf.PdfReader(str(path))

            # Check for password-protected PDF
            if reader.is_encrypted:
                # Try empty password first (some files decrypt automatically)
                try:
                    reader.decrypt("")
                except Exception:
                    raise ExtractorError("PDF is password-protected")

            pages = reader.pages
            texts: list[str] = []

            for i, page in enumerate(pages):
                try:
                    page_text = page.extract_text() or ""
                    texts.append(page_text)
                except Exception as exc:
                    log.debug("PDF page %d extraction error [%s]: %s", i, path.name, exc)
                    continue

            return "\n".join(texts)

        except ExtractorError:
            raise
        except Exception as exc:
            raise ExtractorError(f"PDF read error: {exc}") from exc
